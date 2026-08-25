"""Sales (فروش): Proforma state machine + Invoice (Section 5).

Proforma lifecycle:
    DRAFT → CONFIRMED → AWAITING_PURCHASE → READY → INVOICED
    side states: CANCELLED, UNFULFILLABLE

Each goods line links one-to-one to a specific PurchaseLine — the basis of the
5% rule (Section 6). Converting to an invoice enforces that rule per line and
posts the sale's financial effect automatically.
"""
from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.core.models import Item, NumberedModel, Party, TimeStampedModel
from apps.procurement.models import PurchaseLine


class ProformaStatus(models.TextChoices):
    DRAFT = "DRAFT", "پیش‌فاکتور"
    CONFIRMED = "CONFIRMED", "تأییدشده"
    AWAITING_PURCHASE = "AWAITING_PURCHASE", "منتظر خرید"
    READY = "READY", "آماده فاکتور"
    INVOICED = "INVOICED", "فاکتورشده"
    CANCELLED = "CANCELLED", "ابطال‌شده"
    UNFULFILLABLE = "UNFULFILLABLE", "تأمین‌نشدنی"


class Proforma(NumberedModel):
    """A proforma (پیش‌فاکتور) owned by the salesperson who created it."""

    number_prefix = "PF"
    number = models.CharField(max_length=30, unique=True, blank=True)
    customer = models.ForeignKey(Party, on_delete=models.PROTECT, related_name="proformas")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="proformas"
    )
    status = models.CharField(
        max_length=20, choices=ProformaStatus.choices, default=ProformaStatus.DRAFT,
        db_index=True,
    )
    # Section 5: 48h soft reservation starts when the proforma is confirmed.
    confirmed_at = models.DateTimeField(null=True, blank=True)
    reservation_expires_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "پیش‌فاکتور"
        verbose_name_plural = "پیش‌فاکتورها"

    def __str__(self) -> str:
        return self.number or f"پیش‌فاکتور #{self.pk}"

    @property
    def total(self) -> Decimal:
        return sum((l.line_total for l in self.lines.all()), Decimal("0"))

    @property
    def margin(self) -> Decimal:
        """Absolute profit margin — the tiebreak metric on true concurrency."""
        return sum((l.margin for l in self.lines.all()), Decimal("0"))


class ProformaLine(TimeStampedModel):
    proforma = models.ForeignKey(Proforma, on_delete=models.CASCADE, related_name="lines")
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name="proforma_lines")
    description = models.CharField(max_length=255, blank=True)
    quantity = models.DecimalField(max_digits=14, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=18, decimal_places=0, default=0)
    # One-to-one link to the purchase line that supplies this sale line.
    source_purchase_line = models.ForeignKey(
        PurchaseLine, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="proforma_lines",
    )

    class Meta:
        ordering = ["id"]

    @property
    def line_total(self) -> Decimal:
        return Decimal(self.quantity) * Decimal(self.unit_price)

    @property
    def margin(self) -> Decimal:
        if not self.source_purchase_line:
            return Decimal("0")
        cost = Decimal(self.source_purchase_line.unit_price) * Decimal(self.quantity)
        return self.line_total - cost


class Invoice(NumberedModel):
    """A final invoice (فاکتور). Covers goods, service and monthly support."""

    number_prefix = "IN"

    class Type(models.TextChoices):
        GOODS = "GOODS", "فروش کالا"
        SERVICE = "SERVICE", "خدمات"
        SUPPORT = "SUPPORT", "پشتیبانی ماهانه"

    class Status(models.TextChoices):
        ISSUED = "ISSUED", "صادرشده"
        CANCELLED = "CANCELLED", "ابطال‌شده"
        RETURNED = "RETURNED", "مرجوع‌شده"

    number = models.CharField(max_length=30, unique=True, blank=True)
    type = models.CharField(max_length=10, choices=Type.choices, default=Type.GOODS)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ISSUED)
    customer = models.ForeignKey(Party, on_delete=models.PROTECT, related_name="invoices")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="invoices"
    )
    proforma = models.OneToOneField(
        Proforma, null=True, blank=True, on_delete=models.SET_NULL, related_name="invoice"
    )
    date = models.DateField()
    # For monthly support invoices (Section 4.3).
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "فاکتور"
        verbose_name_plural = "فاکتورها"

    def __str__(self) -> str:
        return self.number or f"فاکتور #{self.pk}"

    @property
    def total(self) -> Decimal:
        return sum((l.line_total for l in self.lines.all()), Decimal("0"))


class InvoiceLine(TimeStampedModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines")
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name="invoice_lines")
    description = models.CharField(max_length=255, blank=True)
    quantity = models.DecimalField(max_digits=14, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=18, decimal_places=0, default=0)
    # Goods lines carry their source purchase line (Section 8: FK to origin purchase).
    source_purchase_line = models.ForeignKey(
        PurchaseLine, null=True, blank=True, on_delete=models.PROTECT,
        related_name="invoice_lines",
    )

    class Meta:
        ordering = ["id"]

    @property
    def line_total(self) -> Decimal:
        return Decimal(self.quantity) * Decimal(self.unit_price)
