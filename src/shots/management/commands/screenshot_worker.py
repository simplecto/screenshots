from django.core.management.base import BaseCommand, CommandError
from selenium import webdriver
from time import sleep
from shots.models import ScreenShot
from django.conf import settings
    
class Command(BaseCommand):
    help = 'Run the screenshot worker'

    def handle(self, *args, **options):

        while True:
            sleep(3)
            shots = ScreenShot.objects.filter(status=ScreenShot.NEW)

            if shots.count() > 0:
                shot = shots.all()[0]
                self.stdout.write(self.style.SUCCESS(f'Screenshot started: {shot.url}'))
                
                shot.status = ScreenShot.PENDING
                shot.save()
                self.get_screenshot(shot)
                shot.status = ScreenShot.SUCCESS
                shot.save()
                
                self.stdout.write(self.style.SUCCESS(f'Screenshot saved: {shot.url}'))

    def get_screenshot(self, shot):
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')

        driver = webdriver.Chrome(options=options)
        driver.set_window_size(1280,960)
        driver.get(shot.url)

        height = driver.execute_script("return document.body.scrollHeight")
        driver.set_window_size(1280,height+100)
        sleep(10)
        driver.save_screenshot(f"{settings.IMAGE_DIR}/{shot.id}.png")

        driver.quit()
