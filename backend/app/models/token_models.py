from pydantic import BaseModel
from typing import Optional
from app.models.user_models import UserModelInDB  # Assuming user_models.py is created


class TokenData(BaseModel):
    google_id_token: str


class TokenPayload(BaseModel):
    sub: Optional[str] = None  # Subject (user identifier, e.g., google_id)
    email: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_info: UserModelInDB
