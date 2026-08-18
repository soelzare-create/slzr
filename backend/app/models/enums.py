"""Controlled vocabularies used across the data model (per the blueprint)."""
from __future__ import annotations

import enum


class UserRole(str, enum.Enum):
    """نقش کاربر — مدیر، فروش، فنی، انباردار، حسابدار."""

    manager = "manager"          # مدیر
    sales = "sales"              # فروش
    technical = "technical"      # فنی
    warehouse = "warehouse"      # انباردار
    accountant = "accountant"    # حسابدار


class ActivityType(str, enum.Enum):
    """سه نوع فعالیت درآمدزا."""

    project = "project"                    # پروژه
    sale = "sale"                          # فروش کالا
    support_contract = "support_contract"  # قرارداد پشتیبانی


class ActivityStatus(str, enum.Enum):
    """وضعیت جاری فعالیت."""

    open = "open"                # باز
    in_progress = "in_progress"  # در حال انجام
    done = "done"                # انجام‌شده
    cancelled = "cancelled"      # لغوشده


class ProjectStage(str, enum.Enum):
    """مراحل پروژه — شناخت، طراحی، پیش‌فروش، اجرا، پشتیبانی."""

    discovery = "discovery"    # شناخت
    design = "design"          # طراحی
    presale = "presale"        # پیش‌فروش
    execution = "execution"    # اجرا
    support = "support"        # پشتیبانی


class TrackingType(str, enum.Enum):
    """نوع ردیابی کالا — سریال‌دار یا مقداری."""

    serial = "serial"      # سریال‌دار (تک‌کالا)
    quantity = "quantity"  # مقداری / فله‌ای


class UnitItemStatus(str, enum.Enum):
    """وضعیت تک‌کالا — انبار / فروخته / نصب‌شده / خراب."""

    warehouse = "warehouse"  # انبار
    sold = "sold"            # فروخته
    installed = "installed"  # نصب‌شده
    broken = "broken"        # خراب


class MovementDirection(str, enum.Enum):
    """جهت حرکت انبار — ورود یا خروج."""

    in_ = "in"    # ورود
    out = "out"   # خروج


class InvoiceKind(str, enum.Enum):
    """نوع سند فروش — پیش‌فاکتور یا فاکتور نهایی."""

    proforma = "proforma"  # پیش‌فاکتور (سند غیرقطعی، بدون اثر روی انبار/حساب)
    final = "final"        # فاکتور فروش (قطعی؛ کالا خارج و درآمد ثبت می‌شود)


class InvoiceStatus(str, enum.Enum):
    """وضعیت فاکتور — پرداخت‌شده یا معوق."""

    unpaid = "unpaid"    # صادرشده / پرداخت‌نشده
    paid = "paid"        # پرداخت‌شده
    overdue = "overdue"  # معوق


class PurchaseStatus(str, enum.Enum):
    """وضعیت سند خرید — پرداخت‌شده به تأمین‌کننده یا معوق."""

    unpaid = "unpaid"    # ثبت‌شده / پرداخت‌نشده
    paid = "paid"        # پرداخت‌شده
    overdue = "overdue"  # معوق


class FinancialType(str, enum.Enum):
    """نوع سند مالی — دخل یا خرج."""

    income = "income"    # دخل
    expense = "expense"  # خرج


class TicketStatus(str, enum.Enum):
    """وضعیت تیکت — باز، در حال بررسی، بسته."""

    open = "open"                # باز
    investigating = "investigating"  # در حال بررسی
    closed = "closed"            # بسته
