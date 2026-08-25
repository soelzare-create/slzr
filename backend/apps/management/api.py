"""Management dashboard: a unified cross-department view (Section 3, decision #7).

Read access for management / system admin. Aggregates lightweight KPIs.
"""
from __future__ import annotations

from decimal import Decimal

from django.db.models import Sum
from rest_framework import views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounting.models import JournalLine
from apps.accounting.services import (
    ACCOUNTS_RECEIVABLE, ACCOUNTS_PAYABLE, SALES_INCOME, SERVICE_INCOME, SUPPORT_INCOME,
)
from apps.procurement.models import Purchase
from apps.sales.models import Invoice, Proforma, ProformaStatus


def _account_balance(code: str) -> Decimal:
    agg = JournalLine.objects.filter(account__code=code).aggregate(
        d=Sum("debit"), c=Sum("credit"))
    return (agg["d"] or Decimal("0")) - (agg["c"] or Decimal("0"))


class DashboardView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        income = Decimal("0")
        for code in (SALES_INCOME, SERVICE_INCOME, SUPPORT_INCOME):
            income += -_account_balance(code)  # income carries a credit balance

        proforma_counts = {
            s.value: Proforma.objects.filter(status=s.value).count()
            for s in ProformaStatus
        }
        return Response({
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
        })
