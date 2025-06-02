from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional
import datetime


class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    picture: Optional[HttpUrl] = None


class UserCreate(UserBase):
    google_id: str


class UserUpdate(UserBase):
    pass


class UserModelInDB(UserBase):
    id: str  # MongoDB ObjectId as string
    google_id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True  # Pydantic v2
        # orm_mode = True # Pydantic v1
