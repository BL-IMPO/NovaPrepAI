from typing import Optional

from rest_framework.request import Request
from rest_framework_simplejwt.authentication import JWTAuthentication, AuthUser
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import Token


class CustomCookieAuthentication(JWTAuthentication):
    def authenticate(self, request):
        print("\n=== 🕵️ AUTH DEBUG START ===")

        # 1. Check what cookies Django ACTUALLY received
        print(f"ALL INCOMING COOKIES: {request.COOKIES}")

        raw_token = request.COOKIES.get('access_token')
        print(f"ACCESS TOKEN FOUND: {bool(raw_token)}")

        if raw_token is None:
            print("No cookie found. Falling back to header authentication...")
            result = super().authenticate(request)
            print("=== AUTH DEBUG END ===\n")
            return result

        # 2. If cookie exists, try to validate it
        try:
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)

            print(f"✅ SUCCESS! User Authenticated: {user.username}")
            print("=== AUTH DEBUG END ===\n")

            return user, validated_token

        except Exception as e:
            print(f"❌ TOKEN REJECTED! Reason: {str(e)}")
            print("=== AUTH DEBUG END ===\n")
            return None