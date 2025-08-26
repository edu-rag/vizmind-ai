from pydantic import BaseModel
from typing import Optional
from app.models.user_models import UserModelInDB  # Assuming user_models.py is created


class TokenData(BaseModel):
    google_id_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_info: UserModelInDB
