from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials  # Updated import
from typing import Optional

from app.core.config import settings, logger
from app.core.security import (
    jwt,
)  # Assuming jwt for decode is here or directly from jose
from app.models.user_models import UserModelInDB
from app.services.user_service import (
    get_user_by_google_id,
)  # Ensure this is async if called with await

# Define the HTTPBearer scheme instance
# The description will appear in the Swagger UI for this scheme.
auth_scheme = HTTPBearer(
    description="Your JWT Access Token. Prefix with 'Bearer ' if not already included by the client/Swagger."
)


async def get_current_user(
    authorization: Optional[HTTPAuthorizationCredentials] = Depends(
        auth_scheme
    ),  # Use HTTPBearer
) -> UserModelInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token missing",
        headers={
            "WWW-Authenticate": "Bearer"
        },  # Standard header for bearer auth challenges
    )

    if authorization is None or authorization.scheme.lower() != "bearer":
        logger.warning("Authentication attempt with missing or invalid Bearer scheme.")
        raise credentials_exception

    token = authorization.credentials  # This is the actual token string

    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_google_id: Optional[str] = payload.get(
            "sub"
        )  # 'sub' should be the user's unique ID (e.g., google_id)
        if user_google_id is None:
            logger.warning("Token payload missing 'sub' (user identifier).")
            raise credentials_exception
    except jwt.JWTError as e:  # Catch specific JWT errors from python-jose
        logger.warning(f"JWTError during token decode: {e}")
        raise credentials_exception from e
    except Exception as e:  # Catch any other unexpected errors during decode
        logger.error(f"Unexpected error during JWT decode: {e}", exc_info=True)
        raise credentials_exception

    # Retrieve user from DB based on the identifier in the token
    user = await get_user_by_google_id(google_id=user_google_id)
    if user is None:
        logger.warning(f"User with google_id '{user_google_id}' not found in database.")
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: UserModelInDB = Depends(get_current_user),
) -> UserModelInDB:
    # If you had an `is_active` flag on your user model, you'd check it here:
    # if not current_user.is_active:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user
