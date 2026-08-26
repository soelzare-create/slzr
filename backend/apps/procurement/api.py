from __future__ import annotations

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.accounts.models import User
from apps.accounts.permissions import HasPermissionCode, OwnershipQuerysetMixin
from apps.core.models import Notification
from apps.core.services import log_action, notify

from . import services
from .models import Purchase
from .serializers import PurchaseSerializer


def _procurement_users():
    """Users with a role in the procurement department (assignable)."""
    return User.objects.filter(
        userrole__role__system__code="procurement", is_active=True
    ).distinct()


class PurchaseViewSet(OwnershipQuerysetMixin, viewsets.ModelViewSet):
    """Procurement purchases. Employees see only purchases assigned to them."""

    queryset = Purchase.objects.select_related("supplier", "owner").prefetch_related("lines")
    serializer_class = PurchaseSerializer
    permission_classes = [HasPermissionCode]
    required_permissions = {"read": "procurement.view", "write": "procurement.edit"}
    view_all_permission = "procurement.view_all"
    owner_field = "owner"

    def get_queryset(self):
        return self.filter_by_ownership(super().get_queryset())

    def perform_create(self, serializer):
        # Only a manager (procurement.assign) may assign to someone else on
        # create; everyone else owns what they create.
        requested = serializer.validated_data.get("owner")
        if requested and self.request.user.has_perm_code("procurement.assign"):
            owner = requested
        else:
            owner = self.request.user
        purchase = serializer.save(owner=owner)
        if owner != self.request.user:
            self._notify_assignee(purchase, owner, self.request.user)

    @action(detail=False, methods=["get"])
    def team(self, request):
        """Procurement users available for assignment (managers only)."""
        if not request.user.has_perm_code("procurement.assign"):
            return Response([])
        return Response(list(_procurement_users().values("id", "full_name")))

    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        """Re-assign a purchase to a procurement user (Section 5)."""
        if not request.user.has_perm_code("procurement.assign"):
            raise PermissionDenied("اساین خرید فقط توسط مدیر بازرگانی ممکن است.")
        purchase = self.get_object()
        owner = _procurement_users().filter(pk=request.data.get("owner")).first()
        if not owner:
            raise ValidationError("کاربر بازرگانی معتبر انتخاب کنید.")
        purchase.owner = owner
        purchase.save(update_fields=["owner", "updated_at"])
        log_action(request.user, "procurement.assign_purchase",
                   f"procurement.purchase:{purchase.id}", owner=owner.id)
        self._notify_assignee(purchase, owner, request.user)
        return Response(PurchaseSerializer(purchase).data)

    def _notify_assignee(self, purchase, owner, actor):
        if owner == actor:
            return
        notify(owner, Notification.Kind.GENERAL,
               f"خرید {purchase.number or purchase.id} به شما اساین شد.",
               f"procurement.purchase:{purchase.id}")

    @action(detail=True, methods=["post"])
    def register(self, request, pk=None):
        """Register the purchase: post its financial effect + notify sales."""
        purchase = self.get_object()
        try:
            purchase = services.register_purchase(purchase, actor=request.user)
        except ValueError as exc:
            raise ValidationError(str(exc))
        # Best-effort: advance a linked proforma to READY (off the critical path).
        self._notify_origin(purchase)
        return Response(PurchaseSerializer(purchase).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        purchase = self.get_object()
        purchase = services.cancel_purchase(purchase, actor=request.user)
        return Response(PurchaseSerializer(purchase).data)

    def _notify_origin(self, purchase):
        """If the purchase came from a proforma awaiting stock, advance it to READY.

        Kept off the critical path — a failure here never rolls back the
        registered purchase (Section 2).
        """
        if not purchase.origin_ref.startswith("sales.proforma:"):
            return
        try:
            from apps.sales.models import Proforma, ProformaStatus
            from apps.sales import services as sales_services

            pid = int(purchase.origin_ref.split(":", 1)[1])
            proforma = Proforma.objects.filter(pk=pid).first()
            if proforma and proforma.status == ProformaStatus.AWAITING_PURCHASE:
                sales_services.mark_ready(proforma, actor=self.request.user)
        except Exception:
            pass
