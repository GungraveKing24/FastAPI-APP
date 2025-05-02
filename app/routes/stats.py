from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models.models import Payment, Order
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