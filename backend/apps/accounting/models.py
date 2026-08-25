"""Accounting: Chart of Accounts + double-entry Journal (Section 8).

Every financial event is generated automatically from a business event (a
purchase registration, a sale invoice), never entered by hand (Section 1). Each
posting is atomic and balanced (debit == credit), and reversible (Section 5).
"""
from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.core.models import Party, TimeStampedModel


class Account(TimeStampedModel):
    """A node in the Chart of Accounts (a small tree)."""

    class Type(models.TextChoices):
        ASSET = "ASSET", "دارایی"
        LIABILITY = "LIABILITY", "بدهی"
        EQUITY = "EQUITY", "سرمایه"
        INCOME = "INCOME", "درآمد"
        EXPENSE = "EXPENSE", "هزینه"

    code = models.CharField(max_length=20, unique=True)  # e.g. "1000"
    name = models.CharField(max_length=120)
    type = models.CharField(max_length=12, choices=Type.choices)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="children"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]
        verbose_name = "حساب"
        verbose_name_plural = "حساب‌ها"

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"

    @property
    def normal_is_debit(self) -> bool:
        return self.type in {self.Type.ASSET, self.Type.EXPENSE}


class JournalEntry(TimeStampedModel):
    """A balanced accounting document (سند)."""

    number = models.CharField(max_length=30, unique=True, blank=True)
    date = models.DateField()
    description = models.CharField(max_length=255)
    # Loose link to the business event that produced it (e.g. "sales.invoice:7").
    source_ref = models.CharField(max_length=64, blank=True, db_index=True)
    # Reversal support (Section 5): a reversing document points back at its origin.
    is_reversal = models.BooleanField(default=False)
    reversal_of = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="reversed_by"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        ordering = ["-date", "-id"]
        verbose_name = "سند حسابداری"
        verbose_name_plural = "اسناد حسابداری"

    def __str__(self) -> str:
        return f"{self.number} — {self.description}"

    @property
    def total_debit(self) -> Decimal:
        return sum((l.debit for l in self.lines.all()), Decimal("0"))

    @property
    def total_credit(self) -> Decimal:
        return sum((l.credit for l in self.lines.all()), Decimal("0"))

    @property
    def is_balanced(self) -> bool:
        return self.total_debit == self.total_credit


class JournalLine(TimeStampedModel):
    """One debit/credit line of a journal entry."""

    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name="lines")
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="lines")
    party = models.ForeignKey(
        Party, null=True, blank=True, on_delete=models.PROTECT, related_name="journal_lines"
    )
    debit = models.DecimalField(max_digits=18, decimal_places=0, default=0)
    credit = models.DecimalField(max_digits=18, decimal_places=0, default=0)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return f"{self.account.code} بدهکار {self.debit} / بستانکار {self.credit}"
