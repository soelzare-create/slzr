"""Sales flow — decoupled design.

A proforma converts straight to a goods invoice (no confirmation, no 5% rule,
no purchase prerequisite). The invoice books income only. Purchasing is a
separate track: a purchase is linked to the invoice and, when registered, books
the cost as an expense. One invoice may have several purchases.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from apps.accounting.models import JournalEntry, JournalLine
from apps.core.models import Item, Party
from apps.procurement.models import Purchase, PurchaseLine
from apps.procurement import services as proc
from apps.sales.models import Invoice, Proforma, ProformaLine, ProformaStatus
from apps.sales import services as sales

pytestmark = pytest.mark.django_db


def _setup(seeded, make_user):
    seller = make_user("09120000001", "فروشنده", role_code="sales_employee")
    buyer = make_user("09120000002", "بازرگان", role_code="procurement_manager")
    customer = Party.objects.create(name="مشتری الف", is_customer=True)
    supplier = Party.objects.create(name="تأمین‌کننده ب", is_supplier=True)
    item = Item.objects.create(name="لپ‌تاپ", kind=Item.Kind.GOODS, unit="دستگاه")
    return seller, buyer, customer, supplier, item


def _invoice(seller, customer, item, qty=1, price=1_200_000):
    proforma = Proforma.objects.create(customer=customer, owner=seller)
    ProformaLine.objects.create(proforma=proforma, item=item, quantity=qty, unit_price=price)
    return sales.convert_to_invoice(proforma, actor=seller)


def test_convert_is_direct_and_books_income_only(seeded, make_user):
    seller, buyer, customer, supplier, item = _setup(seeded, make_user)
    invoice = _invoice(seller, customer, item, qty=1, price=1_200_000)

    invoice.proforma.refresh_from_db()
    assert invoice.type == Invoice.Type.GOODS
    assert invoice.proforma.status == ProformaStatus.INVOICED

    se = JournalEntry.objects.get(source_ref=f"sales.invoice:{invoice.id}")
    assert se.is_balanced and se.total_debit == Decimal("1200000")  # AR / income only
    # no cost-of-goods or inventory posting at invoice time
    codes = set(JournalLine.objects.filter(entry=se).values_list("account__code", flat=True))
    assert codes == {"1200", "4100"}


def test_purchase_registered_books_expense(seeded, make_user):
    seller, buyer, customer, supplier, item = _setup(seeded, make_user)
    purchase = Purchase.objects.create(supplier=supplier, owner=buyer)
    PurchaseLine.objects.create(purchase=purchase, item=item, quantity=1, unit_price=1_000_000)
    proc.register_purchase(purchase, actor=buyer)

    pe = JournalEntry.objects.get(source_ref=f"procurement.purchase:{purchase.id}")
    assert pe.is_balanced and pe.total_debit == Decimal("1000000")
    codes = set(JournalLine.objects.filter(entry=pe).values_list("account__code", flat=True))
    assert codes == {"5100", "2100"}  # COGS / payable — independent of any invoice


def test_invoice_can_link_several_purchases(seeded, make_user):
    seller, buyer, customer, supplier, item = _setup(seeded, make_user)
    invoice = _invoice(seller, customer, item)
    supplier2 = Party.objects.create(name="تأمین‌کنندهٔ دوم", is_supplier=True)

    for sup in (supplier, supplier2):
        pur = Purchase.objects.create(supplier=sup, owner=buyer, sale_invoice=invoice)
        PurchaseLine.objects.create(purchase=pur, item=item, quantity=1, unit_price=500_000)
        proc.register_purchase(pur, actor=buyer)

    assert invoice.purchases.count() == 2  # one invoice ← many purchases


def test_proforma_cancel(seeded, make_user):
    seller, *_ = _setup(seeded, make_user)
    customer = Party.objects.create(name="م", is_customer=True)
    proforma = Proforma.objects.create(customer=customer, owner=seller)
    sales.cancel_proforma(proforma, actor=seller, manager_approved=True)
    proforma.refresh_from_db()
    assert proforma.status == ProformaStatus.CANCELLED


def test_invoice_reversal_creates_mirror_entry(seeded, make_user):
    seller, buyer, customer, supplier, item = _setup(seeded, make_user)
    invoice = _invoice(seller, customer, item)
    sales.reverse_invoice(invoice, actor=seller, returned=True)
    origin = JournalEntry.objects.get(source_ref=f"sales.invoice:{invoice.id}",
                                      is_reversal=False)
    assert origin.reversed_by.exists()
