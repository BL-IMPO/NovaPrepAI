from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, AuthUser
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import Token


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user: AuthUser) -> Token:
        token = super().get_token(user)

        # Add custom claims
        token['username'] = user.username
        token['email'] = user.email
        token['first_name'] = user.first_name

        return token

    def validate(self, attrs):
        # Use email instead of username for authentication
        email = attrs.get('email')
        password = attrs.get('password')

        if email:
            try:
                user = User.objects.get(email=email)
                attrs['username'] = user.username
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    'No account found with this email address.'
                )

        data = super().validate(attrs)

        # Include user data in response
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
        }

        return data


class UserSerializer(serializers.ModelSerializer):
    # Fields from related profile
    nickname = serializers.CharField(source='userprofile.nickname', read_only=True)
    avatar = serializers.ImageField(source='userprofile.avatar', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined', 'nickname', 'avatar']
        read_only_fields = ['id', 'date_joined']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    full_name = serializers.CharField(write_only=True, required=True)
    nickname = serializers.CharField(write_only=True, required=False)
    # Add newsletter field
    subscribe_newsletter = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = User
        # Add subscribe_newsletter to fields
        fields = ['email', 'password', 'password2', 'full_name', 'nickname', 'subscribe_newsletter']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "User with this email already exists."})

        return attrs

    def create(self, validated_data):
        # Extract all fields
        full_name = validated_data.pop('full_name')
        nickname = validated_data.pop('nickname', '')
        subscribe_newsletter = validated_data.pop('subscribe_newsletter', False)
        password2 = validated_data.pop('password2')

        # Split full name
        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        # Create user
        user = User.objects.create(
            username=validated_data['email'],
            email=validated_data['email'],
            first_name=first_name,
            last_name=last_name,
            is_active=True,
        )

        user.set_password(validated_data['password'])
        user.save()

        # TODO: Create user profile with nickname and newsletter if needed
        # For now, you can store newsletter in a UserProfile model
        # profile = UserProfile.objects.create(user=user, nickname=nickname, subscribe_newsletter=subscribe_newsletter)

        return user

# TO DO
# Create user profile with nickname if needed
# profile = UserProfile.objects.create(user=user, nickname=nickname)