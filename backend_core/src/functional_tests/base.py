import time
from pathlib import Path
import os
import sys
import django
import dotenv
from dotenv import load_dotenv

from selenium.common import WebDriverException
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
import time


# Add your project to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
django.setup()

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
        super().setUp()
        # BYPASS: Point Selenium directly to your Nginx container!
        # (If your Nginx container is named something else in docker-compose, change this)
        self.live_server_url = 'http://nginx'
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")

        # Important for Docker: prevent shared memory issues
        options.add_argument("--disable-dev-shm-usage")

        # Set MOZ_HEADLESS environment variable
        os.environ['MOZ_HEADLESS'] = '1'

        # Add Firefox binary location explicitly
        options.binary_location = '/usr/bin/firefox'

        # Set up service with geckodriver path
        service = Service(
            executable_path='/usr/local/bin/geckodriver',
            log_path='/tmp/geckodriver.log'  # Optional: log for debugging
        )

        try:
            self.browser = webdriver.Firefox(service=service, options=options)
        except Exception as e:
            print(f"Error starting Firefox: {e}")
            # Try without service if above fails
            self.browser = webdriver.Firefox(options=options)

        # Set implicit wait
        self.browser.implicitly_wait(10)

    def tearDown(self):
        # --- NEW: Print JavaScript console logs on failure ---
        try:
            browser_logs = self.browser.get_log('browser')
            for log in browser_logs:
                # This will print any JS errors (like 404s or missing tokens) to your terminal
                print(f"BROWSER CONSOLE LOG: {log}")
        except Exception:
            pass
        # -----------------------------------------------------

        if hasattr(self, 'browser'):
            self.browser.quit()
        super().tearDown()