"""Bale (بله) bot: delivery (outbox + retry) and handling of incoming updates.

Bale's bot API mirrors Telegram's (sendMessage, inline keyboards, callback
queries, getUpdates, setWebhook) and is reachable from servers inside Iran.
Works with a webhook (``/api/bale/webhook/<secret>``) or long polling
(``manage.py bale_poll``). Uses only the standard library.

Settings (env):
  BALE_BOT_TOKEN       bot token from @botfather in Bale (empty = Bale disabled)
  BALE_BOT_USERNAME    bot username without @, for the "connect" link
  BALE_API_BASE        default https://tapi.bale.ai
  BALE_WEBHOOK_SECRET  random string, part of the webhook URL
"""
from __future__ import annotations

import json
import logging
import re
import secrets
import threading
import urllib.error
import urllib.request

from django.conf import settings
from django.db import close_old_connections, transaction
from django.utils import timezone

from .models import BaleLink, BaleLinkCode, BaleMessage, Task

log = logging.getLogger(__name__)

MAX_ATTEMPTS = 10
LINK_CODE_TTL_MINUTES = 30
STATUS_ICON = {Task.Status.OPEN: "🟡", Task.Status.IN_PROGRESS: "🔵", Task.Status.DONE: "🟢"}
KIND_ICON = {Task.Kind.FAULT: "🔧", Task.Kind.SUPPORT: "🛟", Task.Kind.PROJECT: "📐",
             Task.Kind.INSTALL: "🧰"}
_DIGITS = str.maketrans({**{c: str(i) for i, c in enumerate("۰۱۲۳۴۵۶۷۸۹")},
                         **{c: str(i) for i, c in enumerate("٠١٢٣٤٥٦٧٨٩")}})


class BaleError(Exception):
    pass


def enabled() -> bool:
    return bool(settings.BALE_BOT_TOKEN)


def bot_url() -> str:
    username = settings.BALE_BOT_USERNAME
    return f"https://ble.ir/{username}" if username else ""


# --- Low-level API ------------------------------------------------------------
def api_call(method: str, payload: dict | None = None, timeout: int = 10) -> dict:
    url = f"{settings.BALE_API_BASE.rstrip('/')}/bot{settings.BALE_BOT_TOKEN}/{method}"
    data = json.dumps(payload or {}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            body = json.loads(exc.read().decode("utf-8"))
        except Exception:  # noqa: BLE001
            raise BaleError(f"HTTP {exc.code}") from exc
    except Exception as exc:  # noqa: BLE001 — network errors of every flavour
        raise BaleError(str(exc)) from exc
    if not body.get("ok"):
        raise BaleError(body.get("description") or "unknown error")
    return body.get("result") or {}


# --- Outbox -------------------------------------------------------------------
def queue(chat_id: int, text: str, reply_markup: dict | None = None) -> BaleMessage | None:
    """Queue a message and try to deliver it right after the transaction commits."""
    if not enabled():
        return None
    msg = BaleMessage.objects.create(chat_id=chat_id, text=text, reply_markup=reply_markup)
    transaction.on_commit(lambda: _deliver_soon(msg.pk))
    return msg


def queue_for_user(user, text: str, reply_markup: dict | None = None):
    link = BaleLink.objects.filter(user=user).first() if user else None
    if link:
        return queue(link.chat_id, text, reply_markup)
    return None


def _deliver_soon(pk: int) -> None:
    if getattr(settings, "BALE_SEND_ASYNC", True):
        def run():
            try:
                deliver(pk)
            finally:
                close_old_connections()
        threading.Thread(target=run, daemon=True).start()
    else:
        deliver(pk)


def deliver(pk: int) -> bool:
    msg = BaleMessage.objects.filter(pk=pk, status=BaleMessage.Status.PENDING).first()
    if not msg:
        return False
    payload = {"chat_id": msg.chat_id, "text": msg.text}
    if msg.reply_markup:
        payload["reply_markup"] = msg.reply_markup
    msg.attempts += 1
    try:
        api_call("sendMessage", payload)
    except BaleError as exc:
        msg.last_error = str(exc)[:500]
        if msg.attempts >= MAX_ATTEMPTS:
            msg.status = BaleMessage.Status.FAILED
        msg.save(update_fields=["attempts", "last_error", "status", "updated_at"])
        log.warning("bale send failed (%s): %s", msg.pk, exc)
        return False
    msg.status = BaleMessage.Status.SENT
    msg.sent_at = timezone.now()
    msg.save(update_fields=["attempts", "status", "sent_at", "updated_at"])
    return True


def deliver_pending() -> int:
    if not enabled():
        return 0
    ids = BaleMessage.objects.filter(status=BaleMessage.Status.PENDING) \
        .values_list("id", flat=True)[:100]
    return sum(1 for pk in list(ids) if deliver(pk))


# --- Linking --------------------------------------------------------------------
def link_code_for(user) -> str:
    """A fresh 6-digit code the user sends to the bot (valid 30 minutes)."""
    existing = BaleLinkCode.objects.filter(user=user).first()
    fresh_after = timezone.now() - timezone.timedelta(minutes=LINK_CODE_TTL_MINUTES - 5)
    if existing and existing.updated_at >= fresh_after:
        return existing.code
    while True:
        code = f"{secrets.randbelow(900000) + 100000}"
        if not BaleLinkCode.objects.filter(code=code).exclude(user=user).exists():
            break
    BaleLinkCode.objects.update_or_create(user=user, defaults={"code": code})
    return code


def _user_for_code(code: str):
    cutoff = timezone.now() - timezone.timedelta(minutes=LINK_CODE_TTL_MINUTES)
    row = BaleLinkCode.objects.select_related("user") \
        .filter(code=code, updated_at__gte=cutoff, user__is_active=True).first()
    if not row:
        return None
    user = row.user
    row.delete()  # single use
    return user


def _link(chat_id: int, sender: dict, user) -> None:
    BaleLink.objects.filter(chat_id=chat_id).exclude(user=user).delete()
    BaleLink.objects.update_or_create(
        user=user, defaults={"chat_id": chat_id, "username": sender.get("username") or ""})
    _reply(chat_id, f"✅ {user.full_name} عزیز، اکانت شما وصل شد.\n"
                    "از این به بعد کارهایی که به شما ارجاع می‌شود همین‌جا می‌آید.", MAIN_KEYBOARD)


def normalize_phone(raw: str) -> list[str]:
    digits = "".join(ch for ch in str(raw).translate(_DIGITS) if ch.isdigit())
    if digits.startswith("0098"):
        digits = digits[4:]
    elif digits.startswith("98") and len(digits) == 12:
        digits = digits[2:]
    if digits.startswith("0"):
        digits = digits[1:]
    return [f"0{digits}", digits, f"+98{digits}", f"98{digits}"]


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
def _reply(chat_id: int, text: str, reply_markup: dict | None = None) -> None:
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        api_call("sendMessage", payload)
    except BaleError as exc:
        log.warning("bale reply failed: %s", exc)


ASK_CONTACT = {
    "keyboard": [[{"text": "📱 اشتراک شماره موبایل", "request_contact": True}]],
    "resize_keyboard": True, "one_time_keyboard": True,
}
MAIN_KEYBOARD = {"keyboard": [[{"text": "کارهای من"}]], "resize_keyboard": True}
WELCOME = ("سلام! برای وصل شدن به سیستم کارهای داران ایکس، کد ۶ رقمی‌ای را که در صفحهٔ «کارها» "
           "نمایش داده شده همین‌جا بفرستید، یا شماره‌ی موبایلتان را با دکمه‌ی زیر به اشتراک بگذارید.")
CODE_RE = re.compile(r"^(?:/start\s+)?(\d{6})$")


def handle_update(update: dict) -> None:
    if "callback_query" in update:
        _handle_callback(update["callback_query"])
    elif "message" in update:
        _handle_message(update["message"])


def _handle_message(message: dict) -> None:
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    if not chat_id or chat.get("type", "private") != "private":
        return
    sender = message.get("from") or {}
    text = (message.get("text") or "").translate(_DIGITS).strip()

    m = CODE_RE.match(text)
    if m:
        user = _user_for_code(m.group(1))
        if user:
            _link(chat_id, sender, user)
        else:
            _reply(chat_id, "این کد معتبر نیست یا منقضی شده. صفحهٔ «کارها» را تازه کنید و "
                            "کد جدید را بفرستید.")
        return

    contact = message.get("contact")
    if contact:
        # Only the sender's own number (shared with the button) is trusted.
        if not contact.get("user_id") or contact.get("user_id") != sender.get("id"):
            _reply(chat_id, "لطفاً به‌جای آن، کد ۶ رقمی صفحهٔ «کارها» را بفرستید.")
            return
        from django.contrib.auth import get_user_model
        user = get_user_model().objects.filter(
            phone__in=normalize_phone(contact.get("phone_number", "")), is_active=True).first()
        if user:
            _link(chat_id, sender, user)
        else:
            _reply(chat_id, "این شماره در سیستم داران ایکس ثبت نشده است. کد ۶ رقمی صفحهٔ «کارها» "
                            "را بفرستید یا با مدیر سیستم تماس بگیرید.", {"remove_keyboard": True})
        return

    link = BaleLink.objects.select_related("user").filter(chat_id=chat_id).first()
    if not link:
        _reply(chat_id, WELCOME, ASK_CONTACT)
        return
    if text in {"کارهای من", "/tasks"}:
        _send_my_tasks(chat_id, link.user)
    else:
        _reply(chat_id, f"{link.user.full_name} عزیز، اکانت شما وصل است ✓\n"
                        "کارهای جدید همین‌جا برایتان می‌آید.", MAIN_KEYBOARD)


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
    link = BaleLink.objects.select_related("user").filter(chat_id=chat_id).first()

    def answer(text: str) -> None:
        try:
            api_call("answerCallbackQuery", {"callback_query_id": cq_id, "text": text})
        except BaleError:
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
    except BaleError:
        # Older clients / API variants: fall back to a fresh message.
        _reply(chat_id, task_card(task), markup)
