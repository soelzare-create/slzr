"""Management command: release expired 48h soft reservations (Section 5/6).

Wire this to cron or Celery beat, e.g. every 15 minutes:
    */15 * * * * python manage.py release_reservations
"""
from django.core.management.base import BaseCommand

from apps.sales.services import release_expired_reservations


class Command(BaseCommand):
    help = "آزادسازی رزروهای نرم منقضی‌شده (۴۸ ساعت)"

    def handle(self, *args, **options):
        count = release_expired_reservations()
        self.stdout.write(self.style.SUCCESS(f"✓ {count} رزرو آزاد شد."))
