from __future__ import annotations

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import HasPermissionCode
from apps.procurement.models import Purchase

from .models import GoodsReceipt
from .serializers import (
    GoodsReceiptSerializer, ReceivablePurchaseSerializer,
)


class GoodsReceiptViewSet(viewsets.ModelViewSet):
    """Warehouse goods-receipts. Read/write gated by the warehouse permissions."""

    queryset = (GoodsReceipt.objects
                .select_related("purchase", "purchase__supplier", "received_by")
                .prefetch_related("items"))
    serializer_class = GoodsReceiptSerializer
    permission_classes = [HasPermissionCode]
    required_permissions = {"read": "warehouse.view", "write": "warehouse.edit"}

    def perform_create(self, serializer):
        serializer.save(received_by=self.request.user)

    @action(detail=False, methods=["get"])
    def receivable(self, request):
        """Registered purchases the warehouse may receive (goods hand-over)."""
        qs = (Purchase.objects.filter(status=Purchase.Status.REGISTERED)
              .select_related("supplier").prefetch_related("lines", "goods_receipts")
              .order_by("-created_at"))
        return Response(ReceivablePurchaseSerializer(qs, many=True).data)
