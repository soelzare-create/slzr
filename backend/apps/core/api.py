from __future__ import annotations

from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Item, Notification, Party
from .serializers import ItemSerializer, NotificationSerializer, PartySerializer


class PartyViewSet(viewsets.ModelViewSet):
    queryset = Party.objects.all()
    serializer_class = PartySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        role = self.request.query_params.get("role")
        if role == "customer":
            qs = qs.filter(is_customer=True)
        elif role == "supplier":
            qs = qs.filter(is_supplier=True)
        search = self.request.query_params.get("q")
        if search:
            qs = qs.filter(name__icontains=search)
        return qs

    @action(detail=False, methods=["get"])
    def cards(self, request):
        """Card view of parties: basic info + total sales + balance + settle status.

        Computed with two grouped aggregate queries (not per-row), then merged.
        balance > 0 means the party owes us (receivable); < 0 means we owe them.
        """
        from apps.accounting.models import JournalLine
        from apps.sales.models import Invoice

        parties = list(self.get_queryset())

        # Balance per party from the journal (receivable/payable movement).
        balances = {
            r["party_id"]: (r["debit"] or Decimal("0")) - (r["credit"] or Decimal("0"))
            for r in JournalLine.objects.filter(party__isnull=False)
            .values("party_id").annotate(debit=Sum("debit"), credit=Sum("credit"))
        }

        # Total issued sales per customer (sum of line quantity × unit price).
        line_total = ExpressionWrapper(
            F("lines__quantity") * F("lines__unit_price"),
            output_field=DecimalField(max_digits=20, decimal_places=2),
        )
        sales = {
            r["customer_id"]: r["total"] or Decimal("0")
            for r in Invoice.objects.filter(status=Invoice.Status.ISSUED)
            .values("customer_id").annotate(total=Sum(line_total))
        }

        out = []
        for p in parties:
            balance = balances.get(p.id, Decimal("0"))
            settle = "debtor" if balance > 0 else ("creditor" if balance < 0 else "settled")
            out.append({
                "id": p.id,
                "name": p.name,
                "is_customer": p.is_customer,
                "is_supplier": p.is_supplier,
                "phone": p.phone,
                "address": p.address,
                "sales_total": sales.get(p.id, Decimal("0")),
                "balance": balance,
                "settle_status": settle,
            })
        return Response(out)


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        kind = self.request.query_params.get("kind")
        if kind:
            qs = qs.filter(kind=kind)
        return qs


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """The notifications dashboard — each user sees only their own."""

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return Response({"count": count})

    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        n = self.get_object()
        n.is_read = True
        n.save(update_fields=["is_read", "updated_at"])
        return Response({"ok": True})

    @action(detail=False, methods=["post"])
    def read_all(self, request):
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({"ok": True})
