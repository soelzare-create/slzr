"""Technical / support department API: service & monthly-support invoices.

Reuses the sales Invoice model (single invoice ledger, single place the sale
journal entry is posted) via the sales service layer. Section 4.2 / 4.3.
"""
from __future__ import annotations

from rest_framework import serializers, views
from rest_framework.response import Response

from apps.accounts.permissions import HasPermissionCode
from apps.sales.models import Invoice
from apps.sales.serializers import InvoiceSerializer
from apps.sales import services as sales_services


class _LineIn(serializers.Serializer):
    item = serializers.IntegerField()
    description = serializers.CharField(required=False, allow_blank=True)
    quantity = serializers.DecimalField(max_digits=14, decimal_places=2, default=1)
    unit_price = serializers.DecimalField(max_digits=18, decimal_places=0, default=0)


class _DirectInvoiceIn(serializers.Serializer):
    type = serializers.ChoiceField(
        choices=[Invoice.Type.GOODS, Invoice.Type.SERVICE, Invoice.Type.SUPPORT])
    customer = serializers.IntegerField()
    period_start = serializers.DateField(required=False, allow_null=True)
    period_end = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    lines = _LineIn(many=True)


class DirectInvoiceView(views.APIView):
    """POST a service or monthly-support invoice (no proforma, no 5% rule)."""

    permission_classes = [HasPermissionCode]
    required_permission = "technical.edit"

    def post(self, request):
        data = _DirectInvoiceIn(data=request.data)
        data.is_valid(raise_exception=True)
        v = data.validated_data
        from apps.core.models import Party

        invoice = sales_services.create_direct_invoice(
            invoice_type=v["type"],
            customer=Party.objects.get(pk=v["customer"]),
            owner=request.user,
            lines_data=[dict(l) for l in v["lines"]],
            actor=request.user,
            period_start=v.get("period_start"),
            period_end=v.get("period_end"),
            notes=v.get("notes", ""),
        )
        return Response(InvoiceSerializer(invoice).data, status=201)
