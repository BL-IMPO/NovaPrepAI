from django.test import TestCase
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from users.models import UserProfile


class UserProfileModelTest(TestCase):
    def setUp(self):
        # Create a user to be used in tests
        self.email = 'modeltest@example.com'
        self.password = 'testpass123'
        self.user = User.objects.create_user(
            username=self.email,
            email=self.email,
            password=self.password,
        )

    def test_profile_creation_signal(self):
        """
        Test that creating a User automatically creates a UserProfile
        via the post_save signal.
        """

        # Check if profile exists
        self.assertTrue(hasattr(self.user, 'userprofile'))
        self.assertIsInstance(self.user.userprofile, UserProfile)

        # Check initial values
        profile = self.user.userprofile
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.nickname, '')
        self.assertFalse(profile.subscribe_newsletter)

    def test_update_profile_fields(self):
        """
        Test that we can successfully update profile fields.
        """
        profile = self.user.userprofile
        profile.nickname = 'CoolTester'
        profile.subscribe_newsletter = True
        profile.save()

        # Refresh from database
        profile.refresh_from_db()

        self.assertEqual(profile.nickname, 'CoolTester')
        self.assertTrue(profile.subscribe_newsletter)

    def test_str_representation(self):
        """
        Test the __str__method of the model.
        """
        profile = self.user.userprofile
        expected_str = f"{self.email} Profile"
        self.assertEqual(str(profile), expected_str)

    def test_one_to_one_relationship(self):
        """
        Test that one user cannot have multiple profiles
        (Enforced by OneToOneField).
        """
        with self.assertRaises(IntegrityError):
            UserProfile.objects.create(user=self.user)