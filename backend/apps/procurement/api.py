from __future__ import annotations

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.accounts.permissions import HasPermissionCode, OwnershipQuerysetMixin

from . import services
from .models import Purchase
from .serializers import PurchaseSerializer


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
        # If no explicit owner (assignee), default to the creator.
        owner = serializer.validated_data.get("owner") or self.request.user
        serializer.save(owner=owner)

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
