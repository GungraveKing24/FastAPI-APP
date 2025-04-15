from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.models import Arrangement, Category
from schemas.s_arreglos import arrangement_create, ArrangementResponse, arrangment_update
from config import SessionLocal
from services.jwt import get_current_user

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

# Desabilitar el arreglo floral (SOLO ADMIN)
@router.post("/arrangements/{action}/{arrangements_id}")
async def toggle_arrangement_status_test(
    current_user: dict = Depends(get_current_user),
    arrangements_id: int = None,
    action: str = None,
    db: Session = Depends(get_db)
):
    if current_user["user_role"] != "Administrador":
        raise HTTPException(status_code=403, detail="No tienes permiso")
    
    arreglo = db.query(Arrangement).filter(Arrangement.id == arrangements_id).first()
    if not arreglo:
        raise HTTPException(status_code=404, detail="Arreglo no encontrado")
    
    if action == "disable":
            arreglo.arr_availability = False
    elif action == "enable":
        arreglo.arr_availability = True
    else:
        raise HTTPException(status_code=400, detail="Acción no válida. Usa 'disable' o 'enable'.")

    db.commit()
    db.refresh(arreglo)

    return {"message": "Arreglo actualizado exitosamente"}

# Editar arreglos
@router.patch("/arrangements/edit/{arrangements_id}", response_model=ArrangementResponse)
async def edit_arrangement(
    current_user: dict = Depends(get_current_user), 
    arrangements_id: int = None, 
    arrangement_data: arrangment_update = None, 
    db: Session = Depends(get_db)):

    if current_user["user_role"] != "Administrador":
        raise HTTPException(status_code=403, detail="No tienes permiso")
    
    arreglo = db.query(Arrangement).filter(Arrangement.id == arrangements_id).first()
    if not arreglo:
        raise HTTPException(status_code=404, detail="Arreglo no encontrado")
    
    arreglo.arr_name = arrangement_data.arr_name
    arreglo.arr_description = arrangement_data.arr_description
    arreglo.arr_price = arrangement_data.arr_price
    arreglo.arr_img_url = arrangement_data.arr_img_url
    arreglo.arr_id_cat = arrangement_data.arr_id_cat
    arreglo.arr_stock = arrangement_data.arr_stock
    arreglo.arr_discount = arrangement_data.arr_discount

    db.commit()
    db.refresh(arreglo)

    return {"message": "Arreglo actualizado exitosamente"}
