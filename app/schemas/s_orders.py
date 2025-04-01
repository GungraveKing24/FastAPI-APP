from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class OrderBase(BaseModel):
    order_user_id: int
    order_state: str = "carrito"

class OrderCreate(OrderBase):
    pass

class OrderResponse(OrderBase):
    id: int
    order_date: datetime

    class Config:
        from_attributes = True  # Equivalente a orm_mode = True en versiones anteriores

class OrderDetailBase(BaseModel):
    arrangements_id: int = Field(..., gt=0, description="ID del arreglo floral")
    details_quantity: int = Field(..., gt=0, description="Cantidad debe ser mayor a 0")
    details_price: Optional[float] = Field(None, description="Precio unitario")

class OrderDetailCreate(OrderDetailBase):
    pass

class OrderDetailResponse(OrderDetailBase):
    id: int
    order_id: int
    details_price: float  # Ahora es requerido en la respuesta

    class Config:
        from_attributes = True

class PaymentBase(BaseModel):
    pay_method: str
    pay_amount: float

class PaymentCreate(PaymentBase):
    pass

class PaymentResponse(PaymentBase):
    id: int
    pay_state: str
    pay_date: datetime
    order_id: int

    class Config:
        from_attributes = True