"""Accounts: custom User + database-driven permission-matrix RBAC (Section 3).

The access matrix is data, not hard-coded:

    System        — a department (sales, accounting, procurement, technical, ...).
    Permission    — an atomic permission (system + action), e.g. ``sales.view``.
    Role          — manager/employee per department + management + system admin.
    RolePermission— M2M role↔permission. The heart of the matrix.
    UserRole      — binds a user to a role (+ department).

Adding a department or changing access = a row in RolePermission, no code change.
"""
from __future__ import annotations

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

from apps.core.models import TimeStampedModel


class System(TimeStampedModel):
    """A department / sub-system in the access matrix."""

    code = models.SlugField(max_length=40, unique=True)  # e.g. "sales"
    name = models.CharField(max_length=100)  # e.g. "فروش"

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return self.name


class Permission(TimeStampedModel):
    """An atomic permission: ``<system>.<action>`` (e.g. ``sales.view_all``)."""

    system = models.ForeignKey(System, on_delete=models.CASCADE, related_name="permissions")
    action = models.CharField(max_length=40)  # view, edit, view_all, assign, ...
    code = models.CharField(max_length=80, unique=True)  # denormalised "sales.view"
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["code"]
        unique_together = ["system", "action"]

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = f"{self.system.code}.{self.action}"
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.code


class Role(TimeStampedModel):
    """A role: manager/employee of a department, management, or system admin."""

    code = models.SlugField(max_length=60, unique=True)  # e.g. "sales_manager"
    name = models.CharField(max_length=100)
    system = models.ForeignKey(
        System, null=True, blank=True, on_delete=models.CASCADE, related_name="roles"
    )
    is_manager = models.BooleanField(default=False)
    permissions = models.ManyToManyField(
        Permission, through="RolePermission", related_name="roles"
    )

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return self.name


class RolePermission(TimeStampedModel):
    """The M2M join at the heart of the matrix — all access is read from here."""

    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        unique_together = ["role", "permission"]

    def __str__(self) -> str:
        return f"{self.role.code} → {self.permission.code}"


class UserManager(BaseUserManager):
    def create_user(self, phone: str, password: str | None = None, **extra):
        if not phone:
            raise ValueError("شماره تماس الزامی است")
        user = self.model(phone=phone, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone: str, password: str, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("is_system_admin", True)
        return self.create_user(phone, password, **extra)


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    """User authenticated by phone number (Section 8)."""

    phone = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # Django admin access
    # System admin — separate from the management department (Section 3, decision #8).
    is_system_admin = models.BooleanField(default=False)

    roles = models.ManyToManyField(Role, through="UserRole", related_name="users")

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        ordering = ["full_name"]

    def __str__(self) -> str:
        return f"{self.full_name} ({self.phone})"

    # --- RBAC helpers -------------------------------------------------------
    def permission_codes(self) -> set[str]:
        """All permission codes granted through this user's roles."""
        if self.is_system_admin:
            return {"*"}
        return set(
            Permission.objects.filter(roles__userrole__user=self)
            .values_list("code", flat=True)
            .distinct()
        )

    def has_perm_code(self, code: str) -> bool:
        codes = self.permission_codes()
        return "*" in codes or code in codes

    def department_codes(self) -> set[str]:
        """Departments this user belongs to (via their roles)."""
        return set(
            System.objects.filter(roles__userrole__user=self)
            .values_list("code", flat=True)
            .distinct()
        )


class UserRole(TimeStampedModel):
    """Binds a user to a role (and, implicitly, a department via the role)."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    class Meta:
        unique_together = ["user", "role"]

    def __str__(self) -> str:
        return f"{self.user.phone} = {self.role.code}"
