from dotenv import load_dotenv
from fastapi import Request, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
import dotenv
import os


load_dotenv()

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

async def get_current_user(request: Request):
    """Extracting the user ID from the token and fetches the Django user."""
    from asgiref.sync import sync_to_async
    try:
        from django.contrib.auth import get_user_model

        # Get token from cookie
        token = request.cookies.get("access_token")
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )

        # Decode the token to get the user's ID
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: int = payload.get("user_id")

            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                )
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        # Fetch user from Django database
        def fetch_user():
            User = get_user_model()
            try:
                return User.objects.get(id=user_id)
            except User.DoesNotExist:
                return None

        user = await sync_to_async(fetch_user)()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return  user

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e

        raise HTTPException(status_code=500, detail=str(e))

