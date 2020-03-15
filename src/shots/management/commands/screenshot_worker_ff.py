import requests
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


class ScreenShotException(Exception):
    pass


class SeleniumScreenShot(object):
    def __init__(self, image_binary, height, title, description):
        self.image_binary = image_binary
        self.height = height
        self.title = title
        self.description = description


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
                    results = self.get_screenshot_new(shot)
                    shot.status = ScreenShot.SUCCESS
                    shot.height = results.height
                    shot.image_binary = results.image_binary
                    shot.duration = int(timezone.now().strftime('%s')) - int(start)

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
            'content': shot.image_as_base64,
            'title': shot.meta['title'],
            'description': shot.meta['description']
        }

        headers = {
            'content-type': 'application/json'
        }

        requests.post(shot.callback_url, json=payload, headers=headers)

        self.stdout.write(self.style.SUCCESS(f'Fired Webhook: {shot.url} to {shot.callback_url}'))


    def get_screenshot(self, shot):

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

        options = Options()
        options.headless = True

        driver = webdriver.Firefox(options=options, firefox_profile=profile)
        driver.install_addon(f'{settings.BASE_DIR}/firefox-extensions/i_dont_care_about_cookies-3.1.3-an+fx.xpi')
        driver.set_page_load_timeout(60)
        driver.set_window_size(shot.width, shot.height)
        driver.get(shot.url)

        for i in range(10):
            doc_element_height = driver.execute_script("return document.documentElement.scrollHeight")
            doc_body_height = driver.execute_script("return document.body.scrollHeight")
            height = doc_element_height if doc_element_height > doc_body_height else doc_body_height
            driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
            sleep(1)

        # some sites like pandora and statesman.com have error/GDPR pages that are shorter than
        # a normal screen.
        if height > shot.height:
            shot.height = height
            driver.set_window_size(shot.width, height+100)

        sleep(shot.sleep_seconds)

        with io.BytesIO(driver.get_screenshot_as_png()) as png_file:

            with Image.open(png_file).convert('RGB') as i:

                with io.BytesIO() as output:
                    i.save(output, format="JPEG")
                    shot.image_binary = output.getvalue()

        shot.save()

        driver.quit()

    def get_screenshot_new(self, shot) -> SeleniumScreenShot:

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

        with io.BytesIO(driver.get_screenshot_as_png()) as png_file:

            with Image.open(png_file).convert('RGB') as i:

                with io.BytesIO() as output:
                    i.save(output, format="JPEG")
                    image_binary = output.getvalue()

        title = driver.title
        try:
            description = driver.find_element_by_xpath("//meta[@name='description']").get_attribute("content")
        except NoSuchElementException:
            description = title

        driver.quit()
        return SeleniumScreenShot(height=height, image_binary=image_binary, title=title, description=description)