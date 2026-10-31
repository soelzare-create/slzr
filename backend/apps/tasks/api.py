"""Tasks API: one text box in, everything else happens server-side."""
from __future__ import annotations

import hmac
import json
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import mixins, serializers, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.core.models import Party

from . import bale, parsing, services
from .models import BaleLink, Task, TaskEvent

log = logging.getLogger(__name__)


def _person(user):
    return {"id": user.pk, "full_name": user.full_name} if user else None


class TaskEventSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.full_name", default="", read_only=True)
    kind_display = serializers.CharField(source="get_kind_display", read_only=True)

    class Meta:
        model = TaskEvent
        fields = ["id", "kind", "kind_display", "text", "actor_name", "created_at"]


class TaskSerializer(serializers.ModelSerializer):
    kind_display = serializers.CharField(source="get_kind_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    customer_display = serializers.CharField(read_only=True)
    assignee_name = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)
    proforma_number = serializers.CharField(source="proforma.number", default=None,
                                            read_only=True)

    class Meta:
        model = Task
        fields = ["id", "number", "text", "kind", "kind_display", "status", "status_display",
                  "customer", "customer_name", "customer_display", "assignee", "assignee_name",
                  "created_by", "created_by_name", "proforma", "proforma_number",
                  "created_at", "last_activity_at", "done_at"]

    def get_assignee_name(self, obj):
        return obj.assignee.full_name if obj.assignee_id else "مدیریت"


class TaskDetailSerializer(TaskSerializer):
    events = TaskEventSerializer(many=True, read_only=True)

    class Meta(TaskSerializer.Meta):
        fields = TaskSerializer.Meta.fields + ["events"]


def _optional_user(value):
    if value in (None, "", 0, "0"):
        return None
    try:
        return get_user_model().objects.get(pk=int(value), is_active=True)
    except (ValueError, TypeError, get_user_model().DoesNotExist) as exc:
        raise ValidationError({"assignee": "کاربر پیدا نشد."}) from exc


def _optional_party(value):
    if value in (None, "", 0, "0"):
        return None
    try:
        return Party.objects.get(pk=int(value))
    except (ValueError, TypeError, Party.DoesNotExist) as exc:
        raise ValidationError({"customer": "مشتری پیدا نشد."}) from exc


class TaskViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
                  viewsets.GenericViewSet):
    """Any authenticated user. Employees see tasks they created or own;
    management (``tasks.view_all``) sees everything."""

    serializer_class = TaskSerializer

    def get_queryset(self):
        qs = services.visible_tasks(self.request.user)
        p = self.request.query_params
        me = self.request.user
        scope = p.get("scope")
        if scope == "mine":
            qs = qs.filter(assignee=me) if not services.is_management(me) else \
                qs.filter(Q(assignee=me) | Q(assignee__isnull=True))
        elif scope == "sent":
            qs = qs.filter(created_by=me).exclude(assignee=me)
        st = p.get("status")
        if st == "active":
            qs = qs.exclude(status=Task.Status.DONE)
        elif st in Task.Status.values:
            qs = qs.filter(status=st)
        if p.get("q"):
            qs = qs.filter(Q(text__icontains=p["q"]) | Q(number__icontains=p["q"])
                           | Q(customer__name__icontains=p["q"])
                           | Q(customer_name__icontains=p["q"]))
        return qs

    def get_serializer_class(self):
        return TaskDetailSerializer if self.action == "retrieve" else TaskSerializer

    def _run(self, fn, *args, **kwargs):
        try:
            result = fn(*args, **kwargs)
        except services.TaskError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        task = Task.objects.select_related("customer", "assignee", "created_by", "proforma") \
            .get(pk=result.pk)
        return Response(TaskDetailSerializer(task).data)

    def create(self, request, *args, **kwargs):
        d = request.data
        kwargs = {"text": d.get("text", ""), "actor": request.user}
        if "customer" in d:
            kwargs["customer"] = _optional_party(d.get("customer"))
        if "customer_name" in d:
            kwargs["customer_name"] = d.get("customer_name") or ""
        if d.get("kind") in Task.Kind.values:
            kwargs["kind"] = d["kind"]
        if "assignee" in d:
            kwargs["assignee"] = _optional_user(d.get("assignee"))
        try:
            task = services.create_task(**kwargs)
        except services.TaskError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(TaskDetailSerializer(task).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
    def parse(self, request):
        """Live preview of what the system understood from the text."""
        g = parsing.parse(request.data.get("text", ""))
        return Response({
            "kind": g.kind,
            "kind_display": Task.Kind(g.kind).label,
            "customer": {"id": g.customer.pk, "name": g.customer.name} if g.customer else None,
            "customer_name": g.customer_name,
            "mention_found": g.mention_found,
            "assignee": _person(g.assignee),
        })

    @action(detail=False, methods=["get"])
    def people(self, request):
        User = get_user_model()
        linked = set(BaleLink.objects.values_list("user_id", flat=True))
        mgmt = {u.pk for u in services.management_users()}
        return Response([
            {"id": u.pk, "full_name": u.full_name, "bale": u.pk in linked,
             "management": u.pk in mgmt}
            for u in User.objects.filter(is_active=True).order_by("full_name")
        ])

    @action(detail=False, methods=["get"])
    def summary(self, request):
        me = request.user
        mine = Task.objects.exclude(status=Task.Status.DONE)
        mine = mine.filter(Q(assignee=me) | Q(assignee__isnull=True)) \
            if services.is_management(me) else mine.filter(assignee=me)
        return Response({"mine_open": mine.count(),
                         "can_issue_proforma": services.can_issue_proforma(me),
                         "is_management": services.is_management(me)})

    @action(detail=True, methods=["post"])
    def status(self, request, pk=None):
        return self._run(services.set_status, self.get_object(), request.data.get("status"),
                         actor=request.user)

    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        return self._run(services.assign, self.get_object(),
                         _optional_user(request.data.get("assignee")), actor=request.user)

    @action(detail=True, methods=["post"])
    def note(self, request, pk=None):
        return self._run(services.add_note, self.get_object(), request.data.get("text", ""),
                         actor=request.user)

    @action(detail=True, methods=["post"])
    def kind(self, request, pk=None):
        return self._run(services.set_kind, self.get_object(), request.data.get("kind"),
                         actor=request.user)

    @action(detail=True, methods=["post"])
    def customer(self, request, pk=None):
        d = request.data
        return self._run(services.set_customer, self.get_object(), actor=request.user,
                         customer=_optional_party(d.get("customer")),
                         customer_name=d.get("customer_name") or "",
                         create=bool(d.get("create")))

    @action(detail=True, methods=["post"])
    def proforma(self, request, pk=None):
        task = self.get_object()
        try:
            pf = services.issue_proforma(task, actor=request.user)
        except services.TaskError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"proforma": pf.pk, "number": pf.number,
                         "task": TaskDetailSerializer(Task.objects.get(pk=task.pk)).data})


class BaleStatusView(views.APIView):
    """Is Bale configured, is the current user connected, and their link code."""

    def get(self, request):
        linked = BaleLink.objects.filter(user=request.user).exists()
        return Response({
            "enabled": bale.enabled(),
            "linked": linked,
            "bot_url": bale.bot_url(),
            "code": "" if linked or not bale.enabled() else bale.link_code_for(request.user),
        })


class BaleWebhookView(views.APIView):
    """Bale → us. Authenticated by the secret in the URL path, not JWT."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    def post(self, request, secret: str):
        expected = settings.BALE_WEBHOOK_SECRET
        if not (bale.enabled() and expected and hmac.compare_digest(secret, expected)):
            return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            update = request.data if isinstance(request.data, dict) else json.loads(request.body)
            bale.handle_update(update)
        except Exception:  # noqa: BLE001 — always 200 so Bale doesn't retry forever
            log.exception("bale update failed")
        return Response({"ok": True})
