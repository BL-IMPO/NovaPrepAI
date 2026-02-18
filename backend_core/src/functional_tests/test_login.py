from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import random
import string

from .base import wait, FunctionalTest


class UserAuthFunctionalTest(FunctionalTest):
    def setUp(self):
        super().setUp()

        # 1. Generate random suffix to avoid "User already exists" errors in our persistent DB!
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        self.email = f'selenium_{suffix}@test.com'
        self.password = 'SeleniumPass123!'

        # Unique credentials for the registration flow test
        self.newbie_email = f'newbie_{suffix}@selenium.com'
        self.newbie_nickname = f'Newbie_{suffix}'

        # 2. Seed the database via API
        api_url = f"{self.live_server_url}/api/register/"
        response = requests.post(api_url, json={
            "email": self.email,
            "username": f"tester_{suffix}",
            "password": self.password,
            "password2": self.password,
            "first_name": "Selenium",
            "full_name": "Selenium Tester"  # <-- ADDED THIS FIELD
        })

        # 3. Print exactly why it fails if Django rejects it
        if response.status_code not in [200, 201]:
            print(f"\n--- API REGISTRATION FAILED IN SETUP ---")
            print(f"Status Code: {response.status_code}")
            print(f"Error Message: {response.text}")
            print(f"----------------------------------------\n")
            response.raise_for_status()

    @wait
    def test_login_flow(self):
        """Test that a user can log in via login.html"""
        self.browser.get(f"{self.live_server_url}/login.html")

        self.browser.find_element(By.ID, 'email').send_keys(self.email)
        self.browser.find_element(By.ID, 'password').send_keys(self.password)
        self.browser.find_element(By.ID, 'loginButton').click()

        WebDriverWait(self.browser, 50).until(
            EC.url_contains('dashboard')
        )

        access_token = self.browser.execute_script("return window.localStorage.getItem('access_token');")
        self.assertIsNotNone(access_token, "Access token was not found in localStorage!")
    @wait
    def test_registration_flow(self):
        """Test that a new user can register via registration.html"""
        self.browser.get(f"{self.live_server_url}/registration.html")

        self.browser.find_element(By.ID, 'full_name').send_keys('New Selenium User')
        self.browser.find_element(By.ID, 'nickname').send_keys(self.newbie_nickname)
        self.browser.find_element(By.ID, 'email').send_keys(self.newbie_email)
        self.browser.find_element(By.ID, 'password').send_keys('StrongPass123!')
        self.browser.find_element(By.ID, 'password_confirm').send_keys('StrongPass123!')

        terms_checkbox = self.browser.find_element(By.ID, 'terms')
        if not terms_checkbox.is_selected():
            terms_checkbox.click()

        self.browser.find_element(By.ID, 'newsletter').click()
        self.browser.find_element(By.ID, 'registerButton').click()

        WebDriverWait(self.browser, 5).until(
            lambda driver: 'registration.html' not in driver.current_url
        )

        access_token = self.browser.execute_script("return window.localStorage.getItem('access_token');")
        self.assertIsNotNone(access_token, "Access token was not found in localStorage after registration!")