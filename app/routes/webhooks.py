from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session, joinedload  # Added joinedload import
from models.models import Order, Payment
from config import SessionLocal, WOMPI_CLIENT_SECRET
from datetime import datetime
import json, logging
import hmac
import hashlib

router = APIRouter(prefix="/webhooks")
logger = logging.getLogger(__name__)

# Configuración (debería estar en tus variables de entorno)
WOMPI_SECRET_KEY = WOMPI_CLIENT_SECRET

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_wompi_signature(body: bytes, received_signature: str) -> bool:
    """
    Verifica la firma HMAC-SHA256 del webhook
    """
    try:
        computed_signature = hmac.new(
            WOMPI_SECRET_KEY.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()
        
        logger.info(f"Firma calculada: {computed_signature}")
        logger.info(f"Firma recibida: {received_signature}")
        
        return hmac.compare_digest(computed_signature, received_signature)
    except Exception as e:
        logger.error(f"Error al verificar firma: {str(e)}")
        return False

@router.post("/transaction/complete")
async def handle_wompi_webhook(request: Request, db: Session = Depends(get_db)):
    logger.info("\n=== Received Wompi Webhook ===")
    try:
        # 1. Leer y parsear el request
        body_bytes = await request.body()
        body = json.loads(body_bytes.decode('utf-8'))
        signature = request.headers.get("x-wompi-signature", "")
        
        logger.info(f"Headers: {dict(request.headers)}")
        logger.info(f"Body: {json.dumps(body, indent=2)}")

        # 2. Validar campos requeridos
        required_fields = ["IdTransaccion", "ResultadoTransaccion", "Monto", "EnlacePago"]
        for field in required_fields:
            if field not in body:
                error_msg = f"Missing required field: {field}"
                logger.error(error_msg)
                raise HTTPException(status_code=400, detail=error_msg)

        transaction_id = body["IdTransaccion"]
        status = body["ResultadoTransaccion"].lower()
        amount = float(body["Monto"])
        reference = body["EnlacePago"]["IdentificadorEnlaceComercio"]

        logger.info(f"\nTransaction details:")
        logger.info(f"ID: {transaction_id}")
        logger.info(f"Reference: {reference}")
        logger.info(f"Status: {status}")
        logger.info(f"Amount: {amount}")

        # 3. Buscar el pago (no la orden) primero
        payment = db.query(Payment).filter(
            Payment.pay_transaction_id == reference
        ).first()

        if not payment:
            error_msg = f"Payment not found for reference: {reference}"
            logger.error(error_msg)
            raise HTTPException(status_code=404, detail=error_msg)

        # Ahora obtener la orden relacionada
        order = db.query(Order).filter(Order.id == payment.order_id).first()
        if not order:
            error_msg = f"Order not found for payment: {payment.id}"
            logger.error(error_msg)
            raise HTTPException(status_code=404, detail=error_msg)

        logger.info(f"\nFound payment and order:")
        logger.info(f"Order ID: {order.id}")
        logger.info(f"Current state: {order.order_state}")
        logger.info(f"Payment amount: {payment.pay_amount}")
        logger.info(f"Payment state: {payment.pay_state}")

        # 4. Verificar estado de la transacción
        if status not in ["exitosaaprobada", "aprobada"]:
            error_msg = f"Transaction not approved. Status: {status}"
            logger.error(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)

        # 5. Verificar que el monto coincida
        if abs(float(amount) - float(payment.pay_amount)) > 0.01:
            error_msg = f"Amount mismatch. Expected: {payment.pay_amount}, Received: {amount}"
            logger.error(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)

        # 6. Verificar firma si está presente
        if signature:
            is_valid = verify_wompi_signature(body_bytes, signature)
            if not is_valid:
                error_msg = "Invalid HMAC signature"
                logger.error(error_msg)
                raise HTTPException(status_code=400, detail=error_msg)
            logger.info("Valid HMAC signature received")
        else:
            logger.warning("No HMAC signature received, relying on status validation")

        # 7. Actualizar base de datos
        try:
            # Actualizar pago
            payment.pay_state = "aprobado"
            payment.pay_transaction_id = transaction_id
            payment.pay_date = datetime.utcnow
            
            # Actualizar orden
            order.order_state = "completado"
            
            db.commit()
            
            logger.info("Database updated successfully!")
            
            return {
                "status": "success",
                "message": "Webhook processed successfully",
                "order_id": order.id,
                "transaction_id": transaction_id
            }
            
        except Exception as e:
            db.rollback()
            error_msg = f"Error updating database: {str(e)}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)

    except json.JSONDecodeError:
        error_msg = "Request body is not valid JSON"
        logger.error(error_msg)
        raise HTTPException(status_code=400, detail=error_msg)
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)