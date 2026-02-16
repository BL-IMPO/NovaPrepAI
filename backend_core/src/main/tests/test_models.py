from django.test import TestCase
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from main.models import TestAttempt


class TestAttemptModelTest(TestCase):
    def setUp(self):
        # Create a user to be used in tests
        self.email = 'modeltest@example.com'
        self.password = 'testpass123'
        self.user = User.objects.create_user(
            username=self.email,
            email=self.email,
            password=self.password,
        )

        # Create simple details
        self.test_type = "MATH 1"
        self.score = 25
        self.weighted_score = 30.7
        self.details = {
            "MATH 1: Question 1.": [
                "A", "A", "B", "C", "D", 1.23, ["SVG_GRAPH", '<svg class="w-6 h-6 text-gray-800 dark:text-white" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24"> <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18 6H6m12 4H6m12 4H6m12 4H6"/> </svg> ']
            ],
            "MATH 1: Question 2.": [
                "B", "A", "B", "C", "D", 1.9, ["SVG_GRAPH",
                                                '<svg class="w-6 h-6 text-gray-800 dark:text-white" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24"> <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18 6H6m12 4H6m12 4H6m12 4H6"/> </svg> ']
            ]
        }

        self.test_attempt = TestAttempt.objects.create(user=self.user,
                                   test_type=self.test_type,
                                   score=self.score,
                                   weighted_score=self.weighted_score,
                                   details=self.details,
                                   )

    def test_attempt_creation(self):
        """
        Test that we can create test attempt.
        """

        attempt = TestAttempt.objects.get(user=self.user)

        self.assertEqual(attempt.test_type, "MATH 1")
        self.assertEqual(attempt.score, self.score)
        self.assertEqual(attempt.weighted_score, self.weighted_score)
        self.assertEqual(attempt.details["MATH 1: Question 2."][-1][0], "SVG_GRAPH")
        self.assertFalse(attempt.passed)

    def test_update_test_attempt_fields(self):
        """
        Test that we can successfully update TestAttempt fields.
        """
        new_scores = 30
        new_weighted_scores = 43.5
        new_passed = True
        new_test_type = "MATH 2"

        TestAttempt.objects.filter(user=self.user).update(score=new_scores,
                                   weighted_score=new_weighted_scores,
                                   test_type=new_test_type,
                                   passed=new_passed, )

        attempt = TestAttempt.objects.get(user=self.user)

        self.assertEqual(attempt.score, new_scores)
        self.assertEqual(attempt.weighted_score, new_weighted_scores)
        self.assertEqual(attempt.test_type, new_test_type)
        self.assertTrue(attempt.passed)
        self.assertEqual(attempt.details["MATH 1: Question 2."][-1][0], "SVG_GRAPH")

    def test_str_representation(self):
        """
        Test the __str__method of the model.
        """
        expected_str = f"{self.user} - {self.test_type} - Count: {self.score}, Points: {self.weighted_score}"
        self.assertEqual(str(self.test_attempt), expected_str)
