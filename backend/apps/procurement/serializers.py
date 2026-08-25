from __future__ import annotations

from rest_framework import serializers

from .models import Purchase, PurchaseLine


class PurchaseLineSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="item.name", read_only=True)
    line_total = serializers.DecimalField(max_digits=18, decimal_places=0, read_only=True)

    class Meta:
        model = PurchaseLine
        fields = ["id", "item", "item_name", "description", "quantity",
                  "unit_price", "line_total"]


class PurchaseSerializer(serializers.ModelSerializer):
    lines = PurchaseLineSerializer(many=True)
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    owner_name = serializers.CharField(source="owner.full_name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    total = serializers.DecimalField(max_digits=18, decimal_places=0, read_only=True)

    class Meta:
        model = Purchase
        fields = ["id", "number", "supplier", "supplier_name", "owner", "owner_name",
                  "status", "status_display", "date", "notes", "origin_ref",
                  "total", "lines", "created_at"]
        read_only_fields = ["number", "status"]

    def create(self, validated):
        lines = validated.pop("lines", [])
        purchase = Purchase.objects.create(**validated)
        for line in lines:
            PurchaseLine.objects.create(purchase=purchase, **line)
        return purchase

    def update(self, instance, validated):
        lines = validated.pop("lines", None)
        for k, v in validated.items():
            setattr(instance, k, v)
        instance.save()
        if lines is not None:
            instance.lines.all().delete()
            for line in lines:
                PurchaseLine.objects.create(purchase=instance, **line)
        return instance
