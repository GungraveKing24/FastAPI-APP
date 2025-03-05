from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserCreate(BaseModel):
    user_name: str
    user_email: EmailStr
    user_password: str
    user_role: str = "cliente"

class UserResponse(BaseModel):
    id: int
    user_name: str
    user_email: EmailStr
    user_role: str
    user_register_date: datetime

    class Config:
        from_attributes = True