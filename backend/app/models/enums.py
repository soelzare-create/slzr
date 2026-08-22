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


class ContactPosition(str, enum.Enum):
    """سمت فردِ رابط در سازمانِ طرف‌حساب — برای ارتباط با هر بخش."""

    ceo = "ceo"                  # مدیرعامل
    procurement = "procurement"  # خرید / بازرگانی
    sales = "sales"              # فروش
    finance = "finance"          # مالی / حسابداری
    technical = "technical"      # فنی / مهندسی
    warehouse = "warehouse"      # انباردار
    staff = "staff"              # کارشناس / کارمند
    other = "other"              # سایر


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
    """وضعیت فاکتور — بر اساس مبلغ دریافت‌شده محاسبه می‌شود."""

    unpaid = "unpaid"    # صادرشده / پرداخت‌نشده
    partial = "partial"  # قسمتی پرداخت‌شده
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


class TaskStatus(str, enum.Enum):
    """وضعیت کارِ ارجاع‌شده — ارجاع‌شده، در حال انجام، انجام‌شده."""

    assigned = "assigned"        # ارجاع‌شده (جدید)
    in_progress = "in_progress"  # در حال انجام
    done = "done"                # انجام‌شده


class PaymentDirection(str, enum.Enum):
    """جهت سند مالی — دریافت (پول ورودی) یا پرداخت (پول خروجی)."""

    receipt = "receipt"  # دریافت
    payment = "payment"  # پرداخت


class PaymentMethod(str, enum.Enum):
    """روش پرداخت/دریافت."""

    cash = "cash"          # نقد
    card = "card"          # کارت‌خوان / کارت‌به‌کارت
    transfer = "transfer"  # حواله / انتقال بانکی
    cheque = "cheque"      # چک


class CashAccountType(str, enum.Enum):
    """نوع حساب مالی — صندوق نقدی یا حساب بانکی."""

    cash = "cash"  # صندوق
    bank = "bank"  # بانک


class ChequeDirection(str, enum.Enum):
    """جهت چک — دریافتی از مشتری یا پرداختی/صادرشده به تأمین‌کننده."""

    received = "received"  # دریافتی
    issued = "issued"      # پرداختی (صادرشده)


class ChequeStatus(str, enum.Enum):
    """وضعیت چک — در جریان، وصول/پاس‌شده، برگشتی."""

    registered = "registered"  # ثبت‌شده / در جریان
    cleared = "cleared"        # وصول‌شده (دریافتی) / پاس‌شده (پرداختی)
    bounced = "bounced"        # برگشتی
