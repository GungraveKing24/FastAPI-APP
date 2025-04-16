from pydantic import BaseModel

class CategoryCreate(BaseModel):
    name_cat: str

class CategoryResponse(BaseModel):
    id: int
    name_cat: str

    class Config:
        from_attributes = True
