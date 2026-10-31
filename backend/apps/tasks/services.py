"""Task service layer: every state change goes through here.

Each mutation is atomic, logged to ``AuditLog`` and recorded on the task
timeline. Notifications (dashboard + Bale) are sent after commit and can
never make a task write fail.
"""
from __future__ import annotations

import logging
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from apps.core.models import Item, Notification, Party
from apps.core.services import log_action, notify

from . import bale, parsing
from .models import Task, TaskEvent

log = logging.getLogger(__name__)

REMIND_AFTER = timedelta(hours=24)

PROFORMA_ITEM_NAME = {
    Task.Kind.FAULT: "رفع خرابی",
    Task.Kind.SUPPORT: "خدمات پشتیبانی",
    Task.Kind.PROJECT: "اجرای پروژه",
    Task.Kind.INSTALL: "نصب و راه‌اندازی",
}


class TaskError(Exception):
    """A user-facing error (message is shown as-is)."""


# --- Who is who -----------------------------------------------------------------
def is_management(user) -> bool:
    return bool(user and (user.is_system_admin or user.has_perm_code("tasks.view_all")))


def management_users():
    """The people an unassigned task goes to (role «مدیریت»; admins as fallback)."""
    User = get_user_model()
    users = list(User.objects.filter(is_active=True, userrole__role__code="management").distinct())
    if not users:
        users = list(User.objects.filter(is_active=True, is_system_admin=True))
    return users


def visible_tasks(user):
    from django.db.models import Q
    qs = Task.objects.select_related("customer", "assignee", "created_by", "proforma")
    if is_management(user):
        return qs
    return qs.filter(Q(created_by=user) | Q(assignee=user))


def can_act(user, task: Task) -> bool:
    return is_management(user) or user.pk in {task.created_by_id, task.assignee_id}


def can_issue_proforma(user) -> bool:
    return bool(user and (user.has_perm_code("sales.edit") or user.has_perm_code("technical.edit")))


# --- Notifications (after commit, best-effort) ----------------------------------------
def _recipients(task: Task):
    return [task.assignee] if task.assignee_id else management_users()


def _send(users, task: Task, headline: str, buttons: bool = True) -> None:
    """Dashboard + Bale for each user. Runs after commit; never raises."""
    def run():
        for user in users:
            if not user:
                continue
            try:
                notify(user, Notification.Kind.TASK, f"{headline} — {task.number}: {task.text[:120]}",
                       source_ref=f"tasks.task:{task.pk}")
                bale.queue_for_user(user, bale.task_card(task, headline),
                                        bale.task_buttons(task) if buttons else None)
            except Exception:  # noqa: BLE001 — notifications must not break anything
                log.exception("task notification failed")
    transaction.on_commit(run)


def _event(task: Task, actor, kind: str, text: str = "") -> None:
    TaskEvent.objects.create(task=task, actor=actor, kind=kind, text=text)


def _touch(task: Task, *fields: str) -> None:
    task.last_activity_at = timezone.now()
    task.reminded_at = None
    task.save(update_fields=[*fields, "last_activity_at", "reminded_at", "updated_at"])


# --- Commands ---------------------------------------------------------------------
UNSET = object()


@transaction.atomic
def create_task(*, text: str, actor, customer=UNSET, customer_name: str | None = None,
                kind: str | None = None, assignee=UNSET) -> Task:
    """Create a task from one sentence. Anything not given explicitly is guessed."""
    text = (text or "").strip()
    if not text:
        raise TaskError("متن کار را بنویسید.")
    guess = parsing.parse(text)
    if customer is UNSET:
        customer = guess.customer
    if customer_name is None:
        customer_name = "" if customer else guess.customer_name
    if assignee is UNSET:
        assignee = guess.assignee
    task = Task.objects.create(
        text=text,
        kind=kind or guess.kind,
        customer=customer,
        customer_name=(customer_name or "")[:200] if not customer else "",
        assignee=assignee,
        created_by=actor,
    )
    _event(task, actor, TaskEvent.Kind.CREATED, text)
    log_action(actor, "tasks.create", f"tasks.task:{task.pk}", kind=task.kind,
               assignee=task.assignee_id)
    others = [u for u in _recipients(task) if u.pk != actor.pk]
    _send(others, task, "📥 کار جدید برای شما")
    return task


@transaction.atomic
def assign(task: Task, assignee, *, actor) -> Task:
    task = Task.objects.select_for_update().get(pk=task.pk)
    if not can_act(actor, task):
        raise TaskError("اجازه‌ی ارجاع این کار را ندارید.")
    if task.assignee_id == (assignee.pk if assignee else None):
        return task
    task.assignee = assignee
    _touch(task, "assignee")
    name = assignee.full_name if assignee else "مدیریت"
    _event(task, actor, TaskEvent.Kind.ASSIGNED, f"ارجاع به {name}")
    log_action(actor, "tasks.assign", f"tasks.task:{task.pk}", assignee=task.assignee_id)
    _send([u for u in _recipients(task) if u.pk != actor.pk], task,
          f"📨 {actor.full_name} این کار را به شما ارجاع داد")
    if task.created_by_id not in {actor.pk, task.assignee_id}:
        _send([task.created_by], task, f"↪️ کار شما به {name} ارجاع شد", buttons=False)
    return task


@transaction.atomic
def set_status(task: Task, status: str, *, actor) -> Task:
    task = Task.objects.select_for_update().get(pk=task.pk)
    if status not in Task.Status.values:
        raise TaskError("وضعیت نامعتبر است.")
    if not can_act(actor, task):
        raise TaskError("اجازه‌ی تغییر این کار را ندارید.")
    if task.status == status:
        return task
    task.status = status
    task.done_at = timezone.now() if status == Task.Status.DONE else None
    _touch(task, "status", "done_at")
    _event(task, actor, TaskEvent.Kind.STATUS, task.get_status_display())
    log_action(actor, "tasks.status", f"tasks.task:{task.pk}", status=status)
    if task.created_by_id != actor.pk:
        icon = "✅" if status == Task.Status.DONE else "▶️"
        _send([task.created_by], task,
              f"{icon} {actor.full_name}: {task.get_status_display()}", buttons=False)
    return task


@transaction.atomic
def add_note(task: Task, text: str, *, actor) -> Task:
    text = (text or "").strip()
    if not text:
        raise TaskError("متن یادداشت خالی است.")
    task = Task.objects.select_for_update().get(pk=task.pk)
    if not can_act(actor, task):
        raise TaskError("اجازه‌ی یادداشت روی این کار را ندارید.")
    _touch(task)
    _event(task, actor, TaskEvent.Kind.NOTE, text)
    log_action(actor, "tasks.note", f"tasks.task:{task.pk}")
    others = {u.pk: u for u in [task.created_by, *_recipients(task)] if u.pk != actor.pk}
    _send(list(others.values()), task, f"💬 {actor.full_name}: {text[:200]}", buttons=False)
    return task


@transaction.atomic
def set_customer(task: Task, *, actor, customer: Party | None = None,
                 customer_name: str = "", create: bool = False) -> Task:
    """Link a customer; ``create=True`` adds ``customer_name`` to the party list."""
    task = Task.objects.select_for_update().get(pk=task.pk)
    if not can_act(actor, task):
        raise TaskError("اجازه‌ی ویرایش این کار را ندارید.")
    if create:
        name = (customer_name or task.customer_name).strip()
        if not name:
            raise TaskError("نام مشتری را بنویسید.")
        customer = Party.objects.filter(name=name).first() or Party.objects.create(
            name=name, is_customer=True)
        log_action(actor, "core.party_create", f"core.party:{customer.pk}", via="tasks")
    task.customer = customer
    task.customer_name = "" if customer else customer_name.strip()[:200]
    _touch(task, "customer", "customer_name")
    log_action(actor, "tasks.customer", f"tasks.task:{task.pk}", customer=task.customer_id)
    return task


@transaction.atomic
def set_kind(task: Task, kind: str, *, actor) -> Task:
    if kind not in Task.Kind.values:
        raise TaskError("نوع کار نامعتبر است.")
    task = Task.objects.select_for_update().get(pk=task.pk)
    if not can_act(actor, task):
        raise TaskError("اجازه‌ی ویرایش این کار را ندارید.")
    task.kind = kind
    _touch(task, "kind")
    log_action(actor, "tasks.kind", f"tasks.task:{task.pk}", kind=kind)
    return task


@transaction.atomic
def issue_proforma(task: Task, *, actor):
    """One click: a draft service proforma pre-filled from the task."""
    from apps.sales.models import Proforma, ProformaLine

    task = Task.objects.select_for_update().get(pk=task.pk)
    if not can_act(actor, task):
        raise TaskError("اجازه‌ی این کار را ندارید.")
    if not can_issue_proforma(actor):
        raise TaskError("صدور پیش‌فاکتور فقط برای بخش فروش، فنی یا مدیریت مجاز است.")
    if task.proforma_id:
        return task.proforma
    if not task.customer_id:
        if not task.customer_name:
            raise TaskError("اول مشتری این کار را مشخص کنید.")
        task.customer = Party.objects.filter(name=task.customer_name).first() or \
            Party.objects.create(name=task.customer_name, is_customer=True)
        task.customer_name = ""
    item, _ = Item.objects.get_or_create(
        name=PROFORMA_ITEM_NAME[task.kind], kind=Item.Kind.SERVICE,
        defaults={"unit": "خدمت"},
    )
    proforma = Proforma.objects.create(customer=task.customer, owner=actor,
                                       notes=f"بر اساس کار {task.number}")
    ProformaLine.objects.create(proforma=proforma, item=item, description=task.text[:255],
                                quantity=1, unit_price=0)
    task.proforma = proforma
    _touch(task, "proforma", "customer", "customer_name")
    _event(task, actor, TaskEvent.Kind.PROFORMA, f"پیش‌فاکتور {proforma.number} صادر شد")
    log_action(actor, "tasks.issue_proforma", f"sales.proforma:{proforma.pk}", task=task.pk)
    return proforma


# --- Background jobs ----------------------------------------------------------------------
def send_reminders(now=None) -> int:
    """Remind about tasks nobody has touched for 24h (once per 24h)."""
    from django.db.models import Q
    now = now or timezone.now()
    cutoff = now - REMIND_AFTER
    stale = Task.objects.select_related("assignee", "created_by", "customer") \
        .exclude(status=Task.Status.DONE).filter(last_activity_at__lte=cutoff) \
        .filter(Q(reminded_at__isnull=True) | Q(reminded_at__lte=cutoff))
    count = 0
    for task in stale:
        with transaction.atomic():
            Task.objects.filter(pk=task.pk).update(reminded_at=now)
            _send(_recipients(task), task, "⏰ یادآوری: این کار ۲۴ ساعت است دست نخورده")
        count += 1
    return count
