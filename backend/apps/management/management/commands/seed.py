"""Seed the database: access matrix, roles, admin user, chart of accounts.

Idempotent — safe to run repeatedly. Section 3 (RBAC) + Section 8 (chart of
accounts). Adding a department or changing access is a data change here, not a
code change (decision #14).
"""
from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounting.models import Account
from apps.accounts.models import (
    Permission, Role, RolePermission, System, User, UserRole,
)

# Departments (Section 3). Management is a department too but has full access.
DEPARTMENTS = [
    ("sales", "فروش"),
    ("accounting", "حسابداری"),
    ("procurement", "بازرگانی"),
    ("technical", "فنی و پشتیبانی"),
    ("management", "مدیریت"),
]

# Base actions granted per department.
BASE_ACTIONS = ["view", "view_all", "edit"]
EXTRA_ACTIONS = {"procurement": ["assign"]}

# Chart of accounts (Section 8 / accounting.services codes).
ACCOUNTS = [
    ("1000", "دارایی‌ها", "ASSET", None),
    ("1100", "صندوق/بانک", "ASSET", "1000"),
    ("1200", "حساب‌های دریافتنی", "ASSET", "1000"),
    ("1300", "موجودی کالا", "ASSET", "1000"),
    ("2000", "بدهی‌ها", "LIABILITY", None),
    ("2100", "حساب‌های پرداختنی", "LIABILITY", "2000"),
    ("3000", "سرمایه", "EQUITY", None),
    ("4000", "درآمدها", "INCOME", None),
    ("4100", "درآمد فروش کالا", "INCOME", "4000"),
    ("4200", "درآمد خدمات", "INCOME", "4000"),
    ("4300", "درآمد پشتیبانی", "INCOME", "4000"),
    ("5000", "هزینه‌ها", "EXPENSE", None),
    ("5100", "بهای تمام‌شده کالای فروش‌رفته", "EXPENSE", "5000"),
]


class Command(BaseCommand):
    help = "ساخت ماتریس دسترسی، نقش‌ها، کاربر مدیر و کدینگ حساب‌ها"

    @transaction.atomic
    def handle(self, *args, **options):
        systems = self._seed_systems()
        perms = self._seed_permissions(systems)
        self._seed_roles(systems, perms)
        self._seed_admin()
        self._seed_accounts()
        self.stdout.write(self.style.SUCCESS("✓ داده اولیه با موفقیت ساخته شد."))

    # -- matrix -------------------------------------------------------------
    def _seed_systems(self) -> dict[str, System]:
        out = {}
        for code, name in DEPARTMENTS:
            out[code], _ = System.objects.get_or_create(code=code, defaults={"name": name})
        return out

    def _seed_permissions(self, systems) -> dict[str, Permission]:
        out = {}
        for code, system in systems.items():
            actions = BASE_ACTIONS + EXTRA_ACTIONS.get(code, [])
            for action in actions:
                perm, _ = Permission.objects.get_or_create(
                    system=system, action=action,
                    defaults={"code": f"{code}.{action}"},
                )
                out[perm.code] = perm
        return out

    def _seed_roles(self, systems, perms) -> None:
        for code, system in systems.items():
            if code == "management":
                continue
            # Manager: view_all + edit (+ assign for procurement) on own department.
            mgr, _ = Role.objects.get_or_create(
                code=f"{code}_manager",
                defaults={"name": f"مدیر {system.name}", "system": system, "is_manager": True},
            )
            mgr_perms = [f"{code}.view", f"{code}.view_all", f"{code}.edit"]
            if code == "procurement":
                mgr_perms.append("procurement.assign")
            self._grant(mgr, [perms[c] for c in mgr_perms])

            # Employee: view + edit, restricted to own records at object level.
            emp, _ = Role.objects.get_or_create(
                code=f"{code}_employee",
                defaults={"name": f"کارمند {system.name}", "system": system},
            )
            self._grant(emp, [perms[f"{code}.view"], perms[f"{code}.edit"]])

        # Management role: full view_all + edit across every department.
        mgmt, _ = Role.objects.get_or_create(
            code="management", defaults={"name": "مدیریت", "system": systems["management"],
                                         "is_manager": True},
        )
        self._grant(mgmt, list(perms.values()))

        # Accounting cross-department read (Section 3, decision #9): read all invoices.
        acc_role = Role.objects.get(code="accounting_manager")
        self._grant(acc_role, [perms["sales.view_all"], perms["technical.view_all"]])

    def _grant(self, role, permissions) -> None:
        for perm in permissions:
            RolePermission.objects.get_or_create(role=role, permission=perm)

    # -- admin + accounts ---------------------------------------------------
    def _seed_admin(self) -> None:
        if not User.objects.filter(phone=settings.FIRST_ADMIN_PHONE).exists():
            User.objects.create_superuser(
                phone=settings.FIRST_ADMIN_PHONE,
                password=settings.FIRST_ADMIN_PASSWORD,
                full_name=settings.FIRST_ADMIN_NAME,
            )
            self.stdout.write(f"  کاربر مدیر ساخته شد: {settings.FIRST_ADMIN_PHONE}")

    def _seed_accounts(self) -> None:
        for code, name, type_, parent_code in ACCOUNTS:
            parent = Account.objects.filter(code=parent_code).first() if parent_code else None
            Account.objects.get_or_create(
                code=code, defaults={"name": name, "type": type_, "parent": parent},
            )
