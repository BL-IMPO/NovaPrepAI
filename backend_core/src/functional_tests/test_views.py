import os
import sys

from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
import time

from .base import wait, FunctionalTest


class ViewsTest(FunctionalTest):
    @wait
    def test_main_page(self):
        # Zhanyl goest to the main page
        self.browser.get(self.live_server_url)

        # Zhanyl sees a welcome headline with text "TESTIMO"
        self.elements = self.browser.find_element(By.TAG_NAME, 'h2')

        self.assertIn("TESTIMO", self.elements.text)
