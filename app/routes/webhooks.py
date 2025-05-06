from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from models.models import Order, Payment
from config import SessionLocal, WOMPI_CLIENT_SECRET
from typing import Optional
import hmac, hashlib, json, logging, httpx, uuid

router = APIRouter(prefix="/webhooks")
logger = logging.getLogger(__name__)

# Configuración (debería estar en tus variables de entorno)
WOMPI_SECRET_KEY = WOMPI_CLIENT_SECRET   # Reemplaza con tu API Secret

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

async def validate_transaction_with_wompi(transaction_id: str) -> bool:
    """
    Valida la transacción directamente con la API de Wompi
    como fallback cuando no hay firma HMAC
    """
    try:
        # Implementa la lógica para obtener token y consultar la transacción
        # Similar a lo que hace el código PHP
        # Esto es un esquema básico:
        
        # 1. Obtener token
        token = await get_wompi_token()
        
        # 2. Consultar transacción
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.wompi.sv/TransaccionCompra/{transaction_id}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Verificar que sea real y aprobada
            return data.get("esReal", False) and data.get("esAprobada", False)
            
    except Exception as e:
        logger.error(f"Error validando transacción con Wompi: {str(e)}")
        return False

@router.post("/transaction/complete")
async def handle_wompi_webhook(request: Request, db: Session = Depends(get_db)):
    print("\n=== Webhook recibido ===")
    try:
        # 1. Leer el cuerpo del request
        body_bytes = await request.body()
        body = json.loads(body_bytes.decode('utf-8'))
        signature = request.headers.get("x-wompi-signature", "")
        
        logger.info("\n=== Webhook recibido ===")
        logger.info(f"Headers: {dict(request.headers)}")
        logger.info(f"Body: {body}")

        # 2. Validar campos obligatorios
        required_fields = [
            "IdTransaccion", 
            "ResultadoTransaccion", 
            "Monto", 
            "EnlacePago"
        ]
        
        for field in required_fields:
            if field not in body:
                error_msg = f"Campo requerido faltante: {field}"
                logger.error(error_msg)
                raise HTTPException(status_code=400, detail=error_msg)

        transaction_id = body["IdTransaccion"]
        status = body["ResultadoTransaccion"].lower()
        amount = float(body["Monto"])
        reference = body["EnlacePago"]["IdentificadorEnlaceComercio"]

        logger.info(f"\nDatos de transacción:")
        logger.info(f"ID: {transaction_id}")
        logger.info(f"Referencia: {reference}")
        logger.info(f"Estado: {status}")
        logger.info(f"Monto: {amount}")

        # 3. Buscar la orden en la base de datos
        order = db.query(Order).filter(
            Order.payment.has(Payment.pay_transaction_id == reference)
        ).first()

        if not order:
            error_msg = f"Orden no encontrada para referencia: {reference}"
            logger.error(error_msg)
            raise HTTPException(status_code=404, detail=error_msg)

        logger.info(f"\nOrden encontrada:")
        logger.info(f"ID Orden: {order.id}")
        logger.info(f"Estado actual: {order.order_state}")
        logger.info(f"Monto esperado: {order.payment.pay_amount}")

        # 4. Verificar monto
        if abs(float(amount) - float(order.payment.pay_amount)) > 0.01:
            error_msg = f"Monto no coincide. Esperado: {order.payment.pay_amount}, Recibido: {amount}"
            logger.error(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)

        # 5. Validar firma o consultar API como fallback
        is_valid = False
        
        if signature:
            is_valid = verify_wompi_signature(body_bytes, signature)
            if is_valid:
                logger.info("Firma HMAC válida")
            else:
                logger.warning("Firma HMAC inválida, intentando validar con API...")
                is_valid = await validate_transaction_with_wompi(transaction_id)
        else:
            logger.warning("No hay firma HMAC, validando con API...")
            is_valid = await validate_transaction_with_wompi(transaction_id)

        if not is_valid:
            error_msg = "Transacción no pudo ser validada"
            logger.error(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)

        # 6. Verificar estado de la transacción
        if status not in ["exitosaaprobada", "aprobada"]:
            error_msg = f"Transacción no aprobada. Estado: {status}"
            logger.error(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)

        # 7. Actualizar base de datos
        logger.info("\nActualizando base de datos...")
        
        try:
            # Actualizar pago
            payment = order.payment
            payment.pay_state = "aprobado"
            payment.pay_transaction_id = transaction_id
            
            # Actualizar orden
            order.order_state = "completado"
            
            db.commit()
            
            logger.info("¡Base de datos actualizada correctamente!")
            
            return {
                "status": "success",
                "message": "Webhook procesado correctamente",
                "order_id": order.id,
                "transaction_id": transaction_id
            }
            
        except Exception as e:
            db.rollback()
            error_msg = f"Error al actualizar base de datos: {str(e)}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)

    except json.JSONDecodeError:
        error_msg = "Cuerpo de la petición no es JSON válido"
        logger.error(error_msg)
        raise HTTPException(status_code=400, detail=error_msg)
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error inesperado: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

async def get_wompi_token() -> str:
    """Obtiene token de acceso de Wompi (similar al código PHP)"""
    # Implementa la lógica para obtener el token
    # Esto es un ejemplo básico:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://id.wompi.sv/connect/token",
            data={
                "grant_type": "client_credentials",
                "client_id": "tu_client_id",
                "client_secret": "tu_client_secret",
                "audience": "wompi_api"
            },
            timeout=30.0
        )
        
        response.raise_for_status()
        data = response.json()
        return data["access_token"]