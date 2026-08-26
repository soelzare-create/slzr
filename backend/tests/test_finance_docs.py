"""Tests for the financial-documents module: expense, receipt, payment."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from apps.accounting.models import Account, Expense, JournalEntry, Payment
from apps.accounting import services as acc
from apps.core.models import Party

pytestmark = pytest.mark.django_db


def _bank(seeded):
    return Account.objects.get(code="1120")


def test_direct_expense_posts_balanced_entry(seeded, make_user):
    user = make_user("09120000051", "حسابدار", role_code="accounting_manager")
    bank = _bank(seeded)
    exp = Expense.objects.create(kind=Expense.Kind.DIRECT, category="حمل‌ونقل",
                                 amount=5_000_000, paid_from=bank, date=date.today(),
                                 owner=user)
    acc.register_expense(exp, actor=user)
    e = JournalEntry.objects.get(source_ref=f"accounting.expense:{exp.id}")
    assert e.is_balanced and e.total_debit == Decimal("5000000")
    # Debit hits the direct-expense account 5200.
    assert e.lines.filter(account__code="5200", debit=5_000_000).exists()
    assert e.lines.filter(account__code="1120", credit=5_000_000).exists()


def test_overhead_expense_hits_5300(seeded, make_user):
    user = make_user("09120000052", "حسابدار", role_code="accounting_manager")
    exp = Expense.objects.create(kind=Expense.Kind.OVERHEAD, category="اجاره",
                                 amount=25_000_000, paid_from=_bank(seeded),
                                 date=date.today(), owner=user)
    acc.register_expense(exp, actor=user)
    e = JournalEntry.objects.get(source_ref=f"accounting.expense:{exp.id}")
    assert e.lines.filter(account__code="5300", debit=25_000_000).exists()


def test_receipt_reduces_receivable(seeded, make_user):
    user = make_user("09120000053", "حسابدار", role_code="accounting_manager")
    customer = Party.objects.create(name="مشتری", is_customer=True)
    pay = Payment.objects.create(direction=Payment.Direction.RECEIPT, party=customer,
                                 amount=8_000_000, account=_bank(seeded),
                                 date=date.today(), owner=user)
    acc.register_payment(pay, actor=user)
    e = JournalEntry.objects.get(source_ref=f"accounting.payment:{pay.id}")
    assert e.is_balanced
    assert e.lines.filter(account__code="1120", debit=8_000_000).exists()
    assert e.lines.filter(account__code="1200", credit=8_000_000, party=customer).exists()


def test_payment_reduces_payable_and_reversal(seeded, make_user):
    user = make_user("09120000054", "حسابدار", role_code="accounting_manager")
    supplier = Party.objects.create(name="تأمین", is_supplier=True)
    pay = Payment.objects.create(direction=Payment.Direction.PAYMENT, party=supplier,
                                 amount=3_000_000, account=_bank(seeded),
                                 date=date.today(), owner=user)
    acc.register_payment(pay, actor=user)
    e = JournalEntry.objects.get(source_ref=f"accounting.payment:{pay.id}")
    assert e.lines.filter(account__code="2100", debit=3_000_000, party=supplier).exists()
    # Reversal mirrors it.
    acc.reverse_document(f"accounting.payment:{pay.id}", actor=user)
    assert e.reversed_by.exists()


def test_expense_api_creates_document(seeded, make_user):
    from rest_framework.test import APIClient
    from rest_framework_simplejwt.tokens import RefreshToken

    user = make_user("09120000055", "حسابدار", role_code="accounting_manager")
    api = APIClient()
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    bank = _bank(seeded)
    resp = api.post("/api/expenses", {
        "kind": "OVERHEAD", "category": "اینترنت", "amount": 1_200_000,
        "paid_from": bank.id,
    }, format="json")
    assert resp.status_code == 201, resp.data
    assert resp.data["number"].startswith("EX-")
    assert JournalEntry.objects.filter(
        source_ref=f"accounting.expense:{resp.data['id']}").exists()
