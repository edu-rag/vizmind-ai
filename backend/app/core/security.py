import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import httpx

from jose import JWTError, jwt
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

from app.core.config import settings, logger  # Use centralized settings


# JWT Utilities
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


async def verify_google_id_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        id_info = google_id_token.verify_oauth2_token(
            token, google_requests.Request(), settings.GOOGLE_CLIENT_ID
        )
        return id_info
    except ValueError as e:
        logger.error(f"Google ID token verification failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during Google ID token verification: {e}")
        return None


async def verify_google_access_token(access_token: str) -> Optional[Dict[str, Any]]:
    """
    Verify Google access token by fetching user info from Google's userinfo API.
    This is a fallback method if ID token is not available.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={access_token}"
            )
            if response.status_code == 200:
                user_info = response.json()
                # Convert to match ID token format
                return {
                    "sub": user_info.get("id"),
                    "email": user_info.get("email"),
                    "name": user_info.get("name"),
                    "picture": user_info.get("picture"),
                    "email_verified": user_info.get("verified_email", False),
                }
            else:
                logger.error(
                    f"Google access token verification failed with status: {response.status_code}"
                )
                return None
    except Exception as e:
        logger.error(f"Error verifying Google access token: {e}")
        return None


async def verify_google_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify Google token - tries ID token first, then access token as fallback.
    """
    # First try to verify as ID token
    id_token_result = await verify_google_id_token(token)
    if id_token_result:
        return id_token_result

    # If ID token verification fails, try as access token
    logger.info("ID token verification failed, trying as access token")
    access_token_result = await verify_google_access_token(token)
    if access_token_result:
        logger.warning(
            "Using access token verification as fallback - consider updating frontend to use ID tokens"
        )
        return access_token_result

    return None


# Password hashing utilities (if you add direct password auth later)
# from passlib.context import CryptContext
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# def verify_password(plain_password, hashed_password):
#     return pwd_context.verify(plain_password, hashed_password)
# def get_password_hash(password):
#     return pwd_context.hash(password)
