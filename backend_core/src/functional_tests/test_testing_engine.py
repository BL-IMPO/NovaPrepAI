from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests
import random
import string

from .base import wait, FunctionalTest


class TestingEngineFunctionalTest(FunctionalTest):
    def setUp(self):
        super().setUp()

        # Generate a unique email so the persistent DB doesn't block us with duplicates
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        self.email = f'zhanyl_{suffix}@novaprep.com'
        self.password = 'SmartStudent123!'

        # SEED THE REAL DATABASE VIA YOUR API
        api_url = f"{self.live_server_url}/api/register/"

        response = requests.post(api_url, json={
            "email": self.email,
            "username": f"zhanyl_{suffix}",
            "password": self.password,
            "password2": self.password,
            "first_name": "Zhanyl",
            "full_name": "Zhanyl Tester"  # <-- ADDED THIS FIELD
        })

        # --- Print the exact error if it fails! ---
        if response.status_code not in [200, 201]:
            print(f"\n--- API REGISTRATION FAILED ---")
            print(f"Status Code: {response.status_code}")
            print(f"Error Message: {response.text}")
            print(f"-------------------------------\n")
            response.raise_for_status()

    @wait
    def test_complete_test_submission_flow(self):
        """
        Test that a logged-in user can load a test, select an answer,
        submit it, handle the warning modal, and see their results.
        """
        # 1. Zhanyl logs in to the system
        self.browser.get(f"{self.live_server_url}/login.html")
        self.browser.find_element(By.ID, 'email').send_keys(self.email)
        self.browser.find_element(By.ID, 'password').send_keys(self.password)

        login_btn = WebDriverWait(self.browser, 5).until(
            EC.element_to_be_clickable((By.ID, 'loginButton'))
        )
        login_btn.click()

        # Wait for the redirect to finish
        WebDriverWait(self.browser, 5).until(
            lambda b: "login" not in b.current_url
        )

        # 2. She navigates directly to the Math 1 test page
        self.browser.get(f"{self.live_server_url}/testing/math_1")

        # 3. She waits for FastAPI to fetch the JSON and render questions
        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.ID, 'currentQuestionTitle'))
        )

        # 4. She selects the very first answer option
        first_answer_box = self.browser.find_element(By.CSS_SELECTOR, '.answer-option')
        first_answer_box.click()
        time.sleep(0.5)

        # 5. She clicks the Submit button
        self.browser.find_element(By.ID, 'submitBtn').click()

        # 6. Unanswered Warning Modal appears -> clicks "Submit Anyway"
        confirm_btn = WebDriverWait(self.browser, 5).until(
            EC.element_to_be_clickable((By.ID, 'confirmSubmitBtn'))
        )
        confirm_btn.click()

        # 7. FastAPI grades the test -> waits for Success Modal
        score_element = WebDriverWait(self.browser, 10).until(
            EC.visibility_of_element_located((By.ID, 'modalScore'))
        )
        self.assertTrue(score_element.text.isdigit(), "Score should be a number")