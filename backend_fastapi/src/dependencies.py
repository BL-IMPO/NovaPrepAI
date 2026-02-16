from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
import dotenv
import os


load_dotenv()

# This tells FastAPI to look for a "Bearer" token in the Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Extracting the user ID from the token and fetches the Django user."""
    from asgiref.sync import sync_to_async
    try:
        from django.contrib.auth import get_user_model

        # 1. Decode the token to get the user's ID
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")

        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")

        # 2. Fetch the actual user from the Django database
        def fetch_user():
            User = get_user_model()
            try:
                return User.objects.get(id=user_id)
            except User.DoesNotExist:
                return None

        user = await sync_to_async(fetch_user)()

        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        return user

    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
