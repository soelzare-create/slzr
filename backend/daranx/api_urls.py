"""API URL routing — all department routers under /api/."""
from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounting.api import (
    AccountViewSet, BalanceSheetView, ExpenseViewSet, JournalEntryViewSet, LedgerView,
    PartyBalancesView, PaymentViewSet,
)
from apps.accounts.api import (
    RoleViewSet, SystemViewSet, UserViewSet, login_view, me_view,
)
from apps.core.api import ItemViewSet, NotificationViewSet, PartyViewSet
from apps.management.api import DashboardView
from apps.procurement.api import PurchaseViewSet
from apps.sales.api import InvoiceViewSet, ProformaViewSet
from apps.technical.api import DirectInvoiceView
from apps.warehouse.api import GoodsReceiptViewSet

router = DefaultRouter(trailing_slash=False)
router.register("users", UserViewSet, basename="user")
router.register("roles", RoleViewSet, basename="role")
router.register("systems", SystemViewSet, basename="system")
router.register("parties", PartyViewSet, basename="party")
router.register("items", ItemViewSet, basename="item")
router.register("notifications", NotificationViewSet, basename="notification")
router.register("purchases", PurchaseViewSet, basename="purchase")
router.register("proformas", ProformaViewSet, basename="proforma")
router.register("invoices", InvoiceViewSet, basename="invoice")
router.register("accounts", AccountViewSet, basename="account")
router.register("journal", JournalEntryViewSet, basename="journal")
router.register("expenses", ExpenseViewSet, basename="expense")
router.register("payments", PaymentViewSet, basename="payment")
router.register("receipts", GoodsReceiptViewSet, basename="receipt")

urlpatterns = [
    # Auth
    path("auth/login", login_view),
    path("auth/refresh", TokenRefreshView.as_view()),
    path("auth/me", me_view),
    # Technical direct (service/support) invoices
    path("technical/invoices", DirectInvoiceView.as_view()),
    # Reports
    path("reports/ledger", LedgerView.as_view()),
    path("reports/balance-sheet", BalanceSheetView.as_view()),
    path("reports/party-balances", PartyBalancesView.as_view()),
    path("dashboard", DashboardView.as_view()),
    # Routers
    path("", include(router.urls)),
]
