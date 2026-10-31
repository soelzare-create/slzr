"""Point the Bale bot at this server's webhook.

    python manage.py bale_webhook https://app.daranx.com

Without SSH (cPanel), open this once in a browser instead:
    https://tapi.bale.ai/bot<TOKEN>/setWebhook?url=https://app.daranx.com/api/bale/webhook/<SECRET>
"""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.tasks import bale


class Command(BaseCommand):
    help = "ثبت آدرس webhook ربات بله"

    def add_arguments(self, parser):
        parser.add_argument("base_url", help="آدرس عمومی سایت، مثلاً https://app.daranx.com")

    def handle(self, *args, base_url, **options):
        if not bale.enabled():
            raise CommandError("BALE_BOT_TOKEN تنظیم نشده است.")
        if not settings.BALE_WEBHOOK_SECRET:
            raise CommandError("BALE_WEBHOOK_SECRET تنظیم نشده است.")
        url = f"{base_url.rstrip('/')}/api/bale/webhook/{settings.BALE_WEBHOOK_SECRET}"
        bale.api_call("setWebhook", {"url": url})
        self.stdout.write(self.style.SUCCESS("webhook ثبت شد."))
