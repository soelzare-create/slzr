"""Run the Bale bot with long polling (no public HTTPS needed).

Alternative to the webhook. Also runs the periodic jobs every 10 minutes, so
on a small server this one process is all the bot needs.
"""
import time

from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections

from apps.tasks import bale, services


class Command(BaseCommand):
    help = "اجرای ربات بله به روش long polling"

    def handle(self, *args, **options):
        if not bale.enabled():
            raise CommandError("BALE_BOT_TOKEN تنظیم نشده است.")
        try:
            bale.api_call("deleteWebhook", {})
        except bale.BaleError:
            pass  # no webhook set (or not supported) — polling works regardless
        self.stdout.write(self.style.SUCCESS("ربات بله در حال اجراست…"))
        offset, last_jobs = 0, 0.0
        while True:
            try:
                updates = bale.api_call(
                    "getUpdates",
                    {"offset": offset, "timeout": 25,
                     "allowed_updates": ["message", "callback_query"]},
                    timeout=35,
                )
                for update in updates or []:
                    offset = update["update_id"] + 1
                    try:
                        bale.handle_update(update)
                    except Exception as exc:  # noqa: BLE001
                        self.stderr.write(f"update failed: {exc}")
                if time.monotonic() - last_jobs > 600:
                    services.send_reminders()
                    bale.deliver_pending()
                    last_jobs = time.monotonic()
            except bale.BaleError as exc:
                self.stderr.write(f"bale: {exc}")
                time.sleep(5)
            finally:
                close_old_connections()
