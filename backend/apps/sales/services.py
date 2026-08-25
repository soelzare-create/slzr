"""Sales service layer (Sections 5 & 6): the core financial workflow.

Everything that mutates a proforma's state or money goes through here, inside
``transaction.atomic`` with ``select_for_update`` row locking on the contended
resource. The 5% rule is enforced at invoice time and cannot be bypassed.
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.accounting import services as acc
from apps.accounting.services import Line
from apps.core.models import Notification
from apps.core.services import log_action, notify
from apps.procurement.models import Purchase

from .models import Invoice, InvoiceLine, Proforma, ProformaLine, ProformaStatus


class FivePercentViolation(Exception):
    """Raised when a sale line breaks the ≥ purchase×1.05 rule (Section 6)."""


class InvalidTransition(Exception):
    """Raised on an illegal proforma state transition."""


# --- Numbering --------------------------------------------------------------
def _next_proforma_number() -> str:
    last = Proforma.objects.order_by("-id").first()
    return f"PF-{((last.id + 1) if last else 1):05d}"


def _next_invoice_number() -> str:
    last = Invoice.objects.order_by("-id").first()
    return f"IN-{((last.id + 1) if last else 1):05d}"


# --- State machine ----------------------------------------------------------
@transaction.atomic
def confirm_proforma(proforma: Proforma, *, actor=None) -> Proforma:
    """DRAFT → CONFIRMED. Starts the 48h soft reservation (Section 5)."""
    p = Proforma.objects.select_for_update().get(pk=proforma.pk)
    if p.status != ProformaStatus.DRAFT:
        raise InvalidTransition("فقط پیش‌فاکتور در وضعیت پیش‌نویس قابل تأیید است.")
    now = timezone.now()
    p.status = ProformaStatus.CONFIRMED
    p.confirmed_at = now
    p.reservation_expires_at = now + timedelta(hours=settings.SOFT_RESERVATION_HOURS)
    if not p.number:
        p.number = _next_proforma_number()
    p.save(update_fields=["status", "confirmed_at", "reservation_expires_at",
                          "number", "updated_at"])
    log_action(actor, "sales.confirm_proforma", f"sales.proforma:{p.id}")
    return p


@transaction.atomic
def request_purchase(proforma: Proforma, *, actor=None, procurement_manager=None) -> Proforma:
    """Goods unavailable → AWAITING_PURCHASE + purchase request to procurement."""
    p = Proforma.objects.select_for_update().get(pk=proforma.pk)
    if p.status not in {ProformaStatus.DRAFT, ProformaStatus.CONFIRMED}:
        raise InvalidTransition("درخواست خرید فقط از پیش‌نویس/تأییدشده ممکن است.")
    p.status = ProformaStatus.AWAITING_PURCHASE
    p.save(update_fields=["status", "updated_at"])
    log_action(actor, "sales.request_purchase", f"sales.proforma:{p.id}")
    if procurement_manager is not None:
        notify(
            recipient=procurement_manager,
            kind=Notification.Kind.PURCHASE_REQUEST,
            message=f"درخواست خرید برای پیش‌فاکتور {p.number} ثبت شد.",
            source_ref=f"sales.proforma:{p.id}",
        )
    return p


@transaction.atomic
def mark_ready(proforma: Proforma, *, actor=None) -> Proforma:
    """AWAITING_PURCHASE → READY (goods registered by procurement)."""
    p = Proforma.objects.select_for_update().get(pk=proforma.pk)
    if p.status != ProformaStatus.AWAITING_PURCHASE:
        raise InvalidTransition("فقط پیش‌فاکتور منتظر خرید آماده فاکتور می‌شود.")
    p.status = ProformaStatus.READY
    p.save(update_fields=["status", "updated_at"])
    log_action(actor, "sales.mark_ready", f"sales.proforma:{p.id}")
    notify(
        recipient=p.owner,
        kind=Notification.Kind.READY_TO_INVOICE,
        message=f"کالای پیش‌فاکتور شماره {p.number} آماده فاکتور است.",
        source_ref=f"sales.proforma:{p.id}",
    )
    return p


@transaction.atomic
def mark_unfulfillable(proforma: Proforma, *, actor=None) -> Proforma:
    """Procurement cannot supply → UNFULFILLABLE; sales decides on cancel."""
    p = Proforma.objects.select_for_update().get(pk=proforma.pk)
    p.status = ProformaStatus.UNFULFILLABLE
    p.save(update_fields=["status", "updated_at"])
    log_action(actor, "sales.mark_unfulfillable", f"sales.proforma:{p.id}")
    notify(
        recipient=p.owner,
        kind=Notification.Kind.UNFULFILLABLE,
        message=f"پیش‌فاکتور {p.number} تأمین‌نشدنی اعلام شد.",
        source_ref=f"sales.proforma:{p.id}",
    )
    return p


@transaction.atomic
def cancel_proforma(proforma: Proforma, *, actor=None, manager_approved: bool = False) -> Proforma:
    """Cancel a proforma. A CONFIRMED one needs manager approval (decision #4)."""
    p = Proforma.objects.select_for_update().get(pk=proforma.pk)
    if p.status == ProformaStatus.INVOICED:
        raise InvalidTransition("پیش‌فاکتور فاکتورشده را نمی‌توان ابطال کرد.")
    if p.status == ProformaStatus.CONFIRMED and not manager_approved:
        raise InvalidTransition("ابطال پیش‌فاکتور تأییدشده نیاز به تأیید مدیر دارد.")
    p.status = ProformaStatus.CANCELLED
    p.confirmed_at = None
    p.reservation_expires_at = None  # release reservation
    p.save(update_fields=["status", "confirmed_at", "reservation_expires_at", "updated_at"])
    log_action(actor, "sales.cancel_proforma", f"sales.proforma:{p.id}",
               manager_approved=manager_approved)
    return p


# --- 5% rule ----------------------------------------------------------------
def check_five_percent(lines) -> None:
    """Raise if any goods line breaks sale ≥ purchase × 1.05 (Section 6).

    Applied per line, never on the invoice total, and cannot be bypassed.
    """
    mult = Decimal(str(settings.MIN_MARGIN_MULTIPLIER))
    for line in lines:
        src = line.source_purchase_line
        if src is None:
            raise FivePercentViolation(
                "هر قلم کالا باید به یک خرید مبدأ وصل باشد."
            )
        floor = Decimal(src.unit_price) * mult
        if Decimal(line.unit_price) < floor:
            raise FivePercentViolation(
                f"قیمت فروش قلم «{line.item}» ({line.unit_price}) کمتر از حداقل مجاز "
                f"({floor:.0f} = خرید × {mult}) است."
            )


# --- Convert to invoice -----------------------------------------------------
@transaction.atomic
def convert_to_invoice(proforma: Proforma, *, actor=None) -> Invoice:
    """READY/CONFIRMED proforma → goods Invoice, enforcing the 5% rule.

    Prerequisite (Section 6): each line's purchase must be registered. Posts the
    sale financial effect (AR ⇑ / sales income ⇑, and COGS ⇑ / inventory ⇓).
    """
    p = Proforma.objects.select_for_update().get(pk=proforma.pk)
    if p.status in {ProformaStatus.INVOICED, ProformaStatus.CANCELLED,
                    ProformaStatus.UNFULFILLABLE}:
        raise InvalidTransition("این پیش‌فاکتور قابل تبدیل به فاکتور نیست.")

    lines = list(p.lines.select_related("source_purchase_line", "item").all())
    if not lines:
        raise InvalidTransition("پیش‌فاکتور بدون قلم قابل فاکتور شدن نیست.")

    # Prerequisite: every source purchase must be registered (Section 6).
    for line in lines:
        src = line.source_purchase_line
        if src is None or src.purchase.status != Purchase.Status.REGISTERED:
            raise InvalidTransition(
                f"قلم «{line.item}» به خرید ثبت‌شده وصل نیست؛ ابتدا خرید را ثبت کنید."
            )

    # 5% rule — non-bypassable, at the moment of final registration.
    check_five_percent(lines)

    invoice = Invoice.objects.create(
        number=_next_invoice_number(),
        type=Invoice.Type.GOODS,
        customer=p.customer,
        owner=p.owner,
        proforma=p,
        date=date.today(),
    )
    cost_total = Decimal("0")
    for line in lines:
        InvoiceLine.objects.create(
            invoice=invoice,
            item=line.item,
            description=line.description,
            quantity=line.quantity,
            unit_price=line.unit_price,
            source_purchase_line=line.source_purchase_line,
        )
        cost_total += Decimal(line.source_purchase_line.unit_price) * Decimal(line.quantity)

    sale_total = invoice.total
    _post_sale_entry(invoice, sale_total=sale_total, cost_total=cost_total,
                     income_code=acc.SALES_INCOME, actor=actor)

    p.status = ProformaStatus.INVOICED
    p.save(update_fields=["status", "updated_at"])
    log_action(actor, "sales.convert_to_invoice",
               f"sales.invoice:{invoice.id}", proforma=p.id)
    return invoice


def _post_sale_entry(invoice: Invoice, *, sale_total: Decimal, cost_total: Decimal,
                     income_code: str, actor=None) -> None:
    """Post the automatic sale document(s). Called for goods/service/support."""
    lines = [
        Line(acc.ACCOUNTS_RECEIVABLE, debit=sale_total, party=invoice.customer,
             description=f"فاکتور {invoice.number}"),
        Line(income_code, credit=sale_total, description="درآمد فروش"),
    ]
    if cost_total > 0:
        # Recognise cost of goods sold and relieve inventory.
        lines += [
            Line(acc.COGS, debit=cost_total, description="بهای تمام‌شده"),
            Line(acc.INVENTORY, credit=cost_total, description="خروج موجودی"),
        ]
    acc.post_entry(
        description=f"فروش — فاکتور {invoice.number}",
        source_ref=f"sales.invoice:{invoice.id}",
        actor=actor,
        lines=lines,
    )


# --- Direct invoices (service / support), used by the technical app ---------
@transaction.atomic
def create_direct_invoice(*, invoice_type: str, customer, owner, lines_data: list[dict],
                          actor=None, period_start=None, period_end=None,
                          notes: str = "") -> Invoice:
    """Create a service or monthly-support invoice (no proforma, no 5% rule)."""
    income_code = (acc.SUPPORT_INCOME if invoice_type == Invoice.Type.SUPPORT
                   else acc.SERVICE_INCOME)
    invoice = Invoice.objects.create(
        number=_next_invoice_number(),
        type=invoice_type,
        customer=customer,
        owner=owner,
        date=date.today(),
        period_start=period_start,
        period_end=period_end,
        notes=notes,
    )
    for ld in lines_data:
        InvoiceLine.objects.create(
            invoice=invoice,
            item_id=ld["item"],
            description=ld.get("description", ""),
            quantity=ld.get("quantity", 1),
            unit_price=ld.get("unit_price", 0),
        )
    _post_sale_entry(invoice, sale_total=invoice.total, cost_total=Decimal("0"),
                     income_code=income_code, actor=actor)
    log_action(actor, "sales.create_direct_invoice", f"sales.invoice:{invoice.id}",
               type=invoice_type)
    return invoice


# --- Returns / cancel (reverse) ---------------------------------------------
@transaction.atomic
def reverse_invoice(invoice: Invoice, *, actor=None, returned: bool = False) -> Invoice:
    """Cancel/return an invoice → reverse its sale document (Section 5)."""
    from apps.accounting.models import JournalEntry

    inv = Invoice.objects.select_for_update().get(pk=invoice.pk)
    origin = JournalEntry.objects.filter(
        source_ref=f"sales.invoice:{inv.id}", is_reversal=False
    ).first()
    if origin and not origin.reversed_by.exists():
        acc.reverse_entry(origin, actor=actor,
                          description=f"برگشت فروش فاکتور {inv.number}")
    inv.status = Invoice.Status.RETURNED if returned else Invoice.Status.CANCELLED
    inv.save(update_fields=["status", "updated_at"])
    log_action(actor, "sales.reverse_invoice", f"sales.invoice:{inv.id}", returned=returned)
    return inv


# --- Scheduled job: release expired 48h reservations ------------------------
def release_expired_reservations(*, actor=None) -> int:
    """Release CONFIRMED proformas whose 48h reservation elapsed (Section 5/6).

    Run from a management command via cron / Celery beat. Returns the count.
    """
    now = timezone.now()
    expired = Proforma.objects.filter(
        status=ProformaStatus.CONFIRMED, reservation_expires_at__lt=now
    )
    count = 0
    for proforma in expired:
        with transaction.atomic():
            p = Proforma.objects.select_for_update().get(pk=proforma.pk)
            if p.status != ProformaStatus.CONFIRMED or p.reservation_expires_at >= now:
                continue
            p.status = ProformaStatus.DRAFT
            p.confirmed_at = None
            p.reservation_expires_at = None
            p.save(update_fields=["status", "confirmed_at", "reservation_expires_at",
                                  "updated_at"])
            notify(
                recipient=p.owner,
                kind=Notification.Kind.RESERVATION_RELEASED,
                message=f"رزرو پیش‌فاکتور {p.number} پس از ۴۸ ساعت آزاد شد.",
                source_ref=f"sales.proforma:{p.id}",
            )
            log_action(actor, "sales.release_reservation", f"sales.proforma:{p.id}")
            count += 1
    return count
