from datetime import timedelta
from time import sleep
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from shots.models import ScreenShot


class Command(BaseCommand):
    help = 'Remove screenshots mor than 7 days old'

    def handle(self, *args, **options):

        while True:
            target_day = timezone.now() - timedelta(days=7)
            count, result = ScreenShot.objects.filter(created_at__lt=target_day).delete()
            self.stdout.write(self.style.SUCCESS(f'Deleted {count} screenshots'))

            sleep(86400)