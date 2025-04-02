from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.models import Category
from schemas.s_category import CategoryCreate, CategoryResponse
from config import SessionLocal
from typing import List

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/categories", response_model=CategoryResponse)
async def create_category(category_data: CategoryCreate, db: Session = Depends(get_db)):
    new_category = Category(name_cat=category_data.name_cat)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

@router.get("/categories", response_model=List[CategoryResponse])
async def get_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()
