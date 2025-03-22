from pydantic import BaseModel

class arrangement_create(BaseModel):
    arr_name: str
    arr_description: str
    arr_price: float
    arr_img_url: str
    arr_id_cat: int
    arr_stock: int
    arr_discount: int

class ArrangementResponse(BaseModel):
    id: int
    arr_name: str
    arr_description: str
    arr_price: float
    arr_img_url: str
    arr_id_cat: int
    arr_stock: int
    arr_discount: float | None

    class Config:
        from_attributes = True