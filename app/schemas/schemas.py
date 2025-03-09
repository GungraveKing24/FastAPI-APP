from pydantic import BaseModel, EmailStr
from datetime import datetime

#Configuracion para el registro de los usuarios
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

#Configuracion para el inicio y registro de usuarios
class UserLogin(BaseModel):
    user_email: EmailStr
    user_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

#Configuracoin para el inventario
class InventoryCreate(BaseModel):
    product_name: str
    product_description: str
    product_quantity: int
    product_price: float

class InventoryResponse(BaseModel):
    id: int
    product_name: str
    product_description: str
    product_quantity: int
    product_price: float

    class Config:
        from_attributes = True

