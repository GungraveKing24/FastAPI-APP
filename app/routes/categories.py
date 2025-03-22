from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.models import Category
from schemas.s_category import Category_create
from config import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/categories")
async def create_category(category_data: Category_create, db: Session = Depends(get_db)):
    new_category = Category(
        name_cat=category_data.name_cat
    )
    db.add(new_category)
    db.commit()
    db.refresh(new_category)