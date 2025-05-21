from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session, joinedload
from models.models import Order, OrderDetail, Payment, Arrangement, User
from schemas.s_orders import OrderDetailCreate, OrderDetailResponse, OrderResponse, GuestOrderCreate, OrderAdminResponse, OrderDetailSchema
from schemas.s_payment import PaymentLinkResponse
from config import SessionLocal
from services.jwt import get_current_user
from services.wompi import create_payment_link
from services.messages import send_email
from datetime import datetime
import logging, uuid

router = APIRouter(prefix='/orders')
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
        cart = Order(order_user_id=user_id, order_state="carrito")
        db.add(cart)
        db.commit()
        db.refresh(cart)
    
    return cart

def calculate_final_price(arrangement: Arrangement) -> float:
    #Calcular el precio final considerando el descuento
    return arrangement.arr_price * (1 - arrangement.arr_discount / 100)

# Ruta obtener la orden
@router.get("/cart/", response_model=list[dict])
def get_user_orders(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    # Obtener las ordenes
    orders = db.query(Order).filter(
        Order.order_user_id == current_user["id"],
        Order.order_state != "carrito"
    ).options(joinedload(Order.order_details)).all()

    return [
        {
            "id": order.id,
            "order_date": order.order_date.strftime("%Y-%m-%d %H:%M:%S"),
            "order_total": sum(detail.details_quantity * detail.details_price for detail in order.order_details),
            "order_state": order.order_state
        }
        for order in orders
    ]

@router.get("/cart/details/", response_model=list)
def get_orders_details(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    # Obtener el carrito del usuario
    if current_user["user_role"] == "Administrador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")

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

@router.get("/cart/order_details/{order_id}", response_model=list[OrderDetailSchema])
def get_order_details(order_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    # Verificar que sea el usuario que creo la solicitud
    user_order = db.query(Order).filter(Order.id == order_id and Order.order_user_id == current_user["id"]).first()
    if not user_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orden no encontrada")
    else:
        cart = db.query(OrderDetail).filter(OrderDetail.order_id == order_id).all()
        return cart

# Ruta obtener el detalle de la orden
@router.get("/cart/details/quantity", response_model=int)
def get_user_cart(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    # Obtener detalles del carrito
    if current_user["user_role"] == "Administrador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")

    cart = get_or_create_cart(db, current_user["id"])
    
    return db.query(OrderDetail).filter(OrderDetail.order_id == cart.id).count()

@router.post("/cart/add", response_model=OrderDetailResponse, status_code=status.HTTP_201_CREATED)
def add_to_cart(item: OrderDetailCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):

    if current_user["user_role"] == "Administrador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")
    
    arrangement = db.query(Arrangement).filter(Arrangement.id == item.arrangements_id).first()
    if not arrangement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arreglo floral no encontrado")
    
    cart = get_or_create_cart(db, current_user["id"])
    final_price = calculate_final_price(arrangement)
    
    # Verificar si el producto ya está en el carrito
    existing_item = db.query(OrderDetail).filter(
        OrderDetail.order_id == cart.id,
        OrderDetail.arrangements_id == item.arrangements_id
    ).first()

    if existing_item:
        # Si ya existe, incrementa la cantidad en lugar de agregar un nuevo registro
        existing_item.details_quantity += 1
        db.commit()
        db.refresh(existing_item)
        return existing_item
    else:
        order_detail = OrderDetail(
            order_id=cart.id,
            arrangements_id=item.arrangements_id,
            details_quantity=item.details_quantity,
            details_price=final_price
        )
        db.add(order_detail)
        db.commit()
        db.refresh(order_detail)
    return order_detail

#Procesar el pago final
@router.post("/cart/complete/", response_model=OrderResponse)
def complete_order(order_data: dict = Body(...),db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    # Obtener la orden
    order = db.query(Order).filter(
        Order.order_user_id == current_user["id"],
        Order.order_state == "carrito"
    ).first()

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orden no encontrada")

    if order.order_state == "procesado":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La orden ya ha sido procesada")

    # Actualizar comentarios si vienen en order_data
    if order_data.get("notes"):
        order.order_comments = order_data["notes"]

    order.order_state = "procesado"
    order.order_date = datetime.utcnow()

    total_amount = sum(
        detail.details_quantity * (db.query(Arrangement).filter(Arrangement.id == detail.arrangements_id).first().arr_price * (1 - detail.discount / 100))
        for detail in order.order_details
    )

    payment = Payment(
        order_id=order.id,
        pay_method="Efectivo",
        pay_amount=total_amount,
        pay_state="pendiente"
    )

    db.add(payment)
    db.flush()  # Para obtener el ID del pago antes del commit

    order.payment_id = payment.id
    db.commit()
    db.refresh(order)

    return order

@router.post("/cart/plus/{order_detail_id}", response_model=OrderDetailResponse)
def plus_quantity(order_detail_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):

    if current_user["user_role"] == "Administrador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")

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

@router.post("/cart/minus/{order_detail_id}", response_model=OrderDetailResponse)
def minus_quantity(order_detail_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):

    if current_user["user_role"] == "Administrador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")

    cart = get_or_create_cart(db, current_user["id"])
    item = db.query(OrderDetail).filter(
        OrderDetail.id == order_detail_id, OrderDetail.order_id == cart.id
    ).first()
    
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado en el carrito")
    
    if item.details_quantity > 1:
        item.details_quantity -= 1
        db.commit()
        db.refresh(item)
    
    return item

@router.delete("/cart/remove/{order_detail_id}")
def remove_from_cart(order_detail_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):

    if current_user["user_role"] == "Administrador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")

    cart = get_or_create_cart(db, current_user["id"])
    item = db.query(OrderDetail).filter(
        OrderDetail.id == order_detail_id, OrderDetail.order_id == cart.id
    ).first()
    
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado en el carrito")
    
    db.delete(item)
    db.commit()
    return {"message": "Producto eliminado del carrito"}

@router.get("/admin/cart/", response_model=list[OrderAdminResponse])   
def get_admin_cart(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user["user_role"] != "Administrador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")

    # Query orders that are not in "carrito" state
    orders = db.query(Order).filter(
        Order.order_state != "carrito"
    ).all()
    
    if not orders:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontraron órdenes")
    
    # Prepare the response data
    response = []
    for order in orders:
        # Get user details if it's not a guest order
        user_name = order.guest_name or (order.user.user_name if order.user else "N/A")
        user_email = order.guest_email or (order.user.user_email if order.user else "N/A")
        user_phone = order.guest_phone or (order.user.user_number if order.user else "N/A")
        
        # Calculate total amount from order details
        total = sum(
            detail.details_quantity * detail.details_price * (1 - detail.discount/100) 
            for detail in order.order_details
        )
        
        response.append({
            "id": order.id,
            "name": user_name,
            "email": user_email,
            "phone": user_phone,
            "Date": order.order_date.strftime("%d/%m/%Y"),
            "totalSpent": f"{total:.2f}",
            "status": order.order_state,
            # Add any other fields you need for the frontend
        })
    
    return response

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

@router.post("/payments/create/", response_model=PaymentLinkResponse)
async def create_payment(
    order_data: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # 1. Verificar autenticación y permisos
        logger.info("\n=== Datos del usuario ===")
        logger.info(f"ID Usuario: {current_user.get('id')}")
        logger.info(f"Rol Usuario: {current_user.get('user_role')}")
        
        if current_user["user_role"] != "Cliente":
            raise HTTPException(status_code=403, detail="Acceso denegado")

        # 2. Obtener usuario de la base de datos
        user = db.query(User).filter(User.id == current_user["id"]).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        logger.info(f"\nUsuario DB: {user.user_name} ({user.user_email})")

        # 3. Obtener el carrito del usuario
        order = db.query(Order).filter(
            Order.order_user_id == user.id,
            Order.order_state == "carrito"
        ).first()

        if not order:
            raise HTTPException(status_code=404, detail="No tienes un carrito activo")
        
        # Actualizar el comntario de la orden
        if order_data.get("notes"):
            order.order_comments = order_data["notes"]
            db.commit()  # Guardar los comentarios inmediatamente

        logger.info(f"\n=== Datos del carrito ===")
        logger.info(f"ID Orden: {order.id}")
        logger.info(f"Estado: {order.order_state}")
        logger.info(f"Fecha: {order.order_date}")

        # 4. Obtener detalles del carrito
        order_details = db.query(OrderDetail).filter(
            OrderDetail.order_id == order.id
        ).all()

        if not order_details:
            raise HTTPException(status_code=400, detail="El carrito está vacío")

        logger.info("\n=== Productos en el carrito ===")
        total = 0.0
        for i, detail in enumerate(order_details, 1):
            arrangement = db.query(Arrangement).filter(
                Arrangement.id == detail.arrangements_id
            ).first()
            
            logger.info(f"\nProducto #{i}:")
            logger.info(f"ID: {detail.arrangements_id}")
            logger.info(f"Nombre: {arrangement.arr_name if arrangement else 'No encontrado'}")
            logger.info(f"Cantidad: {detail.details_quantity}")
            logger.info(f"Precio unitario: ${detail.details_price}")
            logger.info(f"Descuento: {detail.discount}%")
            
            final_price = detail.details_price * (1 - (detail.discount / 100))
            subtotal = final_price * detail.details_quantity
            total += subtotal
            logger.info(f"Subtotal: ${subtotal:.2f}")

        logger.info(f"\nTOTAL DEL CARRITO: ${total:.2f}")
        logger.info("\n=== Datos recibidos del frontend ===")
        logger.info(order_data)

        # Crear nuevo pago siempre con nueva referencia
        reference = f"ORD-{order.id}-{uuid.uuid4().hex[:6]}"
        
        descripcion_productos = []
        for detail in order_details:
            arrangement = db.query(Arrangement).filter(Arrangement.id == detail.arrangements_id).first()
            if arrangement:
                final_price = detail.details_price * (1 - (detail.discount / 100))
                descripcion_productos.append(
                    f"{detail.details_quantity}x {arrangement.arr_name} (${final_price:.2f} c/u)"
                )

        descripcion = " | ".join(descripcion_productos)
        if len(descripcion) > 240:  # Limitar descripción para Wompi
            descripcion = descripcion[:237] + "..."

        try:
            enlace_pago = await create_payment_link(
                amount=total,
                description=descripcion or "Compra de arreglos florales",                
                reference=reference,
                customer_email=user.user_email
            )

            logger.info("\n=== Respuesta de Wompi ===")
            logger.info(enlace_pago)

            # Marcar pagos anteriores como expirados
            db.query(Payment).filter(
                Payment.order_id == order.id,
                Payment.pay_state.in_(["pendiente", "procesando"])
            ).update({"pay_state": "expirado"})

            # Crear nuevo registro de pago
            payment = Payment(
                order_id=order.id,
                pay_method="Tarjeta",
                pay_amount=total,
                pay_state="procesando",
                pay_transaction_id=reference,
                pay_date=datetime.utcnow()
            )
            
            db.add(payment)
            db.commit()

            return {
                "payment_url": enlace_pago.get("urlEnlace") or enlace_pago.get("urlEnlaceLargo"),
                "reference": reference,
                "amount": total,
                "idEnlace": enlace_pago.get("idEnlace"),
                "urlQrCodeEnlace": enlace_pago.get("urlQrCodeEnlace"),
                "estaProductivo": enlace_pago.get("estaProductivo")
            }

        except Exception as e:
            db.rollback()
            logger.error(f"\n!!! Error al crear pago: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"No se pudo crear el enlace de pago: {str(e)}"
            )

    except HTTPException as he:
        logger.error(f"\n!!! Error controlado: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"\n!!! Error inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.post("/order/cancel/{order_id}")
async def cancel_order(order_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user["user_role"] != "Cliente":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Acceso denegado")

    orden_cancelar =  db.query(Order).filter(Order.id == order_id).first()
    if not orden_cancelar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orden no encontrada")

    if orden_cancelar.order_state == "cancelado":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La orden ya ha sido cancelada")
    
    if orden_cancelar.order_state == "completado":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La orden ya ha sido completada y no se puede cancelar")

    orden_cancelar.order_state = "cancelado"
    db.commit()

    return {"message": "Orden cancelada"}

@router.post("/change/order_state/{order_id}")
async def change_order_state(
    order_id: int,
    new_state: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_role"] != "Administrador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orden no encontrada")

    if order.order_state in ["cancelado", "completado"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La orden ya ha sido {order.order_state}"
        )

    if order.order_user_id:
        user = db.query(User).filter(User.id == order.order_user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        user_email = user.user_email
    else:
        if not order.guest_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email del invitado no disponible")
        user_email = order.guest_email

    try:
        # Obtener los detalles
        detalles = db.query(OrderDetail).filter(OrderDetail.order_id == order.id).all()
        productos_html = ""

        for detalle in detalles:
            producto = db.query(Arrangement).filter(Arrangement.id == detalle.arrangements_id).first()
            if producto:
                productos_html += f"<li><strong>{producto.arr_name}</strong> - Cantidad: {detalle.details_quantity}</li>"

        # Actualizar estado
        order.order_state = new_state
        db.commit()

        # HTML del correo
        html_content = f"""
        <div style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px;">
            <div style="max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 8px;">
                <img src="https://res.cloudinary.com/dnwggo6kz/image/upload/v1747847292/ArreglitosSV_jxbbms.png" alt="ArreglistoSV" style="width: 150px; display: block; margin: auto;" />
                <h2 style="text-align: center; color: #2d2d2d;">Estado de tu pedido actualizado</h2>
                <p>Hola,</p>
                <p>Queremos informarte que el estado de tu pedido ha sido actualizado a:</p>
                <p style="font-size: 18px; font-weight: bold; color: #007b5e;">{new_state.upper()}</p>
                <p>Detalles de tu pedido:</p>
                <ul>{productos_html}</ul>
                <p>Gracias por confiar en <strong>ArreglistoSV</strong>.</p>
                <hr />
                <p style="font-size: 12px; color: gray;">Este es un correo automático, por favor no responder.</p>
            </div>
        </div>
        """

        # Enviar email
        email_result = await send_email(
            to=user_email,
            subject="📦 Actualización de tu pedido - ArreglistoSV",
            html_body=html_content
        )

        if "error" in email_result:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al enviar el email de notificación")

        return {"message": "Estado de la orden cambiado correctamente"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al cambiar el estado de la orden: {str(e)}")

# Notificaciones
@router.get("/notifications/orders")
async def notification_orders(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user["user_role"] != "Administrador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")

    # Get approved orders with their payments (Clientes y invitados)
    orders = db.query(Order).filter(Order.order_state != "carrito" or Order.order_state != "completado").all()

    if not orders:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontraron ordenes")

    response = []
    for order in orders:
        payment = db.query(Payment).filter(Payment.order_id == order.id).first()
        response.append({
            "id": order.id,
            "order_id": order.id,
            "order_state": order.order_state,
            "order_date": order.order_date.isoformat() if order.order_date else None,
            "customer": order.guest_name or (order.user.user_name if order.user else "Cliente no registrado"),
            "pay_method": payment.pay_method if payment else "No especificado",
            "pay_amount": payment.pay_amount if payment else 0,
            "read": False  # Default unread status
        })

    return response