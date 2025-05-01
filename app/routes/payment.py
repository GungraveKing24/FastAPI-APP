from fastapi import APIRouter, Depends, HTTPException, status, logger, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from models.models import Payment, Order
from config import SessionLocal, WOMPI_URL
from services.jwt import get_current_user
from services.wompi import create_payment_link, create_token
from datetime import datetime
import uuid, httpx

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/payment/create")
async def create_wompi_payment(
        order_data: dict
    ):
    
    # Validar datos de la orden
    if not order_data.get("amount") or order_data["amount"] <= 0:
        raise HTTPException(status_code=400, detail="Monto inválido")
    
    # Crear referencia única
    reference = f"ORD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"
    
    try:
        payment_link = await create_payment_link(
            amount=order_data["amount"],
            description="Compra de arreglos florales",
            reference=reference,
            customer_email=order_data["email"]
        )
        
        # Guardar la referencia en tu base de datos
        # ... código para guardar ...
        
        return {"payment_url": payment_link["url"]}
    except Exception as e:
        print(f"Payment creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="No se pudo crear el pago")
    
@router.get("/payments/verify")
async def verify_payment(
    reference: str = Query(..., description="Referencia de la transacción"),
    transaction_id: str = Query(None, description="ID de transacción de Wompi"),
    db: Session = Depends(get_db)
):
    try:
        # 1. Buscar la orden en tu base de datos
        order = db.query(Order).filter(Order.reference == reference).first()
        if not order:
            raise HTTPException(status_code=404, detail="Orden no encontrada")

        # 2. Verificar con Wompi si tenemos transaction_id
        if transaction_id:
            token = await create_token()
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{WOMPI_URL}/TransaccionCompra/{transaction_id}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if response.status_code != 200:
                    logger.error(f"Wompi API error: {response.text}")
                    return JSONResponse(
                        status_code=400,
                        content={"status": "PENDING", "message": "No se pudo verificar con Wompi"}
                    )
                
                wompi_data = response.json()
                status_map = {
                    "APPROVED": "APPROVED",
                    "DECLINED": "DECLINED",
                    "PENDING": "PENDING",
                    "VOIDED": "DECLINED",
                    "ERROR": "DECLINED"
                }
                
                wompi_status = status_map.get(wompi_data["estado"], "PENDING")
                
                # Actualizar estado en tu base de datos
                if order.payment:
                    order.payment.pay_state = wompi_status
                    db.commit()
                
                return {
                    "status": wompi_status,
                    "order": {
                        "id": order.id,
                        "order_date": order.order_date,
                        "total": order.payment.pay_amount if order.payment else 0,
                        "payment_method": order.payment.pay_method if order.payment else "N/A"
                    }
                }
        
        # 3. Si no hay transaction_id, verificar estado local
        return {
            "status": order.payment.pay_state if order.payment else "PENDING",
            "order": {
                "id": order.id,
                "order_date": order.order_date,
                "total": order.payment.pay_amount if order.payment else 0,
                "payment_method": order.payment.pay_method if order.payment else "N/A"
            }
        }
        
    except Exception as e:
        logger.error(f"Payment verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al verificar el pago")