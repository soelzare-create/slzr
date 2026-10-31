"""Telegram bot: delivery (outbox + retry) and handling of incoming updates.

Works with either a webhook (``/api/telegram/webhook``) or long polling
(``manage.py telegram_poll``). Uses only the standard library.

Settings (env):
  TELEGRAM_BOT_TOKEN       bot token from @BotFather (empty = Telegram disabled)
  TELEGRAM_BOT_USERNAME    bot username without @, for the "connect" link
  TELEGRAM_API_BASE        default https://api.telegram.org (or a relay)
  TELEGRAM_PROXY           optional http(s) proxy for reaching Telegram
  TELEGRAM_WEBHOOK_SECRET  secret header Telegram sends with webhook calls
"""
from __future__ import annotations

import json
import logging
import threading
import urllib.error
import urllib.request

from django.conf import settings
from django.db import close_old_connections, transaction
from django.utils import timezone

from .models import Task, TelegramLink, TelegramMessage

log = logging.getLogger(__name__)

MAX_ATTEMPTS = 10
STATUS_ICON = {Task.Status.OPEN: "🟡", Task.Status.IN_PROGRESS: "🔵", Task.Status.DONE: "🟢"}
KIND_ICON = {Task.Kind.FAULT: "🔧", Task.Kind.SUPPORT: "🛟", Task.Kind.PROJECT: "📐",
             Task.Kind.INSTALL: "🧰"}


class TelegramError(Exception):
    pass


def enabled() -> bool:
    return bool(settings.TELEGRAM_BOT_TOKEN)


# --- Low-level API ------------------------------------------------------------
def api_call(method: str, payload: dict | None = None, timeout: int = 10) -> dict:
    url = f"{settings.TELEGRAM_API_BASE.rstrip('/')}/bot{settings.TELEGRAM_BOT_TOKEN}/{method}"
    data = json.dumps(payload or {}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    handlers = []
    if settings.TELEGRAM_PROXY:
        handlers.append(urllib.request.ProxyHandler(
            {"http": settings.TELEGRAM_PROXY, "https": settings.TELEGRAM_PROXY}))
    opener = urllib.request.build_opener(*handlers)
    try:
        with opener.open(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            body = json.loads(exc.read().decode("utf-8"))
        except Exception:  # noqa: BLE001
            raise TelegramError(f"HTTP {exc.code}") from exc
    except Exception as exc:  # noqa: BLE001 — network errors of every flavour
        raise TelegramError(str(exc)) from exc
    if not body.get("ok"):
        raise TelegramError(body.get("description") or "unknown error")
    return body.get("result") or {}


# --- Outbox -------------------------------------------------------------------
def queue(chat_id: int, text: str, reply_markup: dict | None = None) -> TelegramMessage | None:
    """Queue a message and try to deliver it right after the transaction commits."""
    if not enabled():
        return None
    msg = TelegramMessage.objects.create(chat_id=chat_id, text=text, reply_markup=reply_markup)
    transaction.on_commit(lambda: _deliver_soon(msg.pk))
    return msg


def queue_for_user(user, text: str, reply_markup: dict | None = None):
    link = TelegramLink.objects.filter(user=user).first() if user else None
    if link:
        return queue(link.chat_id, text, reply_markup)
    return None


def _deliver_soon(pk: int) -> None:
    if getattr(settings, "TELEGRAM_SEND_ASYNC", True):
        def run():
            try:
                deliver(pk)
            finally:
                close_old_connections()
        threading.Thread(target=run, daemon=True).start()
    else:
        deliver(pk)


def deliver(pk: int) -> bool:
    msg = TelegramMessage.objects.filter(pk=pk, status=TelegramMessage.Status.PENDING).first()
    if not msg:
        return False
    payload = {"chat_id": msg.chat_id, "text": msg.text}
    if msg.reply_markup:
        payload["reply_markup"] = msg.reply_markup
    msg.attempts += 1
    try:
        api_call("sendMessage", payload)
    except TelegramError as exc:
        msg.last_error = str(exc)[:500]
        if msg.attempts >= MAX_ATTEMPTS:
            msg.status = TelegramMessage.Status.FAILED
        msg.save(update_fields=["attempts", "last_error", "status", "updated_at"])
        log.warning("telegram send failed (%s): %s", msg.pk, exc)
        return False
    msg.status = TelegramMessage.Status.SENT
    msg.sent_at = timezone.now()
    msg.save(update_fields=["attempts", "status", "sent_at", "updated_at"])
    return True


def deliver_pending() -> int:
    if not enabled():
        return 0
    ids = TelegramMessage.objects.filter(status=TelegramMessage.Status.PENDING) \
        .values_list("id", flat=True)[:100]
    return sum(1 for pk in list(ids) if deliver(pk))


# --- Message rendering ----------------------------------------------------------
def task_card(task: Task, headline: str = "") -> str:
    lines = []
    if headline:
        lines.append(headline)
    lines.append(f"{KIND_ICON.get(task.kind, '📌')} {task.number} · {task.get_kind_display()}")
    if task.customer_display:
        lines.append(f"مشتری: {task.customer_display}")
    lines.append(f"«{task.text}»")
    lines.append(f"ثبت: {task.created_by.full_name}")
    lines.append(f"مسئول: {task.assignee.full_name if task.assignee_id else 'مدیریت'}")
    lines.append(f"وضعیت: {STATUS_ICON.get(task.status, '')} {task.get_status_display()}")
    return "\n".join(lines)


def task_buttons(task: Task) -> dict | None:
    row = []
    if task.status == Task.Status.OPEN:
        row.append({"text": "▶️ شروع کردم", "callback_data": f"task:{task.pk}:start"})
    if task.status != Task.Status.DONE:
        row.append({"text": "✅ انجام شد", "callback_data": f"task:{task.pk}:done"})
    return {"inline_keyboard": [row]} if row else None


# --- Incoming updates -----------------------------------------------------------
def normalize_phone(raw: str) -> list[str]:
    digits = "".join(ch for ch in str(raw) if ch.isdigit())
    if digits.startswith("0098"):
        digits = digits[4:]
    elif digits.startswith("98") and len(digits) == 12:
        digits = digits[2:]
    if digits.startswith("0"):
        digits = digits[1:]
    return [f"0{digits}", digits, f"+98{digits}", f"98{digits}"]


def _reply(chat_id: int, text: str, reply_markup: dict | None = None) -> None:
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        api_call("sendMessage", payload)
    except TelegramError as exc:
        log.warning("telegram reply failed: %s", exc)


ASK_CONTACT = {
    "keyboard": [[{"text": "📱 اشتراک شماره موبایل", "request_contact": True}]],
    "resize_keyboard": True, "one_time_keyboard": True,
}
MAIN_KEYBOARD = {"keyboard": [[{"text": "کارهای من"}]], "resize_keyboard": True}


def handle_update(update: dict) -> None:
    if "callback_query" in update:
        _handle_callback(update["callback_query"])
    elif "message" in update:
        _handle_message(update["message"])


def _handle_message(message: dict) -> None:
    chat_id = message.get("chat", {}).get("id")
    if not chat_id or message.get("chat", {}).get("type") != "private":
        return
    sender = message.get("from", {})
    link = TelegramLink.objects.select_related("user").filter(chat_id=chat_id).first()

    contact = message.get("contact")
    if contact:
        if contact.get("user_id") != sender.get("id"):
            _reply(chat_id, "لطفاً شماره‌ی خودتان را با دکمه‌ی زیر بفرستید.", ASK_CONTACT)
            return
        _link_by_phone(chat_id, sender, contact.get("phone_number", ""))
        return

    if not link:
        _reply(chat_id, "سلام! برای وصل شدن به سیستم کارهای داران ایکس، شماره‌ی موبایلتان "
                        "را با دکمه‌ی زیر بفرستید.", ASK_CONTACT)
        return

    text = (message.get("text") or "").strip()
    if text in {"کارهای من", "/tasks"}:
        _send_my_tasks(chat_id, link.user)
    else:
        _reply(chat_id, f"{link.user.full_name} عزیز، اکانت شما وصل است ✓\n"
                        "کارهای جدید همین‌جا برایتان می‌آید.", MAIN_KEYBOARD)


def _link_by_phone(chat_id: int, sender: dict, phone: str) -> None:
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.filter(phone__in=normalize_phone(phone), is_active=True).first()
    if not user:
        _reply(chat_id, "این شماره در سیستم داران ایکس ثبت نشده است. با مدیر سیستم تماس بگیرید.",
               {"remove_keyboard": True})
        return
    TelegramLink.objects.filter(chat_id=chat_id).exclude(user=user).delete()
    TelegramLink.objects.update_or_create(
        user=user, defaults={"chat_id": chat_id, "username": sender.get("username") or ""})
    _reply(chat_id, f"✅ {user.full_name} عزیز، اکانت شما وصل شد.\n"
                    "از این به بعد کارهایی که به شما ارجاع می‌شود همین‌جا می‌آید.", MAIN_KEYBOARD)


def _send_my_tasks(chat_id: int, user) -> None:
    tasks = list(Task.objects.select_related("customer", "assignee", "created_by")
                 .filter(assignee=user).exclude(status=Task.Status.DONE)[:10])
    if not tasks:
        _reply(chat_id, "کار بازی ندارید 🎉", MAIN_KEYBOARD)
        return
    for task in tasks:
        _reply(chat_id, task_card(task), task_buttons(task))


def _handle_callback(cq: dict) -> None:
    from . import services

    cq_id = cq.get("id")
    chat_id = (cq.get("message") or {}).get("chat", {}).get("id")
    message_id = (cq.get("message") or {}).get("message_id")
    link = TelegramLink.objects.select_related("user").filter(chat_id=chat_id).first()

    def answer(text: str) -> None:
        try:
            api_call("answerCallbackQuery", {"callback_query_id": cq_id, "text": text})
        except TelegramError:
            pass

    if not link:
        answer("اکانت شما وصل نیست.")
        return
    try:
        _, task_id, action = (cq.get("data") or "").split(":")
        task = Task.objects.get(pk=int(task_id))
    except (ValueError, Task.DoesNotExist):
        answer("کار پیدا نشد.")
        return

    status = {"start": Task.Status.IN_PROGRESS, "done": Task.Status.DONE}.get(action)
    if not status:
        answer("دستور نامعتبر.")
        return
    try:
        task = services.set_status(task, status, actor=link.user)
    except services.TaskError as exc:
        answer(str(exc))
        return
    answer("ثبت شد ✓")
    payload = {"chat_id": chat_id, "message_id": message_id, "text": task_card(task)}
    markup = task_buttons(task)
    if markup:
        payload["reply_markup"] = markup
    try:
        api_call("editMessageText", payload)
    except TelegramError:
        pass
