import tempfile

import requests
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from time import sleep
from shots.models import ScreenShot
import random
from django.core.cache import cache
from django.core.cache import caches
from boto3.exceptions import Boto3Error
from shots.screenshot_driver import (
    ScreenShotException,
    get_screenshot
)


class Command(BaseCommand):
    help = 'Run the screenshot worker'

    def handle(self, *args, **options):

        self.stdout.write(self.style.SUCCESS(f'Starting Screenshot Firefox Worker.'))
        while True:
            # do this to try to prevent race conditions when multiple workers
            # are present. 
            sleep(random.randrange(1, 10))

            start = timezone.now().strftime('%s')
            shots = ScreenShot.objects.filter(status=ScreenShot.NEW)

            # Bail out if there is no work to do
            if shots.count() == 0:
                continue

            shot = shots.all()[0]
            self.stdout.write(self.style.SUCCESS(f'Screenshot started: {shot.url}'))

            cache.delete(shot.id.hex)
            caches['page'].clear()

            shot.status = ScreenShot.PENDING
            shot.save()

            try:
                results = get_screenshot(shot)

            # Save the screenshot status and bail out if there was a failure
            except ScreenShotException as e:
                shot.status = ScreenShot.FAILURE
                shot.save()
                self.stdout.write(self.style.ERROR(f'Error: {e}'))
                continue

            shot.status = ScreenShot.SUCCESS
            shot.height = results.height
            shot.duration = int(timezone.now().strftime('%s')) - int(start)

            with tempfile.TemporaryFile(mode="w+b") as f:
                f.write(results.file)

                try:
                    shot.file.save(f"{shot.id.hex}.jpg", File(f))
                except Boto3Error as e:
                    # todo handle error
                    pass

            # JSON Fields
            shot.meta = {
                'title': results.title,
                'description': results.description
            }

            shot.save()

            self.stdout.write(self.style.SUCCESS(f'Screenshot saved: {shot.url} {shot.duration} seconds'))
            self.do_webhook(shot)

    def do_webhook(self, shot):

        if not shot.callback_url:
            return

        payload = {
            'id': shot.id.hex,
            'url': shot.url,
            'callback_url': shot.callback_url,
            'created_at': shot.created_at.strftime("%Y-%m-%dT%H:%M:%S%z"),
            'image_url': shot.s3_url,
            'title': shot.meta['title'],
            'description': shot.meta['description']
        }

        headers = {
            'content-type': 'application/json'
        }

        requests.post(shot.callback_url, json=payload, headers=headers)

        self.stdout.write(self.style.SUCCESS(f'Fired Webhook: {shot.url} to {shot.callback_url}'))
