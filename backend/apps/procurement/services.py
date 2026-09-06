"""Procurement service layer (Section 5): register / cancel a purchase.

Registering is one atomic financial event; the notification to sales is created
*after* the atomic block so a notification failure can never roll back a
registered purchase (Section 2).
"""
from __future__ import annotations

from datetime import date

from django.db import transaction

from apps.accounting import services as acc
from apps.accounting.services import Line
from apps.core.services import log_action, notify
from apps.core.models import Notification

from .models import Purchase


def _next_number() -> str:
    last = Purchase.objects.order_by("-id").first()
    seq = (last.id + 1) if last else 1
    return f"PU-{seq:05d}"


@transaction.atomic
def register_purchase(purchase: Purchase, *, actor=None) -> Purchase:
    """Register a purchase: post its financial effect. Atomic.

    In the current (decoupled) flow a purchase is its own document, independent
    of the sales side, so it is expensed directly:
        بهای تمام‌شده (بدهکار) / پرداختنی به تأمین‌کننده (بستانکار).
    """
    if purchase.status == Purchase.Status.REGISTERED:
        return purchase
    if purchase.status == Purchase.Status.CANCELLED:
        raise ValueError("خرید ابطال‌شده قابل ثبت نیست.")

    locked = Purchase.objects.select_for_update().get(pk=purchase.pk)
    total = locked.total
    if total <= 0:
        raise ValueError("مبلغ خرید باید بزرگتر از صفر باشد.")

    if not locked.number:
        locked.number = _next_number()
    locked.status = Purchase.Status.REGISTERED
    locked.date = locked.date or date.today()

    entry = acc.post_entry(
        description=f"خرید {locked.number} از {locked.supplier.name}",
        source_ref=f"procurement.purchase:{locked.id}",
        actor=actor,
        lines=[
            Line(acc.COGS, debit=total, description="بهای تمام‌شدهٔ خرید"),
            Line(acc.ACCOUNTS_PAYABLE, credit=total, party=locked.supplier,
                 description="بدهی به تأمین‌کننده"),
        ],
    )
    locked.save(update_fields=["number", "status", "date", "updated_at"])
    log_action(actor, "procurement.register_purchase",
               f"procurement.purchase:{locked.id}", journal_entry=entry.id)
    return locked


def notify_sales_ready(purchase: Purchase, sales_owner) -> None:
    """After registration, tell the originating sales owner it's ready to invoice."""
    if sales_owner is None:
        return
    notify(
        recipient=sales_owner,
        kind=Notification.Kind.READY_TO_INVOICE,
        message=f"کالای مرتبط با خرید {purchase.number} آماده فاکتور است.",
        source_ref=f"procurement.purchase:{purchase.id}",
    )


@transaction.atomic
def cancel_purchase(purchase: Purchase, *, actor=None) -> Purchase:
    """Cancel a purchase; reverse its financial effect if it was registered."""
    locked = Purchase.objects.select_for_update().get(pk=purchase.pk)
    if locked.status == Purchase.Status.REGISTERED:
        from apps.accounting.models import JournalEntry

        origin = JournalEntry.objects.filter(
            source_ref=f"procurement.purchase:{locked.id}", is_reversal=False
        ).first()
        if origin and not origin.reversed_by.exists():
            acc.reverse_entry(origin, actor=actor,
                              description=f"ابطال خرید {locked.number}")
    locked.status = Purchase.Status.CANCELLED
    locked.save(update_fields=["status", "updated_at"])
    log_action(actor, "procurement.cancel_purchase", f"procurement.purchase:{locked.id}")
    return locked
