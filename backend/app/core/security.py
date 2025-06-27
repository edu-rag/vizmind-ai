import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

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


# Password hashing utilities (if you add direct password auth later)
# from passlib.context import CryptContext
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# def verify_password(plain_password, hashed_password):
#     return pwd_context.verify(plain_password, hashed_password)
# def get_password_hash(password):
#     return pwd_context.hash(password)
