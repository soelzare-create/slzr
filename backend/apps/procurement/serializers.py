from __future__ import annotations

from rest_framework import serializers

from .models import Purchase, PurchaseLine


class PurchaseLineSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="item.name", read_only=True)
    item_kind = serializers.CharField(source="item.kind", read_only=True)
    item_kind_display = serializers.CharField(source="item.get_kind_display", read_only=True)
    line_total = serializers.DecimalField(max_digits=18, decimal_places=0, read_only=True)

    class Meta:
        model = PurchaseLine
        fields = ["id", "item", "item_name", "item_kind", "item_kind_display",
                  "description", "quantity", "unit_price", "line_total"]


class PurchaseSerializer(serializers.ModelSerializer):
    lines = PurchaseLineSerializer(many=True)
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    owner_name = serializers.CharField(source="owner.full_name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    total = serializers.DecimalField(max_digits=18, decimal_places=0, read_only=True)
    goods_total = serializers.DecimalField(max_digits=18, decimal_places=0, read_only=True)
    service_total = serializers.DecimalField(max_digits=18, decimal_places=0, read_only=True)
    received = serializers.SerializerMethodField()

    class Meta:
        model = Purchase
        fields = ["id", "number", "supplier", "supplier_name", "owner", "owner_name",
                  "status", "status_display", "date", "notes", "origin_ref",
                  "total", "goods_total", "service_total", "received", "lines", "created_at"]
        read_only_fields = ["number", "status"]
        extra_kwargs = {"owner": {"required": False}}

    def create(self, validated):
        lines = validated.pop("lines", [])
        purchase = Purchase.objects.create(**validated)
        for line in lines:
            PurchaseLine.objects.create(purchase=purchase, **line)
        return purchase

    def get_received(self, obj) -> bool:
        # True once the warehouse has recorded a goods-receipt for this purchase.
        return obj.goods_receipts.exists()

    def update(self, instance, validated):
        # A registered purchase has posted its financial effect and may have
        # sale lines attached to its lines — editing it would corrupt both.
        # Only a draft purchase is editable; change a registered one via ابطال.
        if instance.status != Purchase.Status.DRAFT:
            raise serializers.ValidationError(
                "فقط خرید در وضعیت «پیش‌نویس» قابل ویرایش است؛ برای تغییر، ابتدا آن را ابطال کنید."
            )
        lines = validated.pop("lines", None)
        for k, v in validated.items():
            setattr(instance, k, v)
        instance.save()
        if lines is not None:
            instance.lines.all().delete()
            for line in lines:
                PurchaseLine.objects.create(purchase=instance, **line)
        return instance
