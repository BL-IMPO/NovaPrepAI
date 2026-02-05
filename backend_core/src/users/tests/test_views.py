from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth.models import User
from users.models import UserProfile


class BaseViewTest(APITestCase):
    def setUp(self):
        # Create a standard user for login/profile tests
        self.email = 'test@example.com'
        self.password = 'strongpass123'
        self.user = User.objects.create_user(
            username=self.email,
            email=self.email,
            password=self.password,
            first_name='Test',
            last_name='User',
        )

        # Ensure profile exists (handling signal/manual creation race conditions)
        if not hasattr(self.user, 'userprofile'):
            UserProfile.objects.create(user=self.user)

        # URL Configuration - UPDATED WITH NAMESPACE 'users'
        self.login_url = reverse('users:token_obtain_pair')
        self.register_url = reverse('users:register')
        self.profile_url = reverse('users:user_profile')

class RegisterViewTest(BaseViewTest):
    def test_register_success(self):
        """
        Test that registration creates a user and sets authentication cookies.
        """

        data = {
            'email': 'newuser@example.com',
            'password': 'StrongPassword!123',
            'password2': 'StrongPassword!123',
            'full_name': 'New User',
            'nickname': 'Newbie',
        }
        response = self.client.post(self.register_url, data)

        # 1. Check HTTP Status
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 2. Check if Tokens are in Cookies (Critical for app)
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)
        self.assertTrue(response.cookies['access_token']['httponly'])

        # 3. Check Response Data structure
        self.assertEqual(response.data['user']['email'], 'newuser@example.com')

        # Check if profile data was saved via the serializer/signal logic
        new_user = User.objects.get(email='newuser@example.com')
        self.assertEqual(new_user.userprofile.nickname, 'Newbie')

    def test_register_duplicate_email(self):
        """
        Test that registering with an existing email fails.
        """
        data = {
            'email': self.email,
            'password': 'StrongPassword!123',
            'password2': 'StrongPassword!123',
            'full_name': 'Copy Cat',
        }

        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_register_password_mismatch(self):
        """
        Test validation when passwords do not match.
        """
        data = {
            'email': 'mismatch@example.com',
            'password': 'pass1',
            'password2': 'pass2',
            'full_name': 'Mismatch User',
        }

        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class LoginViewTest(BaseViewTest):
    def test_login_success_with_email(self):
        """
        Test login with email and verify custom response logic.
        """
        data = {
            'email': self.email,
            'password': self.password,
        }

        response = self.client.post(self.login_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify Cookies are set
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)

        # Verify Custom Response Data
        self.assertEqual(response.data['redirect_url'], '/dashboard')

    def test_login_invalid_credentials(self):
        """
        Test login fails with wrong password.
        """
        data = {
            'email': self.email,
            'password': 'wrongpassword',
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserProfileViewTest(BaseViewTest):
    def test_get_profile_unauthenticated(self):
        """
        Test that anonymous users cannot access profile data.
        """
        self.client.logout() # Ensure we are logged out
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_profile_authenticated(self):
        """
        Test that logged-in users can see their own profile.
        """
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.email)
        self.assertEqual(response.data['username'], self.email)

    def test_update_profile_nickname(self):
        """
        Test PATCH request to update profile nickname.
        """
        self.client.force_authenticate(user=self.user)

        data = {
            'nickname': 'UpdatedNick',
        }
        response = self.client.patch(self.profile_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nickname'], 'UpdatedNick')

        # Verify DB was actually updated
        self.user.userprofile.refresh_from_db()
        self.assertEqual(self.user.userprofile.nickname, 'UpdatedNick')

    def test_update_user_fields(self):
        """
        Test PATCH request to update User model fields (first_name).
        """
        self.client.force_authenticate(user=self.user)

        data = {
            'first_name': 'NewName'
        }
        response = self.client.patch(self.profile_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'NewName')

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'NewName')
