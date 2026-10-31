"""Tasks (کارها): a deliberately tiny work tracker for the whole company.

A customer reports a fault / support need / new project to a colleague; the
colleague types one sentence, the system works out the rest (customer, kind,
assignee) and pushes the task to the assignee on Telegram.
"""
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import NumberedModel, Party, TimeStampedModel


class Task(NumberedModel):
    number_prefix = "T"
    number_pad = 4

    class Kind(models.TextChoices):
        FAULT = "FAULT", "خرابی"
        SUPPORT = "SUPPORT", "پشتیبانی"
        PROJECT = "PROJECT", "پروژه"
        INSTALL = "INSTALL", "نصب و راه‌اندازی"

    class Status(models.TextChoices):
        OPEN = "OPEN", "باز"
        IN_PROGRESS = "IN_PROGRESS", "در حال انجام"
        DONE = "DONE", "انجام‌شده"

    number = models.CharField(max_length=20, unique=True, blank=True)
    text = models.TextField()
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.SUPPORT)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN,
                              db_index=True)
    customer = models.ForeignKey(Party, null=True, blank=True, on_delete=models.SET_NULL,
                                 related_name="tasks")
    # Free-text customer name when the customer is not (yet) in the party list.
    customer_name = models.CharField(max_length=200, blank=True)
    # Null assignee = the task sits with management (all management users).
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name="tasks_assigned")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                   related_name="tasks_created")
    proforma = models.OneToOneField("sales.Proforma", null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name="task")
    last_activity_at = models.DateTimeField(default=timezone.now)
    reminded_at = models.DateTimeField(null=True, blank=True)
    done_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "کار"
        verbose_name_plural = "کارها"

    def __str__(self) -> str:
        return self.number or f"کار #{self.pk}"

    @property
    def customer_display(self) -> str:
        return self.customer.name if self.customer_id else self.customer_name


class TaskEvent(TimeStampedModel):
    """Timeline of a task: created, assigned, status changes, notes."""

    class Kind(models.TextChoices):
        CREATED = "CREATED", "ثبت"
        ASSIGNED = "ASSIGNED", "ارجاع"
        STATUS = "STATUS", "تغییر وضعیت"
        NOTE = "NOTE", "یادداشت"
        PROFORMA = "PROFORMA", "پیش‌فاکتور"

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="events")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                              on_delete=models.SET_NULL, related_name="+")
    kind = models.CharField(max_length=10, choices=Kind.choices)
    text = models.TextField(blank=True)

    class Meta:
        ordering = ["created_at", "id"]


class TelegramLink(TimeStampedModel):
    """A user's Telegram chat, linked once by sharing their phone with the bot."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name="telegram")
    chat_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=64, blank=True)

    def __str__(self) -> str:
        return f"{self.user_id} → {self.chat_id}"


class TelegramMessage(TimeStampedModel):
    """Outbox: Telegram delivery is retried, never on the critical path."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "در صف"
        SENT = "SENT", "ارسال‌شده"
        FAILED = "FAILED", "ناموفق"

    chat_id = models.BigIntegerField()
    text = models.TextField()
    reply_markup = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.PENDING,
                              db_index=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    last_error = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["id"]
