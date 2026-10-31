"""Periodic task jobs — run every ~10 minutes from cron.

* retries queued Bale messages
* reminds about tasks untouched for 24h
"""
from django.core.management.base import BaseCommand

from apps.tasks import bale, services


class Command(BaseCommand):
    help = "ارسال مجدد پیام‌های بله در صف + یادآوری کارهای ۲۴ ساعت دست‌نخورده"

    def handle(self, *args, **options):
        reminded = services.send_reminders()
        sent = bale.deliver_pending()
        self.stdout.write(f"reminders={reminded} bale_sent={sent}")
