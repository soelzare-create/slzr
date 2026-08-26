"""Dashboards — role-aware (Section 3).

Each department sees its own view: sales sees their sales & receivables;
accounting / management see the cross-department financial picture.
"""
from __future__ import annotations

from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from rest_framework import views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounting.models import JournalLine
from apps.accounting.services import (
    ACCOUNTS_RECEIVABLE, ACCOUNTS_PAYABLE, SALES_INCOME, SERVICE_INCOME, SUPPORT_INCOME,
)
from apps.procurement.models import Purchase
from apps.sales.models import Invoice, Proforma, ProformaStatus

_LINE_TOTAL = ExpressionWrapper(
    F("lines__quantity") * F("lines__unit_price"),
    output_field=DecimalField(max_digits=20, decimal_places=2),
)


def _account_balance(code: str) -> Decimal:
    agg = JournalLine.objects.filter(account__code=code).aggregate(
        d=Sum("debit"), c=Sum("credit"))
    return (agg["d"] or Decimal("0")) - (agg["c"] or Decimal("0"))


def _resolve_role(user) -> str:
    if user.is_system_admin or user.has_perm_code("management.view_all"):
        return "management"
    if user.has_perm_code("accounting.view"):
        return "accounting"
    if user.has_perm_code("procurement.view"):
        return "procurement"
    if user.has_perm_code("technical.view"):
        return "technical"
    if user.has_perm_code("sales.view"):
        return "sales"
    return "generic"


class DashboardView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        role = _resolve_role(request.user)
        if role == "sales":
            return Response({"role": role, **self._sales(request.user)})
        if role == "procurement":
            return Response({"role": role, **self._procurement(request.user)})
        if role == "technical":
            return Response({"role": role, **self._technical(request.user)})
        return Response({"role": role, **self._financial()})

    # -- sales view ---------------------------------------------------------
    def _sales(self, user) -> dict:
        my_issued = Invoice.objects.filter(owner=user, status=Invoice.Status.ISSUED)
        my_sales = my_issued.aggregate(t=Sum(_LINE_TOTAL))["t"] or Decimal("0")

        my_proformas = Proforma.objects.filter(owner=user)
        total = my_proformas.count()
        invoiced = my_proformas.filter(status=ProformaStatus.INVOICED).count()
        open_count = my_proformas.exclude(
            status__in=[ProformaStatus.INVOICED, ProformaStatus.CANCELLED]
        ).count()

        # Uncollected among this seller's customers (positive journal balance).
        customer_ids = list(my_issued.values_list("customer_id", flat=True).distinct())
        uncollected = Decimal("0")
        top_debtors = []
        if customer_ids:
            rows = (JournalLine.objects.filter(party_id__in=customer_ids)
                    .values("party_id", "party__name")
                    .annotate(d=Sum("debit"), c=Sum("credit")))
            for r in rows:
                bal = (r["d"] or Decimal("0")) - (r["c"] or Decimal("0"))
                if bal > 0:
                    uncollected += bal
                    top_debtors.append({"party_id": r["party_id"],
                                        "party_name": r["party__name"], "balance": bal})
            top_debtors.sort(key=lambda x: x["balance"], reverse=True)
        return {
            "my_sales": my_sales,
            "uncollected": uncollected,
            "open_proformas": open_count,
            "conversion_rate": round(invoiced / total * 100) if total else 0,
            "top_debtors": top_debtors[:5],
        }

    # -- procurement (بازرگانی) view ---------------------------------------
    def _procurement(self, user) -> dict:
        my = Purchase.objects.filter(owner=user)
        my_registered = my.filter(status=Purchase.Status.REGISTERED)
        my_total = my_registered.aggregate(t=Sum(_LINE_TOTAL))["t"] or Decimal("0")
        pending = my.filter(status=Purchase.Status.DRAFT).count()

        # Proformas department-wide awaiting a purchase to be registered.
        open_requests = Proforma.objects.filter(
            status=ProformaStatus.AWAITING_PURCHASE).count()

        top_suppliers = [
            {"party_id": r["supplier_id"], "party_name": r["supplier__name"],
             "amount": r["total"] or Decimal("0")}
            for r in (Purchase.objects.filter(status=Purchase.Status.REGISTERED)
                      .values("supplier_id", "supplier__name")
                      .annotate(total=Sum(_LINE_TOTAL)).order_by("-total")[:5])
        ]
        return {
            "my_purchases": my_total,
            "pending_purchases": pending,
            "open_requests": open_requests,
            "payable": -_account_balance(ACCOUNTS_PAYABLE),
            "top_suppliers": top_suppliers,
        }

    # -- technical / support (فنی) view ------------------------------------
    def _technical(self, user) -> dict:
        from datetime import date, timedelta

        my = Invoice.objects.filter(owner=user, status=Invoice.Status.ISSUED)
        my_income = my.exclude(type=Invoice.Type.GOODS).aggregate(t=Sum(_LINE_TOTAL))["t"] or Decimal("0")
        service_count = my.filter(type=Invoice.Type.SERVICE).count()
        support_count = my.filter(type=Invoice.Type.SUPPORT).count()

        soon = date.today() + timedelta(days=30)
        support_due = [
            {"invoice": inv.number, "party_name": inv.customer.name,
             "period_end": inv.period_end}
            for inv in Invoice.objects.filter(
                owner=user, type=Invoice.Type.SUPPORT, status=Invoice.Status.ISSUED,
                period_end__isnull=False, period_end__lte=soon
            ).select_related("customer").order_by("period_end")[:5]
        ]
        return {
            "my_income": my_income,
            "service_count": service_count,
            "support_count": support_count,
            "support_due": support_due,
        }

    # -- accounting / management view --------------------------------------
    def _financial(self) -> dict:
        income = Decimal("0")
        for code in (SALES_INCOME, SERVICE_INCOME, SUPPORT_INCOME):
            income += -_account_balance(code)
        proforma_counts = {
            s.value: Proforma.objects.filter(status=s.value).count()
            for s in ProformaStatus
        }
        return {
            "receivable": _account_balance(ACCOUNTS_RECEIVABLE),
            "payable": -_account_balance(ACCOUNTS_PAYABLE),
            "income": income,
            "counts": {
                "proformas": Proforma.objects.count(),
                "invoices": Invoice.objects.count(),
                "purchases": Purchase.objects.count(),
                "open_proformas": Proforma.objects.exclude(
                    status__in=[ProformaStatus.INVOICED, ProformaStatus.CANCELLED]
                ).count(),
            },
            "proforma_by_status": proforma_counts,
        }
