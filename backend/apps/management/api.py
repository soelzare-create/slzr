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
    if user.has_perm_code("sales.view"):
        return "sales"
    return "generic"


class DashboardView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        role = _resolve_role(request.user)
        if role == "sales":
            return Response({"role": role, **self._sales(request.user)})
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
