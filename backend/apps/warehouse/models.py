"""Warehouse (انبار): physical goods-receipt of a registered purchase.

When procurement registers a purchase, the goods still have to be physically
received by the warehouse. A GoodsReceipt records that hand-over, and the
warehouse enters the serial numbers of the received units on it.

This is a record layer only — it does not gate invoicing and does not post a
journal entry (the purchase already did that on registration). Serials are
optional per line (a non-serialised item can be received with none).
"""
from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.models import Item, NumberedModel, TimeStampedModel
from apps.procurement.models import Purchase, PurchaseLine


class GoodsReceipt(NumberedModel):
    """رسید ورود انبار — تحویل فیزیکی کالاهای یک خرید ثبت‌شده."""

    number_prefix = "GR"
    number = models.CharField(max_length=30, unique=True, blank=True)
    purchase = models.ForeignKey(
        Purchase, on_delete=models.PROTECT, related_name="goods_receipts"
    )
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="goods_receipts"
    )
    received_at = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "رسید انبار"
        verbose_name_plural = "رسیدهای انبار"

    def __str__(self) -> str:
        return self.number or f"رسید #{self.pk}"


class ReceiptItem(TimeStampedModel):
    """One received line — how many units arrived and their (optional) serials."""

    receipt = models.ForeignKey(GoodsReceipt, on_delete=models.CASCADE, related_name="items")
    purchase_line = models.ForeignKey(
        PurchaseLine, on_delete=models.PROTECT, related_name="receipt_items"
    )
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name="receipt_items")
    quantity = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    # Optional per-unit serial numbers, e.g. ["SN-1", "SN-2"]. May be empty.
    serials = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return f"{self.item} × {self.quantity}"
