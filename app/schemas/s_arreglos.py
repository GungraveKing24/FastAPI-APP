from pydantic import BaseModel
from typing import List

class arrangement_create(BaseModel):
    arr_name: str
    arr_description: str
    arr_price: float
    arr_img_url: str
    arr_id_cat: int
    arr_stock: int
    arr_discount: int

class CategoryBase(BaseModel):
    id: int
    name_cat: str

    class Config:
        from_attributes = True

class ArrangementResponse(BaseModel):
    id: int
    arr_name: str
    arr_description: str
    arr_price: float
    arr_img_url: str
    arr_stock: int
    arr_discount: float | None
    arr_availability: bool
    categories: list[CategoryBase] = []

    class Config:
        from_attributes = True

class arrangment_update(BaseModel):
    arr_name: str | None
    arr_description: str | None
    arr_price: float | None
    arr_img_url: str | None
    arr_stock: int | None
    arr_discount: int | None
    arrangment_update: List[int] | None

    class Config:
        from_attributes = True