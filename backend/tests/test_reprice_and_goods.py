"""Editing an issued invoice's amount (reprice) and issuing a direct goods
invoice from the invoices screen."""
from __future__ import annotations

from decimal import Decimal

import pytest

from apps.accounting.models import JournalEntry, JournalLine
from apps.core.models import Item, Party
from apps.procurement.models import Purchase, PurchaseLine
from apps.procurement import services as proc
from apps.sales.models import Invoice, Proforma, ProformaLine
from apps.sales import services as sales

pytestmark = pytest.mark.django_db


def _auth(api, user):
    from rest_framework_simplejwt.tokens import RefreshToken
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return api


def _active_entry(invoice):
    return JournalEntry.objects.filter(
        source_ref=f"sales.invoice:{invoice.id}", is_reversal=False, reversed_by__isnull=True
    ).order_by("-id").first()


# --- reprice a direct (service) invoice ------------------------------------

def test_reprice_direct_invoice_updates_total_and_ledger(seeded, make_user, api):
    seller = make_user("09120000061", "فروشنده", role_code="sales_employee")
    customer = Party.objects.create(name="مشتری", is_customer=True)
    item = Item.objects.create(name="خدمت نصب", kind=Item.Kind.SERVICE)
    inv = sales.create_direct_invoice(
        invoice_type=Invoice.Type.SERVICE, customer=customer, owner=seller,
        lines_data=[{"item": item.id, "quantity": 1, "unit_price": 1000}], actor=seller,
    )
    line = inv.lines.first()
    assert inv.total == Decimal("1000")

    _auth(api, seller)
    resp = api.post(f"/api/invoices/{inv.id}/reprice", {
        "lines": [{"id": line.id, "quantity": 2, "unit_price": 1500}],
    }, format="json")
    assert resp.status_code == 200, resp.data
    assert int(resp.data["total"]) == 3000

    # ledger: old entry reversed, a fresh active entry reflects the new amount
    origin = JournalEntry.objects.filter(
        source_ref=f"sales.invoice:{inv.id}", is_reversal=False).order_by("id").first()
    assert origin.reversed_by.exists()
    assert _active_entry(inv).total_debit == Decimal("3000")


# --- reprice a goods invoice: 5% rule still holds, COGS preserved -----------

def _goods_invoice(seller, buyer, customer, supplier, item, cost, price):
    purchase = Purchase.objects.create(supplier=supplier, owner=buyer)
    pline = PurchaseLine.objects.create(purchase=purchase, item=item,
                                        quantity=1, unit_price=cost)
    proc.register_purchase(purchase, actor=buyer)
    proforma = Proforma.objects.create(customer=customer, owner=seller)
    ProformaLine.objects.create(proforma=proforma, item=item, quantity=1,
                                unit_price=price, source_purchase_line=pline)
    sales.confirm_proforma(proforma, actor=seller)
    return sales.convert_to_invoice(proforma, actor=seller)


def test_reprice_goods_enforces_five_percent_and_keeps_cogs(seeded, make_user, api):
    seller = make_user("09120000062", "فروشنده", role_code="sales_employee")
    buyer = make_user("09120000063", "بازرگان", role_code="procurement_manager")
    customer = Party.objects.create(name="مشتری", is_customer=True)
    supplier = Party.objects.create(name="تأمین", is_supplier=True)
    item = Item.objects.create(name="لپ‌تاپ", kind=Item.Kind.GOODS, unit="دستگاه")
    inv = _goods_invoice(seller, buyer, customer, supplier, item,
                         cost=1_000_000, price=1_200_000)
    line = inv.lines.first()
    _auth(api, seller)

    # below the 1.05× floor → rejected, amount unchanged
    bad = api.post(f"/api/invoices/{inv.id}/reprice", {
        "lines": [{"id": line.id, "quantity": 1, "unit_price": 1_040_000}],
    }, format="json")
    assert bad.status_code == 400
    inv.refresh_from_db()
    assert inv.total == Decimal("1200000")

    # valid new price → total updates, COGS (1.0m) preserved in the fresh entry
    ok = api.post(f"/api/invoices/{inv.id}/reprice", {
        "lines": [{"id": line.id, "quantity": 1, "unit_price": 1_300_000}],
    }, format="json")
    assert ok.status_code == 200, ok.data
    assert int(ok.data["total"]) == 1_300_000
    # active entry = sale 1.3m + COGS relief 1.0m → total debit 2.3m
    assert _active_entry(inv).total_debit == Decimal("2300000")

    # a later cancel still reverses the live entry (reprice didn't orphan it)
    sales.reverse_invoice(inv, actor=seller)
    assert _active_entry(inv) is None


# --- direct goods invoice from the invoices screen -------------------------

def test_direct_goods_invoice_via_api(seeded, make_user, api):
    tech = make_user("09120000064", "فنی", role_code="technical_manager")
    customer = Party.objects.create(name="مشتری", is_customer=True)
    item = Item.objects.create(name="کابل", kind=Item.Kind.GOODS)
    _auth(api, tech)
    resp = api.post("/api/technical/invoices", {
        "type": "GOODS", "customer": customer.id,
        "lines": [{"item": item.id, "quantity": 3, "unit_price": 2000}],
    }, format="json")
    assert resp.status_code == 201, resp.data
    assert resp.data["type"] == "GOODS"
    assert int(resp.data["total"]) == 6000
    # income booked to sales income (4100), no COGS line
    inv_id = resp.data["id"]
    sales_income = JournalLine.objects.filter(
        entry__source_ref=f"sales.invoice:{inv_id}", account__code="4100").first()
    assert sales_income is not None and sales_income.credit == Decimal("6000")
    cogs = JournalLine.objects.filter(
        entry__source_ref=f"sales.invoice:{inv_id}", account__code="5100").exists()
    assert cogs is False
