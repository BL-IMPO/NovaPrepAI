from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.urls import path
from django.views.generic import TemplateView
from rest_framework_simplejwt.views import TokenRefreshView


from .views import (
    IndexView,
    LoginView,
    RegisterView,
    UserProfileView,
    LogoutView,
    RefreshTokenView,
    VerifyTokenView,
    UserTestHistoryView,
)

app_name = "users"

urlpatterns = [
    # Pages for tests
    path('', IndexView.as_view(), name="index"),
    path('login.html', TemplateView.as_view(template_name='login.html'), name='login'),
    path('registration.html', TemplateView.as_view(template_name='registration.html'), name='registration'),
    path('profile.html', TemplateView.as_view(template_name='profile.html'), name='profile'),
    path('dashboard/', TemplateView.as_view(template_name='index.html'), name='dashboard'),

    # API Endpoints
    # JWT Authentication
    path('api/token/', LoginView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', RefreshTokenView.as_view(), name='token_refresh'),
    path('api/token/verify', VerifyTokenView.as_view(), name='token_verify'),

    # User Management
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/user/', UserProfileView.as_view(), name='user_profile'),
    path('api/logout/', LogoutView.as_view(), name='logout'),
    path('api/user/tests/', UserTestHistoryView.as_view(), name='user-tests'),

    # Add CSRF token endpoint for Django forms
    path('api/csrf/', lambda request: JsonResponse({'csrfToken': get_token(request)}), name='csrf_token'),
]