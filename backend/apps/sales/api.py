from __future__ import annotations

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.accounts.models import Role, UserRole
from apps.accounts.permissions import HasPermissionCode, OwnershipQuerysetMixin

from . import services
from .models import Invoice, Proforma
from .serializers import InvoiceSerializer, ProformaSerializer


def _procurement_manager():
    """Find a procurement manager to route purchase requests to (best-effort)."""
    role = Role.objects.filter(code="procurement_manager").first()
    if not role:
        return None
    ur = UserRole.objects.filter(role=role).select_related("user").first()
    return ur.user if ur else None


class ProformaViewSet(OwnershipQuerysetMixin, viewsets.ModelViewSet):
    """Proformas. Employees see only their own; managers see the whole department."""

    queryset = Proforma.objects.select_related("customer", "owner").prefetch_related("lines")
    serializer_class = ProformaSerializer
    permission_classes = [HasPermissionCode]
    required_permissions = {"read": "sales.view", "write": "sales.edit"}
    view_all_permission = "sales.view_all"
    owner_field = "owner"

    def get_queryset(self):
        return self.filter_by_ownership(super().get_queryset())

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    # -- state machine actions ---------------------------------------------
    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        return self._run(services.confirm_proforma, self.get_object())

    @action(detail=True, methods=["post"])
    def request_purchase(self, request, pk=None):
        p = self.get_object()
        return self._run(services.request_purchase, p,
                         procurement_manager=_procurement_manager())

    @action(detail=True, methods=["post"])
    def unfulfillable(self, request, pk=None):
        return self._run(services.mark_unfulfillable, self.get_object())

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        p = self.get_object()
        manager_approved = bool(request.data.get("manager_approved")) or \
            request.user.has_perm_code("sales.view_all")
        return self._run(services.cancel_proforma, p, manager_approved=manager_approved)

    @action(detail=True, methods=["post"])
    def convert(self, request, pk=None):
        """Convert to a goods invoice — enforces the 5% rule (Section 6)."""
        p = self.get_object()
        try:
            invoice = services.convert_to_invoice(p, actor=request.user)
        except (services.InvalidTransition, services.FivePercentViolation) as exc:
            raise ValidationError(str(exc))
        return Response(InvoiceSerializer(invoice).data)

    def _run(self, fn, proforma, **kwargs):
        try:
            proforma = fn(proforma, actor=self.request.user, **kwargs)
        except (services.InvalidTransition, services.FivePercentViolation) as exc:
            raise ValidationError(str(exc))
        return Response(ProformaSerializer(proforma).data)


class InvoiceViewSet(OwnershipQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    """Invoices — read + reverse. Accounting (cross-dept) reads all, read-only."""

    queryset = Invoice.objects.select_related("customer", "owner").prefetch_related("lines")
    serializer_class = InvoiceSerializer
    permission_classes = [HasPermissionCode]
    # Invoices are shared by sales (goods) and technical (service/support); either
    # department may read/manage them, scoped to their own records by ownership.
    required_permissions_any = {
        "read": ["sales.view", "technical.view"],
        "write": ["sales.edit", "technical.edit"],
    }
    view_all_permissions = ["sales.view_all", "technical.view_all"]
    owner_field = "owner"

    def get_queryset(self):
        qs = self.filter_by_ownership(super().get_queryset())
        user = self.request.user
        # A technical-only viewer (no sales access) sees only their department's
        # service/support invoices, never sales' goods invoices — even a manager.
        if (not user.is_system_admin and not user.has_perm_code("sales.view")
                and user.has_perm_code("technical.view")):
            qs = qs.filter(type__in=[Invoice.Type.SERVICE, Invoice.Type.SUPPORT])
        type_ = self.request.query_params.get("type")
        if type_:
            qs = qs.filter(type=type_)
        return qs

    @action(detail=True, methods=["post"])
    def reverse(self, request, pk=None):
        returned = bool(request.data.get("returned"))
        invoice = services.reverse_invoice(self.get_object(), actor=request.user,
                                           returned=returned)
        return Response(InvoiceSerializer(invoice).data)
