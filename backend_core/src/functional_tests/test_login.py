from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from django.contrib.auth.models import User
from users.models import UserProfile

from .base import wait, FunctionalTest


class UserAuthFunctionalTest(FunctionalTest):
    def setUp(self):
        super().setUp()
        self.email = 'selenium@test.com'
        self.password = 'SeleniumPass123!'

        # Create user for login test
        self.user = User.objects.create_user(
            username=self.email,
            email=self.email,
            password=self.password,
            first_name="Selenium",
            last_name="Tester",
        )

        # Ensure profile exists (via signal or manual)
        if not hasattr(self.user, 'userprofile'):
            UserProfile.objects.create(user=self.user)

    @wait
    def test_login_flow(self):
        """
        Test that a user can log in via login.html
        """

        # 1. Zhanyl sees the login button she clicks it and sees the login page
        self.browser.get(f"{self.live_server_url}/login.html")

        # 2. Zhanyl writes her account info
        self.browser.find_element(By.ID, 'email').send_keys(self.email)
        self.browser.find_element(By.ID, 'password').send_keys(self.password)

        # 3. Zhanyl clicks Login button
        self.browser.find_element(By.ID, 'loginButton').click()

        # 4. After a little waiting Zhanyl authorized and get to the dashboard page
        WebDriverWait(self.browser, 5).until(
            EC.url_contains('dashboard')
        )

        ## Verify Cookies were set
        cookies = {c['name'] for c in self.browser.get_cookies()}
        self.assertIn('access_token', cookies)

    @wait
    def test_registration_flow(self):
        """
        Test that a new user can register via registration.html
        """
        # 1. Zhanyl sees a registration button. She clicks it and sees the registration page
        self.browser.get(f"{self.live_server_url}/registration.html")

        # 2. Zhanyl wants to create a new account so she fills fields wit her data
        self.browser.find_element(By.ID, 'full_name').send_keys('New Selenium User')
        self.browser.find_element(By.ID, 'nickname').send_keys('Newbie')
        self.browser.find_element(By.ID, 'email').send_keys('newbie@selenium.com')
        self.browser.find_element(By.ID, 'password').send_keys('StrongPass123!')
        ## NOTE: id="password_confirm", but Serializer expects "password2" this handled in auth.js by renaming it manually
        self.browser.find_element(By.ID, 'password_confirm').send_keys('StrongPass123!')

        # After Zhanyl filled all fields she sees checkboxes at the bottom and confirms
        # that she read all terms
        terms_checkbox = self.browser.find_element(By.ID, 'terms')
        if not terms_checkbox.is_selected():
            terms_checkbox.click()

        # Zhanyl decided that she wants to recive emails with news on her email
        self.browser.find_element(By.ID, 'newsletter').click()

        # 4. Zhansyl clicks register buuton
        self.browser.find_element(By.ID, 'registerButton').click()

        # 5. After waiting for a while she sees that she is at the main page
        WebDriverWait(self.browser, 20).until(
            lambda driver: 'registration.html' not in driver.current_url
        )

        cookies = {c['name'] for c in self.browser.get_cookies()}
        self.assertIn('access_token', cookies)
