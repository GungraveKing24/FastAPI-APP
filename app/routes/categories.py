from fastapi import APIRouter, Depends, HTTPException, Path, Body
from sqlalchemy.orm import Session
from models.models import Category
from schemas.s_category import CategoryCreate, CategoryResponse
from config import SessionLocal
from typing import List
from services.jwt import get_current_user

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/categories", response_model=CategoryResponse)
async def create_category(category_data: CategoryCreate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    # Verificar permisos de administrador
    if current_user["user_role"] != "Administrador":
        raise HTTPException(status_code=403, detail="No tienes permiso")

    # Verificar si la categoría ya existe
    existing_category = db.query(Category).filter(
        Category.name_cat == category_data.name_cat
    ).first()
    
    if existing_category:
        raise HTTPException(status_code=400, detail="La categoría ya existe")
    
    # Crear nueva categoría
    new_category = Category(name_cat=category_data.name_cat)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

@router.get("/categories", response_model=List[CategoryResponse])
async def get_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()


@router.patch("/categories/{categories_id}", response_model=CategoryResponse)
async def edit_category(
    categories_id: int = Path(..., description="ID de la categoría a editar"),
    category_data: CategoryCreate = Body(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user["user_role"] != "Administrador":
        raise HTTPException(status_code=403, detail="No tienes permiso")
    
    category = db.query(Category).filter(Category.id == categories_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    category.name_cat = category_data.name_cat
    db.commit()
    db.refresh(category)
    return category