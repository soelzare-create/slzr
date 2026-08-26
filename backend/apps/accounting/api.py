"""Accounting API: chart of accounts, journal (read), and reports.

Reports (Section 9): general ledger, balance sheet, and per-party balances.
Access is read for accounting/management (Section 3, decision #9).
"""
from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from rest_framework import viewsets, views
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.accounts.permissions import HasPermissionCode

from . import services
from .models import Account, Expense, JournalEntry, JournalLine, Payment
from .serializers import (
    AccountSerializer, ExpenseSerializer, JournalEntrySerializer, PaymentSerializer,
)


class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [HasPermissionCode]
    required_permissions = {"read": "accounting.view", "write": "accounting.edit"}

    @action(detail=False, methods=["get"])
    def cash(self, request):
        """Cash & bank accounts selectable for expenses/payments (code 11xx)."""
        qs = self.get_queryset().filter(type=Account.Type.ASSET, code__startswith="11",
                                        is_active=True).exclude(code="1100")
        return Response(AccountSerializer(qs, many=True).data)


class ExpenseViewSet(viewsets.ModelViewSet):
    """Expenses (هزینه) — direct / overhead. Posts a journal entry on create."""

    queryset = Expense.objects.select_related("paid_from", "party", "owner")
    serializer_class = ExpenseSerializer
    permission_classes = [HasPermissionCode]
    required_permissions = {"read": "accounting.view", "write": "accounting.edit"}

    def perform_create(self, serializer):
        with transaction.atomic():
            expense = serializer.save(owner=self.request.user)
            services.register_expense(expense, actor=self.request.user)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        expense = self.get_object()
        with transaction.atomic():
            services.reverse_document(f"accounting.expense:{expense.id}",
                                      actor=request.user,
                                      description=f"ابطال هزینه {expense.number}")
            expense.status = Expense.Status.CANCELLED
            expense.save(update_fields=["status", "updated_at"])
        return Response(ExpenseSerializer(expense).data)


class PaymentViewSet(viewsets.ModelViewSet):
    """Receipts (دریافت) and payments (پرداخت) against party balances."""

    queryset = Payment.objects.select_related("account", "party", "owner")
    serializer_class = PaymentSerializer
    permission_classes = [HasPermissionCode]
    required_permissions = {"read": "accounting.view", "write": "accounting.edit"}

    def get_queryset(self):
        qs = super().get_queryset()
        party = self.request.query_params.get("party")
        if party:
            qs = qs.filter(party_id=party)
        return qs

    def perform_create(self, serializer):
        with transaction.atomic():
            payment = serializer.save(owner=self.request.user)
            services.register_payment(payment, actor=self.request.user)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        payment = self.get_object()
        with transaction.atomic():
            services.reverse_document(f"accounting.payment:{payment.id}",
                                      actor=request.user,
                                      description=f"ابطال {payment.number}")
            payment.status = Payment.Status.CANCELLED
            payment.save(update_fields=["status", "updated_at"])
        return Response(PaymentSerializer(payment).data)


class JournalEntryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = JournalEntry.objects.prefetch_related("lines__account", "lines__party")
    serializer_class = JournalEntrySerializer
    permission_classes = [HasPermissionCode]
    required_permission = "accounting.view"


class LedgerView(views.APIView):
    """General ledger: balance per account (sum of debit − credit)."""

    permission_classes = [HasPermissionCode]
    required_permission = "accounting.view"

    def get(self, request):
        rows = []
        agg = (JournalLine.objects.values("account__code", "account__name", "account__type")
               .annotate(debit=Sum("debit"), credit=Sum("credit"))
               .order_by("account__code"))
        for r in agg:
            debit = r["debit"] or Decimal("0")
            credit = r["credit"] or Decimal("0")
            rows.append({
                "code": r["account__code"],
                "name": r["account__name"],
                "type": r["account__type"],
                "debit": debit,
                "credit": credit,
                "balance": debit - credit,
            })
        return Response(rows)


class BalanceSheetView(views.APIView):
    """Balance sheet totals grouped by account type (Section 9)."""

    permission_classes = [HasPermissionCode]
    required_permission = "accounting.view"

    def get(self, request):
        totals = {t: Decimal("0") for t in
                  ["ASSET", "LIABILITY", "EQUITY", "INCOME", "EXPENSE"]}
        agg = (JournalLine.objects.values("account__type")
               .annotate(debit=Sum("debit"), credit=Sum("credit")))
        for r in agg:
            debit = r["debit"] or Decimal("0")
            credit = r["credit"] or Decimal("0")
            t = r["account__type"]
            # Assets/expenses carry a debit balance; the rest carry credit.
            totals[t] = (debit - credit) if t in {"ASSET", "EXPENSE"} else (credit - debit)
        net_income = totals["INCOME"] - totals["EXPENSE"]
        return Response({
            "assets": totals["ASSET"],
            "liabilities": totals["LIABILITY"],
            "equity": totals["EQUITY"],
            "income": totals["INCOME"],
            "expense": totals["EXPENSE"],
            "net_income": net_income,
        })


class PartyBalancesView(views.APIView):
    """Balance per party: what each customer owes / we owe each supplier."""

    permission_classes = [HasPermissionCode]
    required_permission = "accounting.view"

    def get(self, request):
        agg = (JournalLine.objects.filter(party__isnull=False)
               .values("party__id", "party__name")
               .annotate(debit=Sum("debit"), credit=Sum("credit"))
               .order_by("party__name"))
        rows = [{
            "party_id": r["party__id"],
            "party_name": r["party__name"],
            "balance": (r["debit"] or Decimal("0")) - (r["credit"] or Decimal("0")),
        } for r in agg]
        return Response(rows)
