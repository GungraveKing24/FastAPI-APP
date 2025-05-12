from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models.models import OrderDetail, Order, Payment, User, Arrangement
from schemas.s_order_details import OrderDetailResponse, ArrangementInOrder
from config import SessionLocal
from services.jwt import get_current_user

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Para el cliente 
@router.get("/order/details/{order_id}", response_model=OrderDetailResponse)
async def get_user_order_details(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Obtener la orden
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    # Verificación de usuario
    if current_user["user_role"] != "Administrador" and current_user["user_role"] != "Cliente":
        if order.order_user_id != current_user["sub"]:
            raise HTTPException(status_code=403, detail="Acceso denegado")
    
    # Obtener detalles del pedido
    order_details = db.query(OrderDetail).filter(OrderDetail.order_id == order_id).all()

    # Obtener información del pago
    payment = db.query(Payment).filter(Payment.order_id == order_id).first()

    # Preparar lista de arreglos en la orden
    arrangements = []
    for detail in order_details:
        arr = db.query(Arrangement).filter(Arrangement.id == detail.arrangements_id).first()
        arrangements.append(ArrangementInOrder(
            arrangement_name=arr.arr_name,
            arrangement_img_url=arr.arr_img_url,
            quantity=detail.details_quantity,
            price=detail.details_price,
            discount=detail.discount
        ))

    # Construir respuesta
    return OrderDetailResponse(
        order_id=order.id,
        order_state=order.order_state,
        order_date=order.order_date,
        delivery_address=order.guest_address or order.user.user_direction,
        payment_method=payment.pay_method if payment else "N/A",
        payment_state=payment.pay_state if payment else "N/A",
        total_paid=payment.pay_amount if payment else 0.0,
        arrangements=arrangements
    )