import tempfile

import requests
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException, WebDriverException, TimeoutException
from django.conf import settings
from time import sleep
from shots.models import ScreenShot
from datetime import datetime
import random
from PIL import Image
import io
from django.core.cache import cache
from django.core.cache import caches
from sentry_sdk import capture_exception
import boto3


class ScreenShotException(Exception):
    pass


class SeleniumScreenShot(object):
    def __init__(self, height, title, description, file):
        self.height = height
        self.title = title
        self.description = description
        self.file = file

"""
def upload_to_s3(file_bytes, s3_object_name):

    # required because we are on scaleway at the moment
    s3 = boto3.client('s3',
                      region_name=settings.S3_REGION_NAME,
                      endpoint_url=settings.S3_ENDPOINT_URL,
                      aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
                      )

    s3.put_object(
        Body=file_bytes,
        Bucket=f"{settings.S3_BUCKET_PREFIX}",
        Key=s3_object_name,
        ACL='public-read',
        CacheControl='max-age=31556926' # 1 year
    )
"""

def convert_png_to_jpg(binary_data) -> bytes:

    with io.BytesIO(binary_data) as png_file:
        with Image.open(png_file).convert('RGB') as i:
            with io.BytesIO() as output:
                i.save(output, format="JPEG")
                image_binary = output.getvalue()

    return image_binary

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

            if shots.count() > 0:
                shot = shots.all()[0]
                self.stdout.write(self.style.SUCCESS(f'Screenshot started: {shot.url}'))

                cache.delete(shot.id.hex)
                caches['page'].clear()

                shot.status = ScreenShot.PENDING
                shot.save()

                try:
                    results = self.get_screenshot(shot)
                    shot.status = ScreenShot.SUCCESS
                    shot.height = results.height
                    shot.duration = int(timezone.now().strftime('%s')) - int(start)

                    with tempfile.TemporaryFile(mode="w+b") as f:
                        f.write(results.file)
                        shot.file.save(f"{shot.id.hex}.jpg", File(f))

                    # JSON Fields
                    shot.meta = {
                        'title': results.title,
                        'description': results.description
                    }

                    shot.save()

                    self.stdout.write(self.style.SUCCESS(f'Screenshot saved: {shot.url} {shot.duration} seconds'))
                    self.do_webhook(shot)

                except ScreenShotException as e:
                    shot.status = ScreenShot.FAILURE
                    shot.save()
                    self.stdout.write(self.style.ERROR(f'Error: {e}'))

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

    def get_screenshot(self, shot) -> SeleniumScreenShot:

        profile = webdriver.FirefoxProfile()
        profile.set_preference("layout.css.devPixelsPerPx", str(shot.dpi))

        if settings.SOCKS5_PROXY_ENABLED:
            self.stdout.write(self.style.SUCCESS(f'Proxy enabled: {settings.SOCKS5_PROXY_HOSTNAME}:{settings.SOCKS5_PROXY_PORT}'))
            profile.set_preference('network.proxy.type', 1)
            profile.set_preference("network.proxy.socks_version", 5)
            profile.set_preference('network.proxy.socks', settings.SOCKS5_PROXY_HOSTNAME)

            # explicit casting to int because otherwise it is ignored and fails silently.
            profile.set_preference('network.proxy.socks_port', int(settings.SOCKS5_PROXY_PORT))
            profile.set_preference("network.proxy.socks_remote_dns", True)

            profile.set_preference("dom.webnotifications.enabled", False)
            profile.set_preference("dom.push.enabled", False)

        options = Options()
        options.headless = True

        driver = webdriver.Firefox(options=options, firefox_profile=profile)
        driver.install_addon(f'{settings.BASE_DIR}/firefox-extensions/i_dont_care_about_cookies-3.1.3-an+fx.xpi')
        driver.set_page_load_timeout(60)
        driver.set_window_size(shot.width, shot.height)

        try:
            driver.get(shot.url)
        except WebDriverException as e:
            driver.quit()
            capture_exception(e)
            raise ScreenShotException

        for i in range(10):
            doc_element_height = driver.execute_script("return document.documentElement.scrollHeight")
            doc_body_height = driver.execute_script("return document.body.scrollHeight")
            height = doc_element_height if doc_element_height > doc_body_height else doc_body_height
            driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
            sleep(1)

        # some sites like pandora and statesman.com have error/GDPR pages that are shorter than
        # a normal screen.
        if height > shot.height:
            driver.set_window_size(shot.width, height+100)

        sleep(shot.sleep_seconds) # this might not be necessary, but needs testing

        image_binary = convert_png_to_jpg(driver.get_screenshot_as_png())

        # with io.BytesIO(driver.get_screenshot_as_png()) as png_file:
        #
        #     with Image.open(png_file).convert('RGB') as i:
        #
        #         with io.BytesIO() as output:
        #             i.save(output, format="JPEG")
        #             image_binary = output.getvalue()

        title = driver.title
        try:
            description = driver.find_element_by_xpath("//meta[@name='description']").get_attribute("content")
        except NoSuchElementException:
            description = title

        driver.quit()
        return SeleniumScreenShot(height=height, title=title, description=description, file=image_binary)