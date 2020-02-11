from django.core.management.base import BaseCommand, CommandError
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from django.conf import settings
from time import sleep
from shots.models import ScreenShot
from datetime import datetime
import random
from PIL import Image
import io
from django.core.cache import cache


class Command(BaseCommand):
    help = 'Run the screenshot worker'

    def handle(self, *args, **options):

        self.stdout.write(self.style.SUCCESS(f'Starting Screenshot Firefox Worker.'))
        while True:
            # do this to try to prevent race conditions when multiple workers
            # are present. 
            sleep(random.randrange(1, 10))
            start = datetime.now().strftime('%s')
            shots = ScreenShot.objects.filter(status=ScreenShot.NEW)

            if shots.count() > 0:
                shot = shots.all()[0]
                cache.delete(shot.id.hex)
                self.stdout.write(self.style.SUCCESS(f'Screenshot started: {shot.url}'))

                shot.status = ScreenShot.PENDING
                shot.save()

                try:
                    self.get_screenshot(shot)
                    shot.status = ScreenShot.SUCCESS
                    shot.save()

                    end = datetime.now().strftime('%s')
                    diff = int(end) - int(start) - 5
                    shot.duration = diff
                    shot.save()
                    self.stdout.write(self.style.SUCCESS(f'Screenshot saved: {shot.url} {diff} seconds'))

                except WebDriverException as e:
                    shot.status = ScreenShot.FAILURE
                    shot.save()
                    self.stdout.write(self.style.ERROR(f'Error: {e}'))

    def get_screenshot(self, shot):
        options = Options()
        options.headless = True
        driver = webdriver.Firefox(options=options)
        driver.set_page_load_timeout(60)
        driver.set_window_size(shot.width, shot.height)
        driver.get(shot.url)

        # used by chron.com and others
        try:
            btn = driver.find_element_by_id('continue')
            btn.click()
        except NoSuchElementException:
            pass

        doc_element_height = driver.execute_script("return document.documentElement.scrollHeight")
        doc_body_height = driver.execute_script("return document.body.scrollHeight")
        height = doc_element_height if doc_element_height > doc_body_height else doc_body_height

        # some sites like pandora and statesman.com have error/GDPR pages that are shorter than
        # a normal screen.
        if height > shot.height:
            shot.height = height
            driver.set_window_size(shot.width, height+100)

        sleep(5)

        with io.BytesIO(driver.get_screenshot_as_png()) as png_file:

            with Image.open(png_file).convert('RGB') as i:

                with io.BytesIO() as output:
                    i.save(output, format="JPEG")
                    shot.image_binary = output.getvalue()

        shot.save()

        driver.quit()
