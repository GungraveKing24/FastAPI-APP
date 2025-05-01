from pydantic import EmailStr, Field, constr, BaseModel
from datetime import datetime  # Import datetime correctly
from typing import Optional  # For Optional types

class UserCreate(BaseModel):
    user_name: str
    user_email: EmailStr
    user_password: str
    user_role: str = "Cliente"
    user_direction: str
    user_number: str
    user_url_photo: str = "https://lh3.googleusercontent.com/a/ACg8ocJ_XgiDn5HmUe45E0ZookqVyd2Zu-GlwqSg_wrqNHKM7w4VLYFh=s96-c"
    user_google_id: str = None

class UserLogin(BaseModel):
    user_email: EmailStr
    user_password: str

class UserGoogleAuth(BaseModel):
    token: str
    user_number: str
    user_direction: str

class users_data(BaseModel):
    user_name: str
    user_email: EmailStr
    user_register_date: datetime  # This is now properly typed
    user_number: str
    user_direction: str
    user_url_photo: str
    user_account_state: Optional[bool] = None  # Better way to handle nullable bool
    
    class Config:
        arbitrary_types_allowed = True  # Allow arbitrary types if needed