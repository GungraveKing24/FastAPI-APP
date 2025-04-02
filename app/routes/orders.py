from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models.models import Order, OrderDetail, Payment, Arrangement
from schemas.s_orders import OrderDetailCreate, OrderDetailResponse, OrderResponse, GuestOrderCreate
from config import SessionLocal
from services.jwt import get_current_user
from datetime import datetime
from typing import List
import logging

router = APIRouter(prefix='/orders', tags=['Orders'])
logger = logging.getLogger(__name__)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_or_create_cart(db: Session, user_id: int):
    # Obtener o crear el carrito
    cart = db.query(Order).filter(
        Order.order_user_id == user_id, Order.order_state == "carrito"
    ).first()
    
    # Si no hay carrito, crear uno
    if not cart:
        cart = Order(order_user_id=user_id, order_state="carrito", order_total=0)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    
    return cart

def calculate_final_price(arrangement: Arrangement) -> float:
    #Calcular el precio final considerando el descuento
    return arrangement.arr_price * (1 - arrangement.arr_discount / 100)

# Ruta obtener la orden
@router.get("/cart/", response_model=list[OrderResponse])
def get_user_orders(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    # Obtener las ordenes
    return db.query(Order).filter(
        Order.order_user_id == current_user["id"],
        Order.order_state != "carrito"
    ).all()

@router.get("/cart/details/", response_model=list)
def get_orders_details(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    # Obtener el carrito del usuario
    cart = db.query(Order).filter(Order.order_user_id == current_user["id"], Order.order_state == "carrito").first()

    if not cart:
        return []

    # Obtener los detalles del carrito con la información de los arreglos
    cart_details = (
        db.query(
            OrderDetail.id,
            OrderDetail.details_quantity,
            OrderDetail.details_price,
            OrderDetail.discount,
            Arrangement.arr_name,
            Arrangement.arr_img_url,
            Arrangement.arr_price
        )
        .join(Arrangement, OrderDetail.arrangements_id == Arrangement.id)
        .filter(OrderDetail.order_id == cart.id)
        .all()
    )

    # Formatear la respuesta
    print(cart_details) 
    return [
        {
            "id": detail.id,
            "arr_name": detail.arr_name,
            "arr_img_url": detail.arr_img_url,
            "details_quantity": detail.details_quantity,
            "details_price": detail.details_price,
            "discount": detail.discount,
            "final_price": detail.details_price * (1 - detail.discount / 100)
        }
        for detail in cart_details
    ]

# Ruta obtener el detalle de la orden
@router.get("/cart/details/quantity", response_model=int)
def get_user_cart(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    # Obtener detalles del carrito
    cart = get_or_create_cart(db, current_user["id"])
    
    return db.query(OrderDetail).filter(OrderDetail.order_id == cart.id).count()

@router.post("/cart/add", response_model=OrderDetailResponse, status_code=status.HTTP_201_CREATED)
def add_to_cart(item: OrderDetailCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    arrangement = db.query(Arrangement).filter(Arrangement.id == item.arrangements_id).first()
    if not arrangement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arreglo floral no encontrado")
    
    cart = get_or_create_cart(db, current_user["id"])
    final_price = calculate_final_price(arrangement)
    
    order_detail = OrderDetail(
        order_id=cart.id,
        arrangements_id=item.arrangements_id,
        details_quantity=item.details_quantity,
        details_price=final_price
    )
    db.add(order_detail)
    
    payment = db.query(Payment).filter(Payment.order_id == cart.id).first()
    if payment:
        payment.pay_amount = cart.order_total
    
    db.commit()
    db.refresh(order_detail)
    return order_detail

@router.post("/cart/plus/{order_detail_id}", response_model=OrderDetailResponse)
def plus_quantity(order_detail_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = get_or_create_cart(db, current_user["id"])
    item = db.query(OrderDetail).filter(
        OrderDetail.id == order_detail_id, OrderDetail.order_id == cart.id
    ).first()
    
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado en el carrito")
    
    item.details_quantity += 1
    db.commit()
    db.refresh(item)

    return item

@router.delete("/cart/remove/{order_detail_id}")
def remove_from_cart(order_detail_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = get_or_create_cart(db, current_user["id"])
    item = db.query(OrderDetail).filter(
        OrderDetail.id == order_detail_id, OrderDetail.order_id == cart.id
    ).first()
    
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado en el carrito")
    
    cart.order_total = max(0, cart.order_total - (item.details_price * item.details_quantity))
    payment = db.query(Payment).filter(Payment.order_id == cart.id).first()
    if payment:
        payment.pay_amount = cart.order_total
    
    db.delete(item)
    db.commit()
    return {"message": "Producto eliminado del carrito"}

@router.post("/guest/checkout", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_guest_order(guest_order: GuestOrderCreate, db: Session = Depends(get_db)):
    order = Order(
        guest_name=guest_order.guest_name,
        guest_email=guest_order.guest_email,
        guest_phone=guest_order.guest_phone,
        guest_address=guest_order.guest_address,
        order_state="pendiente",  # O el estado que prefieras
        order_date=datetime.utcnow()
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    total_amount = 0

    # Procesar cada producto que se agrega
    for item in guest_order.arrangements:
        arrangement = db.query(Arrangement).filter(Arrangement.id == item.arrangements_id).first()
        if not arrangement:
            db.rollback()
            raise HTTPException(status_code=404, detail=f"Arreglo floral con ID {item.arrangements_id} no encontrado")

        final_price = calculate_final_price(arrangement)
        total_amount += final_price * item.details_quantity

        # Crear detalle de orden
        order_detail = OrderDetail(
            order_id=order.id,
            arrangements_id=item.arrangements_id,
            details_quantity=item.details_quantity,
            details_price=final_price
        )
        db.add(order_detail)

    # Crear el pago
    payment = Payment(
        order_id=order.id,
        pay_method=guest_order.pay_method,
        pay_amount=total_amount,
        pay_state="pendiente"
    )   

    db.add(payment)
    db.commit()
    db.refresh(order)

    return order
