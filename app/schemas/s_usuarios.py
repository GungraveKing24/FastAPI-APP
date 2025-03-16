from schemas.schemas import BaseModel
from pydantic import EmailStr
from datetime import datetime

class UserCreate(BaseModel):
    user_name: str
    user_email: EmailStr
    user_password: str
    user_role: str = "Cliente"
    user_direction: str = "Santa Ana"
    user_number: str = "12345678"
    user_url_photo: str = "https://avatars.githubusercontent.com/u/111700660?v=4&quot"
    user_google_id: str

class UserResponse(BaseModel):
    id: int
    user_name: str
    user_email: EmailStr
    user_role: str
    user_register_date: datetime
    user_direction: str
    user_number: str
    user_url_photo: str
    user_google_id: str

    class Config:
        from_attributes = True