from time import sleep
import os
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException, WebDriverException, TimeoutException
from django.conf import settings
from sentry_sdk import capture_exception
from PIL import Image
import io


class ScreenShotException(Exception):
    pass


class SeleniumScreenShot(object):
    def __init__(self, height, title, description, file):
        self.height = height
        self.title = title
        self.description = description
        self.file = file


def convert_png_to_jpg(binary_data) -> bytes:

    with io.BytesIO(binary_data) as png_file:
        with Image.open(png_file).convert('RGB') as i:
            with io.BytesIO() as output:
                i.save(output, format="JPEG")
                image_binary = output.getvalue()

    return image_binary


def get_screenshot(shot) -> SeleniumScreenShot:

    profile = webdriver.FirefoxProfile()
    profile.set_preference("layout.css.devPixelsPerPx", str(shot.dpi))

    if settings.SOCKS5_PROXY_ENABLED:
        #self.stdout.write(self.style.SUCCESS(f'Proxy enabled: {settings.SOCKS5_PROXY_HOSTNAME}:{settings.SOCKS5_PROXY_PORT}'))
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

    driver = webdriver.Firefox(options=options, firefox_profile=profile, log_path=os.devnull)
    driver.install_addon(f'{settings.BASE_DIR}/firefox-extensions/i_dont_care_about_cookies-3.1.3-an+fx.xpi')
    driver.set_page_load_timeout(60)
    driver.set_window_size(shot.width, shot.height)

    try:
        driver.get(shot.url)
    except WebDriverException as e:
        driver.quit()
        capture_exception(e)
        raise ScreenShotException(e)

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

    title = driver.title
    try:
        description = driver.find_element_by_xpath("//meta[@name='description']").get_attribute("content")
    except NoSuchElementException:
        description = title

    driver.quit()
    return SeleniumScreenShot(height=height, title=title, description=description, file=image_binary)
