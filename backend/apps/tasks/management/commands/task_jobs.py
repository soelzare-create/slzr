"""Periodic task jobs — run every ~10 minutes from cron.

* retries queued Telegram messages
* reminds about tasks untouched for 24h
"""
from django.core.management.base import BaseCommand

from apps.tasks import services, telegram


class Command(BaseCommand):
    help = "ارسال مجدد پیام‌های تلگرام در صف + یادآوری کارهای ۲۴ ساعت دست‌نخورده"

    def handle(self, *args, **options):
        reminded = services.send_reminders()
        sent = telegram.deliver_pending()
        self.stdout.write(f"reminders={reminded} telegram_sent={sent}")
