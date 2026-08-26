"""Accounting service: post and reverse balanced journal entries atomically.

Well-known account codes are named here so the department services (procurement,
sales, technical) reference roles, not magic strings. Resolves the "exact
financial effect" open decisions (Section 10) with a conventional double-entry
scheme, documented per event below.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from django.db import transaction

from apps.core.services import log_action

from .models import Account, JournalEntry, JournalLine


# --- Well-known chart-of-accounts codes (seeded in management.seed) ---------
CASH = "1100"                # صندوق/بانک
ACCOUNTS_RECEIVABLE = "1200"  # حساب‌های دریافتنی (مشتری بدهکار)
INVENTORY = "1300"           # موجودی کالا (خرید تا فروش)
ACCOUNTS_PAYABLE = "2100"     # حساب‌های پرداختنی (بدهی به تأمین‌کننده)
SALES_INCOME = "4100"        # درآمد فروش کالا
SERVICE_INCOME = "4200"      # درآمد خدمات
SUPPORT_INCOME = "4300"      # درآمد پشتیبانی
COGS = "5100"                # بهای تمام‌شده کالای فروش‌رفته
DIRECT_EXPENSE = "5200"      # هزینه‌های مستقیم
OVERHEAD_EXPENSE = "5300"    # هزینه‌های سربار


@dataclass
class Line:
    """A single posting line for :func:`post_entry`."""

    account_code: str
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
    party: Any = None
    description: str = ""


class UnbalancedEntry(Exception):
    """Raised when debit != credit — a journal entry is never posted half-way."""


def _next_number() -> str:
    last = JournalEntry.objects.order_by("-id").first()
    seq = (last.id + 1) if last else 1
    return f"JE-{seq:06d}"


@transaction.atomic
def post_entry(
    *,
    description: str,
    lines: list[Line],
    actor=None,
    source_ref: str = "",
    on_date: date | None = None,
) -> JournalEntry:
    """Create a balanced :class:`JournalEntry`. Atomic; rejects if unbalanced."""
    total_debit = sum((l.debit for l in lines), Decimal("0"))
    total_credit = sum((l.credit for l in lines), Decimal("0"))
    if total_debit != total_credit or total_debit == 0:
        raise UnbalancedEntry(
            f"سند متوازن نیست: بدهکار {total_debit} ≠ بستانکار {total_credit}"
        )

    entry = JournalEntry.objects.create(
        number=_next_number(),
        date=on_date or date.today(),
        description=description,
        source_ref=source_ref,
        created_by=actor if getattr(actor, "is_authenticated", False) else None,
    )
    accounts = {a.code: a for a in Account.objects.filter(
        code__in={l.account_code for l in lines}
    )}
    for l in lines:
        JournalLine.objects.create(
            entry=entry,
            account=accounts[l.account_code],
            party=l.party,
            debit=l.debit,
            credit=l.credit,
            description=l.description,
        )
    log_action(actor, "accounting.post_entry", f"accounting.journalentry:{entry.id}",
               source_ref=source_ref, amount=str(total_debit))
    return entry


@transaction.atomic
def register_expense(expense, *, actor=None):
    """Post an expense: expense account (debit) / cash-bank (credit). Atomic."""
    from .models import Expense

    code = DIRECT_EXPENSE if expense.kind == Expense.Kind.DIRECT else OVERHEAD_EXPENSE
    entry = post_entry(
        description=f"هزینه {expense.category} ({expense.get_kind_display()})",
        source_ref=f"accounting.expense:{expense.id}",
        actor=actor,
        on_date=expense.date,
        lines=[
            Line(code, debit=expense.amount, party=expense.party,
                 description=expense.description or expense.category),
            Line(expense.paid_from.code, credit=expense.amount,
                 description="پرداخت هزینه"),
        ],
    )
    return entry


@transaction.atomic
def register_payment(payment, *, actor=None):
    """Post a receipt/payment against a party balance. Atomic.

    RECEIPT: cash/bank (debit) / receivable (credit).
    PAYMENT: payable (debit) / cash/bank (credit).
    """
    from .models import Payment

    if payment.direction == Payment.Direction.RECEIPT:
        lines = [
            Line(payment.account.code, debit=payment.amount, description="دریافت وجه"),
            Line(ACCOUNTS_RECEIVABLE, credit=payment.amount, party=payment.party,
                 description=f"دریافت از {payment.party.name}"),
        ]
        desc = f"دریافت از {payment.party.name}"
    else:
        lines = [
            Line(ACCOUNTS_PAYABLE, debit=payment.amount, party=payment.party,
                 description=f"پرداخت به {payment.party.name}"),
            Line(payment.account.code, credit=payment.amount, description="پرداخت وجه"),
        ]
        desc = f"پرداخت به {payment.party.name}"
    return post_entry(description=desc, source_ref=f"accounting.payment:{payment.id}",
                      actor=actor, on_date=payment.date, lines=lines)


@transaction.atomic
def reverse_document(source_ref: str, *, actor=None, description: str = ""):
    """Reverse the journal entry posted for a financial document, if any."""
    origin = JournalEntry.objects.filter(source_ref=source_ref, is_reversal=False).first()
    if origin and not origin.reversed_by.exists():
        return reverse_entry(origin, actor=actor, description=description)
    return None


@transaction.atomic
def reverse_entry(entry: JournalEntry, *, actor=None, description: str = "") -> JournalEntry:
    """Post a mirror entry that reverses ``entry`` (Section 5 return paths)."""
    reversal = JournalEntry.objects.create(
        number=_next_number(),
        date=date.today(),
        description=description or f"برگشت سند {entry.number}",
        source_ref=entry.source_ref,
        is_reversal=True,
        reversal_of=entry,
        created_by=actor if getattr(actor, "is_authenticated", False) else None,
    )
    for line in entry.lines.all():
        JournalLine.objects.create(
            entry=reversal,
            account=line.account,
            party=line.party,
            debit=line.credit,   # swap
            credit=line.debit,
            description=f"برگشت: {line.description}",
        )
    log_action(actor, "accounting.reverse_entry",
               f"accounting.journalentry:{reversal.id}", reversed=entry.id)
    return reversal
