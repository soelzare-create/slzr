"""Tests for invoice/purchase settlement via linked receipts/payments."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from apps.accounting.models import Account, Payment
from apps.accounting import services as acc
from apps.core.models import Item, Party
from apps.sales.models import Invoice
from apps.sales import services as sales

pytestmark = pytest.mark.django_db


def _bank():
    return Account.objects.get(code="1120")


def _service_invoice(user, amount):
    return sales.create_direct_invoice(
        invoice_type=Invoice.Type.SERVICE,
        customer=Party.objects.create(name="مشتری", is_customer=True),
        owner=user,
        lines_data=[{"item": Item.objects.create(name="خدمت").id,
                     "quantity": 1, "unit_price": amount}],
        actor=user)


def test_invoice_payment_status_progression(seeded, make_user):
    user = make_user("09120000081", "حسابدار", role_code="accounting_manager")
    inv = _service_invoice(user, 10_000_000)
    assert inv.payment_status == "UNPAID"
    assert inv.remaining == Decimal("10000000")

    # Partial receipt.
    p1 = Payment.objects.create(direction=Payment.Direction.RECEIPT, party=inv.customer,
                                amount=4_000_000, account=_bank(), date=date.today(),
                                owner=user, invoice=inv)
    acc.register_payment(p1, actor=user)
    assert inv.payment_status == "PARTIAL"
    assert inv.paid_amount == Decimal("4000000")
    assert inv.remaining == Decimal("6000000")

    # Settle the rest.
    p2 = Payment.objects.create(direction=Payment.Direction.RECEIPT, party=inv.customer,
                                amount=6_000_000, account=_bank(), date=date.today(),
                                owner=user, invoice=inv)
    acc.register_payment(p2, actor=user)
    assert inv.payment_status == "PAID"
    assert inv.remaining == Decimal("0")


def test_cancelled_receipt_excluded_from_paid(seeded, make_user):
    user = make_user("09120000082", "حسابدار", role_code="accounting_manager")
    inv = _service_invoice(user, 5_000_000)
    p = Payment.objects.create(direction=Payment.Direction.RECEIPT, party=inv.customer,
                               amount=5_000_000, account=_bank(), date=date.today(),
                               owner=user, invoice=inv)
    acc.register_payment(p, actor=user)
    assert inv.payment_status == "PAID"
    # Cancel the receipt → invoice returns to unpaid.
    p.status = Payment.Status.CANCELLED
    p.save(update_fields=["status"])
    assert inv.payment_status == "UNPAID"


def test_receipt_via_api_links_invoice(seeded, make_user):
    from rest_framework.test import APIClient
    from rest_framework_simplejwt.tokens import RefreshToken

    user = make_user("09120000083", "حسابدار", role_code="accounting_manager")
    inv = _service_invoice(user, 3_000_000)
    api = APIClient()
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    resp = api.post("/api/payments", {
        "direction": "RECEIPT", "party": inv.customer_id, "amount": 3_000_000,
        "account": _bank().id, "invoice": inv.id,
    }, format="json")
    assert resp.status_code == 201, resp.data
    inv.refresh_from_db()
    assert inv.payment_status == "PAID"
    # The invoice API now reports it settled.
    got = api.get(f"/api/invoices/{inv.id}").data
    assert got["payment_status"] == "PAID" and str(got["remaining"]) in ("0", "0.0")
