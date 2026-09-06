from __future__ import annotations

from rest_framework import serializers

from .models import Invoice, InvoiceLine, Proforma, ProformaLine, ProformaStatus


class ProformaLineSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="item.name", read_only=True)
    item_kind = serializers.CharField(source="item.kind", read_only=True)
    item_kind_display = serializers.CharField(source="item.get_kind_display", read_only=True)
    line_total = serializers.DecimalField(max_digits=18, decimal_places=0, read_only=True)
    margin = serializers.DecimalField(max_digits=18, decimal_places=0, read_only=True)

    class Meta:
        model = ProformaLine
        fields = ["id", "item", "item_name", "item_kind", "item_kind_display",
                  "description", "quantity", "unit_price", "source_purchase_line",
                  "line_total", "margin"]


class ProformaSerializer(serializers.ModelSerializer):
    lines = ProformaLineSerializer(many=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    owner_name = serializers.CharField(source="owner.full_name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    total = serializers.DecimalField(max_digits=18, decimal_places=0, read_only=True)
    goods_total = serializers.DecimalField(max_digits=18, decimal_places=0, read_only=True)
    service_total = serializers.DecimalField(max_digits=18, decimal_places=0, read_only=True)

    class Meta:
        model = Proforma
        fields = ["id", "number", "customer", "customer_name", "owner", "owner_name",
                  "status", "status_display", "confirmed_at", "reservation_expires_at",
                  "notes", "total", "goods_total", "service_total", "lines", "created_at"]
        read_only_fields = ["number", "status", "confirmed_at", "reservation_expires_at",
                            "owner"]

    def create(self, validated):
        lines = validated.pop("lines", [])
        proforma = Proforma.objects.create(**validated)
        for line in lines:
            ProformaLine.objects.create(proforma=proforma, **line)
        return proforma

    def update(self, instance, validated):
        # A proforma is only freely editable while it is still a draft; once
        # confirmed it holds a soft reservation (and may be linked onward), so
        # changing it must go through ابطال first.
        if instance.status != ProformaStatus.DRAFT:
            raise serializers.ValidationError(
                "فقط پیش‌فاکتور در وضعیت «پیش‌نویس» قابل ویرایش است؛ برای تغییر، ابتدا آن را ابطال کنید."
            )
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
    item_kind = serializers.CharField(source="item.kind", read_only=True)
    item_kind_display = serializers.CharField(source="item.get_kind_display", read_only=True)
    line_total = serializers.DecimalField(max_digits=18, decimal_places=0, read_only=True)
    serials = serializers.SerializerMethodField()

    class Meta:
        model = InvoiceLine
        fields = ["id", "item", "item_name", "item_kind", "item_kind_display",
                  "description", "quantity", "unit_price", "source_purchase_line",
                  "line_total", "serials"]

    def get_serials(self, obj) -> list[str]:
        """Serials allocated to this line — recorded by the warehouse on the
        receipts of the purchases linked to this line's invoice, for this item."""
        from apps.warehouse.models import ReceiptItem
        out: list[str] = []
        for ri in ReceiptItem.objects.filter(
            receipt__purchase__sale_invoice_id=obj.invoice_id, item_id=obj.item_id
        ):
            out.extend(s for s in (ri.serials or []) if s)
        return out


class InvoiceSerializer(serializers.ModelSerializer):
    lines = InvoiceLineSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    owner_name = serializers.CharField(source="owner.full_name", read_only=True)
    type_display = serializers.CharField(source="get_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    total = serializers.DecimalField(max_digits=18, decimal_places=0, read_only=True)
    goods_total = serializers.DecimalField(max_digits=18, decimal_places=0, read_only=True)
    service_total = serializers.DecimalField(max_digits=18, decimal_places=0, read_only=True)

    class Meta:
        model = Invoice
        fields = ["id", "number", "type", "type_display", "status", "status_display",
                  "customer", "customer_name", "owner", "owner_name", "proforma",
                  "date", "period_start", "period_end", "notes", "total",
                  "goods_total", "service_total", "lines", "created_at"]
        # A finalized invoice's financial substance is immutable — its lines,
        # amounts, customer and type are fixed once issued (change them by
        # ابطال/مرجوعی + صدور مجدد). Only descriptive metadata stays editable.
        read_only_fields = ["number", "type", "status", "customer", "owner",
                            "proforma", "total", "created_at"]
