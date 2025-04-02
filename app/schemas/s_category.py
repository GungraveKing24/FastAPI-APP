from pydantic import BaseModel

class CategoryCreate(BaseModel):
    name_cat: str

class CategoryResponse(BaseModel):
    name_cat: str

    class Config:
        from_attributes = True
