from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView


from .views import (
    IndexView,
    LoginView,
    RegisterView,
    UserProfileView,
    LogoutView,
    RefreshTokenView,
    VerifyTokenView,
)

app_name = "users"

urlpatterns = [
    path('', IndexView.as_view(), name="index"),

    # JWT Authentication
    path('api/token/', LoginView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', RefreshTokenView.as_view(), name='token_refresh'),
    path('api/token/verify', VerifyTokenView.as_view(), name='token_verify'),

    # User Management
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/user/', UserProfileView.as_view(), name='user_profile'),
    path('api/logout/', LogoutView.as_view(), name='logout'),

    # Add CSRF token endpoint for Django forms
    path('api/csrf/', lambda request: JsonResponse({'csrfToken': get_token(request)}), name='csrf_token'),
]