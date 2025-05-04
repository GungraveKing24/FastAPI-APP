from pydantic import BaseModel
from datetime import datetime

class CommentBase(BaseModel):
    comment_text: str
    comment_rating: int

class CommentCreate(CommentBase):
    pass

class CommentOut(BaseModel):
    user_name: str
    comment_text: str
    comment_rating: int

    class Config:
        from_attributes = True
