from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import UserProfile
from api.serializer import (
    RegisterSerializer,
    UserSerializer,
    CustomTokenObtainPairSerializer
)


class RegisterSerializerTest(TestCase):
    def setUp(self):
        self.valid_data = {
            'email': 'test@example.com',
            'password': 'strongpassword123',
            'password2': 'strongpassword123',
            'full_name': 'John Doe',
            'nickname': 'Johnny',
            'subscribe_newsletter': True
        }

    def test_valid_registration(self):
        """
        Test that a user is successfully created with valid data.
        """
        serializer = RegisterSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()

        # Check if User was created
        self.assertEqual(user.email, 'test@example.com')
        # Check if full_name_was split correctly
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Doe')
        # Check that username is set to email as per your logic
        self.assertEqual(user.username, 'test@example.com')
        self.assertTrue(user.check_password('strongpassword123'))

    def test_password_mismatch(self):
        """
        Test validation fails if passwords do not match.
        """
        self.valid_data['password2'] = 'mismatch'
        serializer = RegisterSerializer(data=self.valid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_duplicate_email(self):
        """
        Test validation fails if email already exists.
        """
        # Create a user first
        User.objects.create(username='test@example.com', email='test@example.com')

        serializer = RegisterSerializer(data=self.valid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_name_split_logic(self):
        """
        Test edge cases for full_name splitting.
        """
        # Single name
        data = self.valid_data.copy()
        data['full_name'] = 'Cher'
        serializer = RegisterSerializer(data=data)
        serializer.is_valid()
        user = serializer.save()
        self.assertEqual(user.first_name, 'Cher')
        self.assertEqual(user.last_name, '')


class UserSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username='user@test.com',
            email='user@test.com',
            first_name='Alice',
            last_name='Smith',
        )

        self.profile = self.user.userprofile
        self.profile.nickname = 'AliceInWonderland'
        self.profile.subscribe_newsletter = True
        self.profile.save()

    def test_serialization_fields(self):
        """
        Test that data is serialized correctly, including profile fields.
        """
        serializer = UserSerializer(self.user)
        data = serializer.data

        self.assertEqual(data['username'], 'user@test.com')
        self.assertEqual(data['first_name'], 'Alice')
        # Check if fields pulled from UserProfile
        self.assertEqual(data['nickname'], 'AliceInWonderland')

        # Verify read-only fields are present
        self.assertIn('id', data)
        self.assertIn('avatar', data)


class CustomTokenSerializerTest(TestCase):
    def setUp(self):
        self.email = 'token@test.com'
        self.password = 'pass123'
        self.user = User.objects.create_user(
            username=self.email,
            email=self.email,
            password=self.password,
            first_name='TokenUser',
        )

    def test_get_token_claims(self):
        """
        Test that the custom claims are added to the token.
        """
        # Call the class method directly
        token = CustomTokenObtainPairSerializer.get_token(self.user)

        # Check standard claims
        self.assertEqual(int(token['user_id']), self.user.id)

        # Check YOUR custom claims
        self.assertEqual(token['username'], self.email)
        self.assertEqual(token['email'], self.email)
        self.assertEqual(token['first_name'], 'TokenUser')

    def test_validate_authentication(self):
        """
        Test the validate method which handles authentication.
        """
        data = {
            'email': self.email,
            'password': self.password,
            'username': self.email,
        }

        serializer = CustomTokenObtainPairSerializer(data=data)
        # check if validate() returns the response data
        self.assertTrue(serializer.is_valid(), serializer.errors)
        result = serializer.validated_data

        # Check that access/refresh tokens are generated
        self.assertIn('access', result)
        self.assertIn('refresh', result)

        # Check custom user data in response
        self.assertIn('user', result)
        self.assertEqual(result['user']['email'], self.email)

    def test_validate_invalid_credentials(self):
        data = {
            'email': self.email,
            'password': 'wrongpassword',
        }

        serializer = CustomTokenObtainPairSerializer(data=data)

        # Should raise validation error
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)