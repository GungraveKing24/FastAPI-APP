from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from models.models import OrderDetail, Order, Payment, User, Arrangement
from schemas.s_order_details import OrderDetailResponse, ArrangementInOrder
from config import SessionLocal
from services.jwt import get_current_user
from typing import Optional

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
        order_comments=order.order_comments,
        delivery_address=order.guest_address or order.user.user_direction,
        payment_method=payment.pay_method if payment else "N/A",
        payment_state=payment.pay_state if payment else "N/A",
        total_paid=payment.pay_amount if payment else 0.0,
        arrangements=arrangements
    )

@router.get("/order/user_orders", response_model=list[OrderDetailResponse])
async def get_user_orders(
    user_id: Optional[int] = Query(None),
    guest_email: Optional[str] = Query(None),
    guest_phone: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    
    if current_user["user_role"] != "Administrador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")

    # Obtener las ordenes del usuario
    orders = db.query(Order).filter(
        Order.order_user_id == user_id,
        Order.guest_email == guest_email,
        Order.guest_phone == guest_phone
    ).all()

    # Obtener detalles de las ordenes
    order_details = db.query(OrderDetail).filter(OrderDetail.order_id.in_([order.id for order in orders])).all()

    # Obtener información de los pagos
    payments = db.query(Payment).filter(Payment.order_id.in_([order.id for order in orders])).all()

    # Preparar lista de arreglos en las ordenes
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
    return [
        OrderDetailResponse(
            order_id=order.id,
            order_state=order.order_state,
            order_date=order.order_date,
            order_comments=order.order_comments,
            delivery_address=order.guest_address or order.user.user_direction,
            payment_method=payment.pay_method if payment else "N/A",
            payment_state=payment.pay_state if payment else "N/A",
            total_paid=payment.pay_amount if payment else 0.0,
            arrangements=arrangements
        )
        for order, payment in zip(orders, payments)
    ]