import time
import os
from pathlib import Path

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.common import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.wpewebkit.options import Options

MAX_WAIT = 5


def wait(fn):
    def modified_fn(*args, **kwargs):
        start_time = time.time()
        while True:
            try:
                return fn(*args, **kwargs)
            except (AssertionError, WebDriverException) as e:
                if time.time() - start_time > MAX_WAIT:
                    raise e
                time.sleep(0.5)

    return modified_fn


class FunctionalTest(StaticLiveServerTestCase):
    def setUp(self):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")

        # Also set these environment variables
        os.environ['MOZ_HEADLESS'] = '1'

        # Create the driver with options
        self.browser = webdriver.Firefox(options=options)
        self.browser.implicitly_wait(3)

    def tearDown(self):
        self.browser.quit()
        super().tearDown()

    def test_main_page(self):
        # Aby goest to the main page
        self.browser.get("0.0.0.0:8000")

        # Aby sees a welcome headline with text "TESTIMO"
        self.elements = self.browser.find_element(By.TAG_NAME, 'h2')

        self.assertIn("Testimo", self.elements.text)

