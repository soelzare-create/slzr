"""Core shared models: base mixins, Party, Item, Notification, AuditLog.

These are the foundation the department apps build on. Kept dependency-free so
every other app can import from ``core`` without cycles.
"""
from __future__ import annotations

from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    """Adds created/updated timestamps to any model."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class OwnedModel(TimeStampedModel):
    """Adds an ``owner`` for object-level ownership filtering.

    Section 3: employees only ever see their own records; the queryset is
    filtered by ``owner=user`` at object level, not at the role level.
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="%(app_label)s_%(class)s_owned",
    )

    class Meta:
        abstract = True


class NumberedModel(TimeStampedModel):
    """Auto-assigns a unique document ``number`` (``<prefix>-00001``) on first save.

    Subclasses set ``number_prefix``. Blank numbers would otherwise collide on the
    unique constraint (empty string is not NULL in SQLite/Postgres).
    """

    number_prefix = "DOC"
    number_pad = 5

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.number:
            last = type(self).objects.order_by("-id").first()
            seq = (last.id + 1) if last else 1
            self.number = f"{self.number_prefix}-{seq:0{self.number_pad}d}"
        super().save(*args, **kwargs)


class Party(TimeStampedModel):
    """A customer and/or supplier — a single record, no duplication.

    Section 8: Party (customer / supplier). One row can be both.
    """

    name = models.CharField(max_length=200, db_index=True)
    is_customer = models.BooleanField(default=True)
    is_supplier = models.BooleanField(default=False)

    national_id = models.CharField(max_length=20, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "طرف حساب"
        verbose_name_plural = "طرف حساب‌ها"

    def __str__(self) -> str:
        return self.name


class Item(TimeStampedModel):
    """A good or service. Base entity, ready for the future warehouse phase.

    Section 7: the warehouse module is NOT built this phase, but ``Item`` is the
    reserved base other tables (StockTransaction, SerialUnit) will hang off later.
    """

    class Kind(models.TextChoices):
        GOODS = "GOODS", "کالا"
        SERVICE = "SERVICE", "خدمت"

    name = models.CharField(max_length=200, db_index=True)
    sku = models.CharField(max_length=64, blank=True, db_index=True)
    unit = models.CharField(max_length=32, default="عدد")
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.GOODS)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "کالا/خدمت"
        verbose_name_plural = "کالاها/خدمات"

    def __str__(self) -> str:
        return self.name


class Notification(TimeStampedModel):
    """Dashboard notification. Kept off the critical path of financial writes.

    Section 2: registering an invoice must not depend on the notifications
    dashboard — notifications are created best-effort, after the atomic block.
    """

    class Kind(models.TextChoices):
        READY_TO_INVOICE = "READY_TO_INVOICE", "آماده فاکتور"
        PURCHASE_REQUEST = "PURCHASE_REQUEST", "درخواست خرید"
        RESERVATION_RELEASED = "RESERVATION_RELEASED", "آزادسازی رزرو"
        UNFULFILLABLE = "UNFULFILLABLE", "تأمین‌نشدنی"
        SUPPORT_DUE = "SUPPORT_DUE", "یادآوری پشتیبانی"
        GENERAL = "GENERAL", "عمومی"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    kind = models.CharField(max_length=32, choices=Kind.choices, default=Kind.GENERAL)
    message = models.TextField()
    # Loose link back to the source object (e.g. "sales.proforma:12").
    source_ref = models.CharField(max_length=64, blank=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "اعلان"
        verbose_name_plural = "اعلان‌ها"

    def __str__(self) -> str:
        return f"{self.get_kind_display()} → {self.recipient_id}"


class AuditLog(TimeStampedModel):
    """Immutable trail: who, when, what changed. Section 2 / Section 5."""

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=64)
    target = models.CharField(max_length=64, blank=True)  # e.g. "sales.proforma:12"
    detail = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "رویداد ممیزی"
        verbose_name_plural = "رویدادهای ممیزی"

    def __str__(self) -> str:
        return f"{self.action} {self.target}"
