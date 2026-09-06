from __future__ import annotations

from rest_framework import serializers

from apps.procurement.models import Purchase, PurchaseLine

from .models import GoodsReceipt, ReceiptItem


class ReceiptItemSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="item.name", read_only=True)
    item_kind_display = serializers.CharField(source="item.get_kind_display", read_only=True)

    class Meta:
        model = ReceiptItem
        fields = ["id", "purchase_line", "item", "item_name", "item_kind_display",
                  "quantity", "serials"]
        read_only_fields = ["item"]  # derived from the purchase line on create


class GoodsReceiptSerializer(serializers.ModelSerializer):
    items = ReceiptItemSerializer(many=True)
    purchase_number = serializers.CharField(source="purchase.number", read_only=True)
    supplier_name = serializers.CharField(source="purchase.supplier.name", read_only=True)
    received_by_name = serializers.CharField(source="received_by.full_name", read_only=True)

    class Meta:
        model = GoodsReceipt
        fields = ["id", "number", "purchase", "purchase_number", "supplier_name",
                  "received_by", "received_by_name", "received_at", "notes",
                  "items", "created_at"]
        read_only_fields = ["number", "received_by"]

    def validate(self, attrs):
        purchase = attrs.get("purchase")
        if purchase and purchase.status != Purchase.Status.REGISTERED:
            raise serializers.ValidationError(
                "فقط برای خرید «ثبت‌شده» می‌توان رسید انبار صادر کرد."
            )
        return attrs

    def create(self, validated):
        items = validated.pop("items", [])
        receipt = GoodsReceipt.objects.create(**validated)
        for it in items:
            line = it["purchase_line"]
            ReceiptItem.objects.create(
                receipt=receipt,
                purchase_line=line,
                item=line.item,
                quantity=it.get("quantity") or 0,
                serials=[s for s in (it.get("serials") or []) if str(s).strip()],
            )
        return receipt


class ReceivableLineSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="item.name", read_only=True)
    item_kind = serializers.CharField(source="item.kind", read_only=True)
    item_kind_display = serializers.CharField(source="item.get_kind_display", read_only=True)

    class Meta:
        model = PurchaseLine
        fields = ["id", "item", "item_name", "item_kind", "item_kind_display", "quantity"]


class ReceivablePurchaseSerializer(serializers.ModelSerializer):
    """A registered purchase the warehouse can receive, with its lines."""

    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    lines = ReceivableLineSerializer(many=True, read_only=True)
    received = serializers.SerializerMethodField()

    class Meta:
        model = Purchase
        fields = ["id", "number", "supplier_name", "date", "lines", "received"]

    def get_received(self, obj) -> bool:
        return obj.goods_receipts.exists()
