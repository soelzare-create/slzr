"""DRF permission classes + object-level ownership, driven by the RBAC matrix.

Two layers (Section 3):
  Layer 1 — permission codes decide *what actions* a role may do.
  Layer 2 — object-level ownership decides *whose records* an employee sees:
            an employee sees only ``owner=self`` unless they hold ``<system>.view_all``.
"""
from __future__ import annotations

from rest_framework.permissions import BasePermission, SAFE_METHODS


class HasPermissionCode(BasePermission):
    """Grant when the user holds ``required_permission`` (or a per-action code).

    A view sets ``required_permission = "sales.view"`` (blanket), or
    ``required_permissions = {"GET": "sales.view", "POST": "sales.edit"}``.
    System admin (``is_system_admin``) and management (``*``) always pass.
    """

    message = "دسترسی لازم را ندارید."

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not (user and user.is_authenticated):
            return False
        code = self._required_code(request, view)
        if code is None:
            return True
        return user.has_perm_code(code)

    @staticmethod
    def _required_code(request, view) -> str | None:
        per_action = getattr(view, "required_permissions", None)
        if per_action:
            if request.method in SAFE_METHODS:
                return per_action.get("read") or per_action.get("GET")
            return per_action.get("write") or per_action.get(request.method)
        return getattr(view, "required_permission", None)


class OwnershipQuerysetMixin:
    """Filter a queryset to the caller's own records unless they can view all.

    Set ``view_all_permission = "sales.view_all"`` and ``owner_field = "owner"``.
    Managers / management / accounting-read hold ``*.view_all`` and see everything.
    """

    view_all_permission: str | None = None
    owner_field: str = "owner"

    def filter_by_ownership(self, queryset):
        user = self.request.user
        if user.is_system_admin:
            return queryset
        if self.view_all_permission and user.has_perm_code(self.view_all_permission):
            return queryset
        return queryset.filter(**{self.owner_field: user})
