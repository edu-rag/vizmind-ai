from fastapi import APIRouter, HTTPException, status, Depends
from app.core.security import create_access_token, verify_google_id_token
from app.services.user_service import create_or_update_user_from_google
from app.models.token_models import TokenData, TokenResponse
from app.models.user_models import UserModelInDB
from app.api.v1.deps import get_current_active_user
from datetime import timedelta
from app.core.config import settings, logger

router = APIRouter()


@router.post("/google", response_model=TokenResponse, tags=["Authentication"])
async def login_with_google(token_data: TokenData):
    logger.info("Received request for Google login.")
    google_user_info = await verify_google_id_token(token_data.google_id_token)
    if not google_user_info:
        logger.warning("Google ID token verification failed.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google ID Token"
        )

    user_google_id = google_user_info.get("sub")
    user_email = google_user_info.get("email")
    user_name = google_user_info.get("name")
    user_picture = google_user_info.get("picture")

    if not user_google_id or not user_email:  # Basic validation
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token missing required fields",
        )

    pydantic_user = await create_or_update_user_from_google(
        google_id=user_google_id,
        email=user_email,
        name=user_name,
        picture=user_picture,
    )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": pydantic_user.google_id,
            "email": pydantic_user.email,
        },
        expires_delta=access_token_expires,
    )
    logger.info(f"User {pydantic_user.email} authenticated successfully via Google.")
    return TokenResponse(
        access_token=access_token, token_type="bearer", user_info=pydantic_user
    )


@router.get("/users/me", response_model=UserModelInDB, tags=["Authentication"])
async def read_users_me(current_user: UserModelInDB = Depends(get_current_active_user)):
    return current_user
