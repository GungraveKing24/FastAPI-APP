from pydantic import BaseModel
from schemas.s_usuarios import UserCreate, UserResponse

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

class CategoryCreate(BaseModel):
    name_Cat: str