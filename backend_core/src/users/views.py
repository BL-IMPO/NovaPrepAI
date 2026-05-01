from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import TemplateView
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import QueryDict
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.core.cache import cache

from main.models import TestAttempt
from users.models import UserProfile
from api.serializer import (
    CustomTokenObtainPairSerializer,
    UserSerializer,
    RegisterSerializer,
    TestAttemptSerializer,
    ContactUsSerializer
)


class IndexView(TemplateView):
    template_name = 'index.html'

@method_decorator(csrf_protect, name='dispatch')
class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        # Accept both email and username fields
        if 'email' in request.data and 'username' not in request.data:
            if isinstance(request.data, QueryDict):
                request.data._mutable = True
                request.data['username'] = request.data['email']
                request.data._mutable = False
            else:
                request.data['username'] = request.data['email']

        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            # Add redirect URL
            response.data['redirect_url'] = '/dashboard'

            # Set cookie for server-side rendering (optional)
            access_token = response.data['access']
            refresh_token = response.data['refresh']

            response.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,
                secure=True,
                samesite='Strict',
                max_age=4 * 60 * 60
            )

            response.set_cookie(
                key='refresh_token',
                value=refresh_token,
                httponly=True,
                secure=True,
                samesite='Strict',
                max_age=7 * 24 * 60 * 60 # 7 days
            )

        return response

@method_decorator(csrf_protect, name='dispatch')
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        #if 'email' in request.data and 'username' not in request.data:
        #    request.data._mutable = True
        #    request.data['username'] = request.data['email']
        #    request.data._mutable = False

        # Generate tokens for auto-login
        refresh = RefreshToken.for_user(user)

        # Get user data
        user_data = UserSerializer(user).data

        response_data = {
            'success': True,
            'message': 'User registered successfully',
            'user': user_data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'redirect_url': '/dashboard/'
        }



        # Set cookies
        response = Response(response_data, status=status.HTTP_201_CREATED)
        response.set_cookie(
            key='access_token',
            value=str(refresh.access_token),
            httponly=True,
            secure=True,
            samesite='Strict',
            max_age=4 * 60 * 60
        )

        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            secure=True,
            samesite='Strict',
            max_age=7 * 24 * 60 * 60
        )

        return response

@method_decorator(csrf_protect, name='dispatch')
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)

    def patch(self, request):
        user = request.user

        if 'first_name' in request.data:
            user.first_name = request.data['first_name']
        if 'last_name' in request.data:
            user.last_name = request.data['last_name']
        if 'email' in request.data:
            user.email = request.data['email']
        user.save()

        # Update UserProfile model fields
        # Ensure profile exists
        if not hasattr(user, 'userprofile'):
            UserProfile.objects.create(user=user)

        profile = user.userprofile

        if 'nickname' in request.data:
            profile.nickname = request.data['nickname']

        if 'avatar' in request.data:
            profile.avatar = request.data['avatar']

        profile.save()

        serializer = UserSerializer(user)
        return Response(serializer.data)

@method_decorator(csrf_protect, name='dispatch')
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh') or request.COOKIES.get('refresh_token')

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception:
                pass

        response = Response({'success': True, 'message': 'Logged out'})
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response



class RefreshTokenView(TokenRefreshView):
    def post(self, request, *args, **kwargs):

        if 'refresh' not in request.data and request.COOKIES.get('refresh_token'):
            if hasattr(request.data, '_mutable'):
                request.data._mutable = True
            request.data['refresh'] = request.COOKIES['refresh_token']
            if hasattr(request.data, '_mutable'):
                request.data._mutable = False

        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            # Update access token cookie
            response.set_cookie(
                key='access_token',
                value=response.data['access'],
                httponly=True,
                secure=True,
                samesite='Strict',
                max_age=4 * 60 * 60
            )

        return response


# Token verification endpoint
class VerifyTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'valid': True,
            'user': UserSerializer(request.user).data
        })


class UserTestHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        attempts = TestAttempt.objects.filter(user=request.user).order_by('-id')
        serializer = TestAttemptSerializer(attempts, many=True)
        return Response(serializer.data)

class ContactMessageView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ContactUsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Your message has been sent.'
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StreakTestsTaken(APIView):
    permission_classes = [IsAuthenticated]

    # Example of date 2026-03-18 14:43:29.282586+00
    def get(self, request):
        from django.utils import timezone

        cache_key = f"user_streak_{request.user.id}"

        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        today = timezone.now().date()

        test_dates = list(TestAttempt.objects.filter(user=request.user).dates('created_at', 'day', order='DESC'))

        streak = 0
        daily_streak = False

        if test_dates:
            most_recent_test = test_dates[0]

            if most_recent_test in [today, today - timedelta(days=1)]:

                if most_recent_test == today:
                    daily_streak = True

                target_date = most_recent_test

                for test_date in test_dates:
                    if test_date == target_date:
                        streak += 1
                        target_date -= timedelta(days=1)
                    else:
                        break

        response_data = {
            "streak": streak,
            "daily_streak": daily_streak
        }

        cache.set(cache_key, response_data, timeout=86400)

        return Response(response_data)
