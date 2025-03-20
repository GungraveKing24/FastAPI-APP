from pydantic import EmailStr, Field, constr, BaseModel

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