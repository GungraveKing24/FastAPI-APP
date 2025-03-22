from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.models import Arrangement, Category
from schemas.s_arreglos import arrangement_create, ArrangementResponse
from config import SessionLocal

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/arrangements/", response_model=list[ArrangementResponse])
async def get_arrangements(db: Session = Depends(get_db)):
    arrangements = db.query(Arrangement).all()
    return arrangements

@router.post("/create/arrangements")
async def create_arrangement(arrangement_data: arrangement_create, db: Session = Depends(get_db)):
    new_arrangement = Arrangement(
        arr_name=arrangement_data.arr_name,
        arr_description=arrangement_data.arr_description,
        arr_price=arrangement_data.arr_price,
        arr_img_url=arrangement_data.arr_img_url,
        arr_id_cat=arrangement_data.arr_id_cat,
        arr_stock=arrangement_data.arr_stock,
        arr_discount=arrangement_data.arr_discount
    )
    db.add(new_arrangement)
    db.commit()
    db.refresh(new_arrangement)
    return {"message": "Arreglo creado exitosamente"}
