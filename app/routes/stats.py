from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.models import Payment, Order, Arrangement, Category, OrderDetail, User
from config import SessionLocal
from services.jwt import get_current_user

from datetime import datetime, timedelta

router = APIRouter(prefix="/stats", tags=["Estadísticas"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 

@router.get("/week-sales")
async def GetWeekSales(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["user_role"] != "Administrador":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autorizado")

    hace_7_dias = datetime.utcnow() - timedelta(days=7)
    pagos = db.query(Payment).filter(Payment.pay_date >= hace_7_dias, Payment.pay_state == "completado").all()
    total = sum(p.pay_amount for p in pagos)
    return {"monto_total": total, "cantidad_pedidos": len(pagos)}

@router.get("/month-sales")
async def GetMonthSales(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):    
    if current_user["user_role"] != "Administrador":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autorizado")

    hace_30_dias = datetime.utcnow() - timedelta(days=30)
    pagos = db.query(Payment).filter(Payment.pay_date >= hace_30_dias, Payment.pay_state == "completado").all()
    total = sum(p.pay_amount for p in pagos)
    return {"monto_total": total, "cantidad_pedidos": len(pagos)}

@router.get("/cancelled-orders")
async def GetCancelledOrders(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["user_role"] != "Administrador":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autorizado")

    pedidos = db.query(Order).filter(Order.order_state == "cancelado").all()
    ahora = datetime.utcnow()
    cancelaciones = [
        p for p in pedidos if (ahora - p.order_date) > timedelta(hours=1)
    ]
    return {"total": len(cancelaciones)}

@router.get("/client-count")
async def get_client_count(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["user_role"] != "Administrador":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autorizado")
    
    client_count = db.query(User).filter(User.user_role == "Cliente").count()
    return {"total_clientes": client_count}

@router.get("/top-categories")
async def get_top_categories(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["user_role"] != "Administrador":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autorizado")
    
    # Consulta para obtener las 5 categorías más vendidas
    top_categories = db.query(
        Category.name_cat,
        func.sum(OrderDetail.details_quantity).label("total_quantity")
    ).join(Arrangement, Arrangement.arr_id_cat == Category.id)\
    .join(OrderDetail, OrderDetail.arrangements_id == Arrangement.id)\
    .join(Order, Order.id == OrderDetail.order_id)\
    .filter(Order.order_state == "completado")\
    .group_by(Category.name_cat)\
    .order_by(func.sum(OrderDetail.details_quantity).desc())\
    .limit(5)\
    .all()
    
    return [{"categoria": cat[0], "cantidad": cat[1]} for cat in top_categories]

@router.get("/top-arrangements")
async def get_top_arrangements(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["user_role"] != "Administrador":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autorizado")
    
    # Consulta para obtener los 5 arreglos más vendidos
    top_arrangements = db.query(
        Arrangement.arr_name,
        func.sum(OrderDetail.details_quantity).label("total_quantity")
    ).join(OrderDetail, OrderDetail.arrangements_id == Arrangement.id)\
    .join(Order, Order.id == OrderDetail.order_id)\
    .filter(Order.order_state == "completado")\
    .group_by(Arrangement.arr_name)\
    .order_by(func.sum(OrderDetail.details_quantity).desc())\
    .limit(5)\
    .all()
    
    return [{"arreglo": arr[0], "cantidad": arr[1]} for arr in top_arrangements]