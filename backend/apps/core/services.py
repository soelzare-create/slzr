"""Core service helpers shared across departments.

Business logic lives in the service layer (Section 2), not in views/models.
"""
from __future__ import annotations

from typing import Any

from .models import AuditLog, Notification


def log_action(actor, action: str, target: str = "", **detail: Any) -> AuditLog:
    """Record an audit entry. Every state change must be logged (Section 2/5)."""
    return AuditLog.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        action=action,
        target=target,
        detail=detail,
    )


def notify(recipient, kind: str, message: str, source_ref: str = "") -> Notification:
    """Create a dashboard notification (best-effort, off the critical path)."""
    return Notification.objects.create(
        recipient=recipient,
        kind=kind,
        message=message,
        source_ref=source_ref,
    )
