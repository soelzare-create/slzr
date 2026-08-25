from __future__ import annotations

from rest_framework import serializers

from .models import Invoice, InvoiceLine, Proforma, ProformaLine


class ProformaLineSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="item.name", read_only=True)
    line_total = serializers.DecimalField(max_digits=18, decimal_places=0, read_only=True)
    margin = serializers.DecimalField(max_digits=18, decimal_places=0, read_only=True)

    class Meta:
        model = ProformaLine
        fields = ["id", "item", "item_name", "description", "quantity",
                  "unit_price", "source_purchase_line", "line_total", "margin"]


class ProformaSerializer(serializers.ModelSerializer):
    lines = ProformaLineSerializer(many=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    owner_name = serializers.CharField(source="owner.full_name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    total = serializers.DecimalField(max_digits=18, decimal_places=0, read_only=True)

    class Meta:
        model = Proforma
        fields = ["id", "number", "customer", "customer_name", "owner", "owner_name",
                  "status", "status_display", "confirmed_at", "reservation_expires_at",
                  "notes", "total", "lines", "created_at"]
        read_only_fields = ["number", "status", "confirmed_at", "reservation_expires_at"]

    def create(self, validated):
        lines = validated.pop("lines", [])
        proforma = Proforma.objects.create(**validated)
        for line in lines:
            ProformaLine.objects.create(proforma=proforma, **line)
        return proforma

    def update(self, instance, validated):
        lines = validated.pop("lines", None)
        for k, v in validated.items():
            setattr(instance, k, v)
        instance.save()
        if lines is not None:
            instance.lines.all().delete()
            for line in lines:
                ProformaLine.objects.create(proforma=instance, **line)
        return instance


class InvoiceLineSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="item.name", read_only=True)
    line_total = serializers.DecimalField(max_digits=18, decimal_places=0, read_only=True)

    class Meta:
        model = InvoiceLine
        fields = ["id", "item", "item_name", "description", "quantity",
                  "unit_price", "source_purchase_line", "line_total"]


class InvoiceSerializer(serializers.ModelSerializer):
    lines = InvoiceLineSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    owner_name = serializers.CharField(source="owner.full_name", read_only=True)
    type_display = serializers.CharField(source="get_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    total = serializers.DecimalField(max_digits=18, decimal_places=0, read_only=True)

    class Meta:
        model = Invoice
        fields = ["id", "number", "type", "type_display", "status", "status_display",
                  "customer", "customer_name", "owner", "owner_name", "proforma",
                  "date", "period_start", "period_end", "notes", "total", "lines",
                  "created_at"]
