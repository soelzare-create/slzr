"""End-to-end tests for the core sales workflow (Sections 5 & 6)."""
from __future__ import annotations

from decimal import Decimal

import pytest

from apps.accounting.models import JournalEntry
from apps.core.models import Item, Party
from apps.procurement.models import Purchase, PurchaseLine
from apps.procurement import services as proc
from apps.sales.models import Invoice, Proforma, ProformaLine, ProformaStatus
from apps.sales import services as sales

pytestmark = pytest.mark.django_db


def _setup(seeded, make_user):
    seller = make_user("09120000001", "فروشنده", role_code="sales_employee")
    buyer = make_user("09120000002", "خریدار بازرگانی", role_code="procurement_manager")
    customer = Party.objects.create(name="مشتری الف", is_customer=True)
    supplier = Party.objects.create(name="تأمین‌کننده ب", is_supplier=True)
    item = Item.objects.create(name="لپ‌تاپ", unit="دستگاه")
    return seller, buyer, customer, supplier, item


def _registered_purchase(buyer, supplier, item, unit_price):
    purchase = Purchase.objects.create(supplier=supplier, owner=buyer)
    line = PurchaseLine.objects.create(purchase=purchase, item=item,
                                       quantity=1, unit_price=unit_price)
    proc.register_purchase(purchase, actor=buyer)
    return purchase, line


def test_full_flow_creates_balanced_journal_entries(seeded, make_user):
    seller, buyer, customer, supplier, item = _setup(seeded, make_user)
    purchase, pline = _registered_purchase(buyer, supplier, item, 1_000_000)

    # Purchase registration posts a balanced entry.
    pe = JournalEntry.objects.get(source_ref=f"procurement.purchase:{purchase.id}")
    assert pe.is_balanced and pe.total_debit == Decimal("1000000")

    proforma = Proforma.objects.create(customer=customer, owner=seller)
    ProformaLine.objects.create(proforma=proforma, item=item, quantity=1,
                                unit_price=1_200_000, source_purchase_line=pline)
    sales.confirm_proforma(proforma, actor=seller)
    invoice = sales.convert_to_invoice(proforma, actor=seller)

    proforma.refresh_from_db()
    assert proforma.status == ProformaStatus.INVOICED
    assert invoice.type == Invoice.Type.GOODS

    se = JournalEntry.objects.get(source_ref=f"sales.invoice:{invoice.id}")
    assert se.is_balanced
    # Sale (1.2m) + COGS relief (1.0m) → total debit 2.2m.
    assert se.total_debit == Decimal("2200000")


def test_five_percent_rule_blocks_thin_margin(seeded, make_user):
    seller, buyer, customer, supplier, item = _setup(seeded, make_user)
    _, pline = _registered_purchase(buyer, supplier, item, 1_000_000)

    proforma = Proforma.objects.create(customer=customer, owner=seller)
    # 1.04× purchase < required 1.05× → must be rejected.
    ProformaLine.objects.create(proforma=proforma, item=item, quantity=1,
                                unit_price=1_040_000, source_purchase_line=pline)
    sales.confirm_proforma(proforma, actor=seller)
    with pytest.raises(sales.FivePercentViolation):
        sales.convert_to_invoice(proforma, actor=seller)
    # No invoice, no journal entry created for the rejected conversion.
    assert not Invoice.objects.filter(proforma=proforma).exists()


def test_five_percent_rule_allows_exactly_105(seeded, make_user):
    seller, buyer, customer, supplier, item = _setup(seeded, make_user)
    _, pline = _registered_purchase(buyer, supplier, item, 1_000_000)
    proforma = Proforma.objects.create(customer=customer, owner=seller)
    ProformaLine.objects.create(proforma=proforma, item=item, quantity=1,
                                unit_price=1_050_000, source_purchase_line=pline)
    sales.confirm_proforma(proforma, actor=seller)
    invoice = sales.convert_to_invoice(proforma, actor=seller)
    assert invoice.total == Decimal("1050000")


def test_convert_requires_registered_purchase(seeded, make_user):
    seller, buyer, customer, supplier, item = _setup(seeded, make_user)
    purchase = Purchase.objects.create(supplier=supplier, owner=buyer)  # not registered
    pline = PurchaseLine.objects.create(purchase=purchase, item=item,
                                        quantity=1, unit_price=1_000_000)
    proforma = Proforma.objects.create(customer=customer, owner=seller)
    ProformaLine.objects.create(proforma=proforma, item=item, quantity=1,
                                unit_price=2_000_000, source_purchase_line=pline)
    sales.confirm_proforma(proforma, actor=seller)
    with pytest.raises(sales.InvalidTransition):
        sales.convert_to_invoice(proforma, actor=seller)


def test_confirmed_cancel_needs_manager(seeded, make_user):
    seller, *_ = _setup(seeded, make_user)
    customer = Party.objects.create(name="م", is_customer=True)
    proforma = Proforma.objects.create(customer=customer, owner=seller)
    sales.confirm_proforma(proforma, actor=seller)
    with pytest.raises(sales.InvalidTransition):
        sales.cancel_proforma(proforma, actor=seller, manager_approved=False)
    sales.cancel_proforma(proforma, actor=seller, manager_approved=True)
    proforma.refresh_from_db()
    assert proforma.status == ProformaStatus.CANCELLED


def test_reservation_expiry_releases(seeded, make_user):
    from django.utils import timezone
    from datetime import timedelta

    seller, *_ = _setup(seeded, make_user)
    customer = Party.objects.create(name="م", is_customer=True)
    proforma = Proforma.objects.create(customer=customer, owner=seller)
    sales.confirm_proforma(proforma, actor=seller)
    # Force the reservation into the past.
    Proforma.objects.filter(pk=proforma.pk).update(
        reservation_expires_at=timezone.now() - timedelta(hours=1))
    released = sales.release_expired_reservations()
    assert released == 1
    proforma.refresh_from_db()
    assert proforma.status == ProformaStatus.DRAFT


def test_invoice_reversal_creates_mirror_entry(seeded, make_user):
    seller, buyer, customer, supplier, item = _setup(seeded, make_user)
    _, pline = _registered_purchase(buyer, supplier, item, 1_000_000)
    proforma = Proforma.objects.create(customer=customer, owner=seller)
    ProformaLine.objects.create(proforma=proforma, item=item, quantity=1,
                                unit_price=1_200_000, source_purchase_line=pline)
    sales.confirm_proforma(proforma, actor=seller)
    invoice = sales.convert_to_invoice(proforma, actor=seller)
    sales.reverse_invoice(invoice, actor=seller, returned=True)
    origin = JournalEntry.objects.get(source_ref=f"sales.invoice:{invoice.id}",
                                      is_reversal=False)
    assert origin.reversed_by.exists()
