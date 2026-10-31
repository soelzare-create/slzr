"""Point the Telegram bot at this server's webhook.

    python manage.py telegram_webhook https://example.com
"""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.tasks import telegram


class Command(BaseCommand):
    help = "ثبت آدرس webhook ربات تلگرام"

    def add_arguments(self, parser):
        parser.add_argument("base_url", help="آدرس عمومی سایت، مثلاً https://app.daranx.ir")

    def handle(self, *args, base_url, **options):
        if not telegram.enabled():
            raise CommandError("TELEGRAM_BOT_TOKEN تنظیم نشده است.")
        if not settings.TELEGRAM_WEBHOOK_SECRET:
            raise CommandError("TELEGRAM_WEBHOOK_SECRET تنظیم نشده است.")
        url = base_url.rstrip("/") + "/api/telegram/webhook"
        telegram.api_call("setWebhook", {
            "url": url, "secret_token": settings.TELEGRAM_WEBHOOK_SECRET,
            "allowed_updates": ["message", "callback_query"],
        })
        self.stdout.write(self.style.SUCCESS(f"webhook → {url}"))
