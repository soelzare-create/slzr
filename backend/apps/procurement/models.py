"""Procurement (بازرگانی): purchases and their financial effect (Section 5).

A purchase request is created (often from sales), assigned by the procurement
manager to self or an employee, then *registered*. Registering a purchase:
  - produces a balanced JournalEntry (inventory ⇑, payable to supplier ⇑), and
  - notifies sales that the goods are "ready to invoice".

Each sale line links one-to-one to a specific PurchaseLine — the unambiguous
basis for the 5% rule (Section 6).
"""
from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.core.models import Item, NumberedModel, Party, TimeStampedModel


class Purchase(NumberedModel):
    """A purchase document from a supplier."""

    number_prefix = "PU"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "پیش‌نویس"
        REGISTERED = "REGISTERED", "ثبت‌شده"
        CANCELLED = "CANCELLED", "ابطال‌شده"

    number = models.CharField(max_length=30, unique=True, blank=True)
    supplier = models.ForeignKey(
        Party, on_delete=models.PROTECT, related_name="purchases"
    )
    # The employee/manager the purchase is assigned to (object-level ownership).
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="purchases"
    )
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    # Set when the purchase originates from a sales proforma that needs stock.
    origin_ref = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "خرید"
        verbose_name_plural = "خریدها"

    def __str__(self) -> str:
        return self.number or f"خرید #{self.pk}"

    @property
    def total(self) -> Decimal:
        return sum((l.line_total for l in self.lines.all()), Decimal("0"))

    @property
    def paid_amount(self) -> Decimal:
        from django.db.models import Sum
        agg = self.settlements.filter(status="REGISTERED").aggregate(s=Sum("amount"))
        return agg["s"] or Decimal("0")

    @property
    def remaining(self) -> Decimal:
        return self.total - self.paid_amount

    @property
    def payment_status(self) -> str:
        paid = self.paid_amount
        if paid <= 0:
            return "UNPAID"
        return "PAID" if paid >= self.total else "PARTIAL"


class PurchaseLine(TimeStampedModel):
    """One line of a purchase — the source a sale line attaches to (one-to-one)."""

    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name="lines")
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name="purchase_lines")
    description = models.CharField(max_length=255, blank=True)
    quantity = models.DecimalField(max_digits=14, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=18, decimal_places=0, default=0)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return f"{self.item} × {self.quantity}"

    @property
    def line_total(self) -> Decimal:
        return Decimal(self.quantity) * Decimal(self.unit_price)
