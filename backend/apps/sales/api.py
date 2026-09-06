from __future__ import annotations

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed, ValidationError
from rest_framework.response import Response

from apps.accounts.models import Role, UserRole
from apps.accounts.permissions import HasPermissionCode, OwnershipQuerysetMixin
from apps.core.models import Notification
from apps.core.services import notify

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

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        p = self.get_object()
        return self._run(services.cancel_proforma, p, manager_approved=True)

    @action(detail=True, methods=["post"])
    def convert(self, request, pk=None):
        """Convert directly to a goods invoice, then ask procurement to buy.

        No confirmation / 5% rule / purchase prerequisite (decoupled flow):
        issuing the invoice is what triggers the purchase request.
        """
        p = self.get_object()
        try:
            invoice = services.convert_to_invoice(p, actor=request.user)
        except services.InvalidTransition as exc:
            raise ValidationError(str(exc))
        # Ask procurement to buy the goods for this invoice (off the critical path).
        manager = _procurement_manager()
        if manager is not None:
            notify(
                recipient=manager,
                kind=Notification.Kind.PURCHASE_REQUEST,
                message=f"درخواست خرید برای فاکتور {invoice.number} (مشتری: {invoice.customer.name}).",
                source_ref=f"sales.invoice:{invoice.id}",
            )
        return Response(InvoiceSerializer(invoice).data)

    def _run(self, fn, proforma, **kwargs):
        try:
            proforma = fn(proforma, actor=self.request.user, **kwargs)
        except (services.InvalidTransition, services.FivePercentViolation) as exc:
            raise ValidationError(str(exc))
        return Response(ProformaSerializer(proforma).data)


class InvoiceViewSet(OwnershipQuerysetMixin, viewsets.ModelViewSet):
    """Invoices — read, edit metadata, and reverse.

    A finalized invoice's financial substance (lines, amounts, customer, type)
    is immutable: it has posted a journal entry. Only descriptive metadata
    (notes, date, support period) may be edited here — the serializer's
    ``read_only_fields`` enforce that. Direct creation and deletion are blocked;
    invoices are created via «تبدیل به فاکتور»/خدمات and removed via ابطال/مرجوعی.
    """

    queryset = Invoice.objects.select_related("customer", "owner").prefetch_related("lines")
    serializer_class = InvoiceSerializer
    permission_classes = [HasPermissionCode]
    required_permissions = {"read": "sales.view", "write": "sales.edit"}
    view_all_permission = "sales.view_all"
    owner_field = "owner"

    def get_queryset(self):
        qs = self.filter_by_ownership(super().get_queryset())
        type_ = self.request.query_params.get("type")
        if type_:
            qs = qs.filter(type=type_)
        return qs

    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed(
            "POST", detail="فاکتور مستقیم ساخته نمی‌شود؛ از «تبدیل پیش‌فاکتور» یا فاکتور خدمات استفاده کنید."
        )

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed(
            "DELETE", detail="فاکتور حذف نمی‌شود؛ برای لغو اثر مالی از «ابطال» یا «مرجوعی» استفاده کنید."
        )

    @action(detail=True, methods=["post"])
    def reverse(self, request, pk=None):
        returned = bool(request.data.get("returned"))
        invoice = services.reverse_invoice(self.get_object(), actor=request.user,
                                           returned=returned)
        return Response(InvoiceSerializer(invoice).data)

    @action(detail=True, methods=["post"])
    def reprice(self, request, pk=None):
        """Edit the amounts (quantity/unit price) of an issued invoice's lines."""
        lines = request.data.get("lines") or []
        try:
            invoice = services.reprice_invoice(
                self.get_object(), lines_data=lines, actor=request.user)
        except (services.InvalidTransition, services.FivePercentViolation) as exc:
            raise ValidationError(str(exc))
        return Response(InvoiceSerializer(invoice).data)
