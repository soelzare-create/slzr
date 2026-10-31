"""Run the Telegram bot with long polling (no public HTTPS needed).

Alternative to the webhook. Also runs the periodic jobs every 10 minutes, so
on a small server this one process is all the bot needs.
"""
import time

from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections

from apps.tasks import services, telegram


class Command(BaseCommand):
    help = "اجرای ربات تلگرام به روش long polling"

    def handle(self, *args, **options):
        if not telegram.enabled():
            raise CommandError("TELEGRAM_BOT_TOKEN تنظیم نشده است.")
        telegram.api_call("deleteWebhook", {})
        self.stdout.write(self.style.SUCCESS("ربات تلگرام در حال اجراست…"))
        offset, last_jobs = 0, 0.0
        while True:
            try:
                updates = telegram.api_call(
                    "getUpdates",
                    {"offset": offset, "timeout": 25,
                     "allowed_updates": ["message", "callback_query"]},
                    timeout=35,
                )
                for update in updates or []:
                    offset = update["update_id"] + 1
                    try:
                        telegram.handle_update(update)
                    except Exception as exc:  # noqa: BLE001
                        self.stderr.write(f"update failed: {exc}")
                if time.monotonic() - last_jobs > 600:
                    services.send_reminders()
                    telegram.deliver_pending()
                    last_jobs = time.monotonic()
            except telegram.TelegramError as exc:
                self.stderr.write(f"telegram: {exc}")
                time.sleep(5)
            finally:
                close_old_connections()
