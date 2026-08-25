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
