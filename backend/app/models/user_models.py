from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional
import datetime


class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    picture: Optional[HttpUrl] = None


class UserModelInDB(UserBase):
    id: str
    google_id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True
