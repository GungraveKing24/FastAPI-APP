from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.models import Inventory

from app.config import SessionLocal
from app.schemas.schemas import InventoryCreate, InventoryResponse

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=InventoryResponse)
async def create_inventory(inventory: InventoryCreate, db: Session = Depends(get_db)):
    new_item = Inventory(**inventory.model_dump())
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

@router.get("/", response_model=list[InventoryResponse])
async def get_inventory(db: Session = Depends(get_db)):
    items = db.query(Inventory).all()
    return items
