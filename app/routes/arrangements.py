from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from models.models import Arrangement, Category
from schemas.s_arreglos import arrangement_create, ArrangementResponse, arrangment_update
from config import SessionLocal
from services.jwt import get_current_user
from services.cloudinary import upload_file

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/arrangements/", response_model=list[ArrangementResponse])
async def get_all_arrangements(db: Session = Depends(get_db)):
    return db.query(Arrangement).all()

@router.get("/arrangements/by-name/{aarr_name}", response_model=list[ArrangementResponse])
async def get_arrangements_by_name(aarr_name: str, db: Session = Depends(get_db)):
    return db.query(Arrangement).filter(Arrangement.arr_name == aarr_name).all()

@router.post("/create/arrangements")
async def create_arrangement(
        arr_name: str = Form(...),
        arr_description: str = Form(...),
        arr_price: float = Form(...),
        arr_id_cat: int = Form(...),
        arr_stock: int = Form(...),
        arr_discount: int = Form(0),
        image: UploadFile = File(...),
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
    
    # Verificar permisos de administrador
    if current_user["user_role"] != "Administrador":
        raise HTTPException(status_code=403, detail="No tienes permiso")
    
    # Verificar si el arreglo ya existe
    existing_arrangement = db.query(Arrangement).filter(
        Arrangement.arr_name == arr_name  # Use the parameter directly
    ).first()
    
    if existing_arrangement:
        raise HTTPException(status_code=400, detail="El arreglo ya existe")
    
    # Verificar si la categoría existe
    category = db.query(Category).filter(Category.id == arr_id_cat).first()
    if not category:
        raise HTTPException(status_code=400, detail="La categoría no existe")
    
    # Validar que el archivo sea una imagen
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen.")
    
    # Subir la imagen a Cloudinary
    image_url = await upload_file(image)
    if not image_url:
        raise HTTPException(status_code=500, detail="No se pudo subir la imagen.")

    # Crear nuevo arreglo con la URL de Cloudinary
    new_arrangement = Arrangement(
        arr_name=arr_name,  # Use the parameter directly
        arr_description=arr_description,
        arr_price=arr_price,
        arr_img_url=image_url,
        arr_id_cat=arr_id_cat,
        arr_stock=arr_stock,
        arr_discount=arr_discount
    )
    
    db.add(new_arrangement)
    try:
        db.commit()
        db.refresh(new_arrangement)
        return {"message": "Arreglo creado exitosamente", "data": new_arrangement}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear el arreglo: {str(e)}")

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

# Obtener un arreglo por ID
@router.get("/arrangements/{arrangements_id}", response_model=ArrangementResponse)
async def get_arrangement(arrangements_id: int, db: Session = Depends(get_db)):
    return db.query(Arrangement).filter(Arrangement.id == arrangements_id).first()

# Editar arreglos
@router.patch("/arrangements/edit/{arrangements_id}", response_model=ArrangementResponse)
async def edit_arrangement(
    arrangements_id: int,
    arr_name: str = Form(None),
    arr_description: str = Form(None),
    arr_price: float = Form(None),
    arr_id_cat: int = Form(None),
    arr_stock: int = Form(None),
    arr_discount: int = Form(None),
    image: UploadFile = File(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza parcialmente un arreglo floral.
    Solo los campos proporcionados serán actualizados.
    """
    # Verificar permisos
    if current_user["user_role"] != "Administrador":
        raise HTTPException(status_code=403, detail="No tienes permiso")
    
    # Buscar el arreglo
    arreglo = db.query(Arrangement).filter(Arrangement.id == arrangements_id).first()
    if not arreglo:
        raise HTTPException(status_code=404, detail="Arreglo no encontrado")
    
    # Actualizar campos proporcionados
    if arr_name is not None:
        arreglo.arr_name = arr_name
    if arr_description is not None:
        arreglo.arr_description = arr_description
    if arr_price is not None:
        arreglo.arr_price = arr_price
    if arr_id_cat is not None:
        arreglo.arr_id_cat = arr_id_cat
    if arr_stock is not None:
        arreglo.arr_stock = arr_stock
    if arr_discount is not None:
        arreglo.arr_discount = arr_discount
    
    # Manejar imagen si se proporciona
    if image:
        if not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="El archivo debe ser una imagen")
        
        image_url = await upload_file(image)
        if not image_url:
            raise HTTPException(status_code=500, detail="Error al subir la imagen")
        
        arreglo.arr_img_url = image_url
    
    try:
        db.commit()
        db.refresh(arreglo)
        return arreglo
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar: {str(e)}")