from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from models.models import Order, Payment
from config import SessionLocal
import hmac
import hashlib
import logging
import json

router = APIRouter(prefix="/webhook", tags=["Webhooks"])
logger = logging.getLogger(__name__)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/transaction/complete")
async def wompi_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        # 1. Obtener el cuerpo de la petición
        body_bytes = await request.body()
        body = json.loads(body_bytes.decode('utf-8'))
        signature = request.headers.get("x-wompi-signature")
        
        print("\n=== Webhook recibido de Wompi ===")
        print(f"Headers: {dict(request.headers)}")
        print(f"Body: {body}")

        # 2. Verificar la firma
        if not verify_signature(body_bytes, signature):
            error_msg = "Firma de webhook inválida"
            print(f"!!! {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        # 3. Validar campos esenciales
        required_fields = ["IdTransaccion", "ResultadoTransaccion", "Monto", "EnlacePago"]
        for field in required_fields:
            if field not in body:
                error_msg = f"Campo requerido faltante: {field}"
                print(f"!!! {error_msg}")
                raise HTTPException(status_code=400, detail=error_msg)

        transaction_id = body["IdTransaccion"]
        status = body["ResultadoTransaccion"]
        amount = body["Monto"]
        reference = body["EnlacePago"]["IdentificadorEnlaceComercio"]

        print(f"\nDatos extraídos:")
        print(f"ID Transacción: {transaction_id}")
        print(f"Referencia: {reference}")
        print(f"Estado: {status}")
        print(f"Monto: {amount}")

        # 4. Buscar el pago en la base de datos
        payment = db.query(Payment).filter(
            Payment.pay_transaction_id == reference
        ).first()

        if not payment:
            error_msg = f"No se encontró pago con referencia: {reference}"
            print(f"!!! {error_msg}")
            return {"status": "error", "message": error_msg}

        print(f"\nPago encontrado en DB:")
        print(f"ID Pago: {payment.id}")
        print(f"Estado actual: {payment.pay_state}")
        print(f"Monto esperado: {payment.pay_amount}")

        # 5. Validar coincidencia de montos
        if float(amount) != float(payment.pay_amount):
            error_msg = f"El monto no coincide. Esperado: {payment.pay_amount}, Recibido: {amount}"
            print(f"!!! {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)

        # 6. Verificar estado de transacción
        if status.lower() not in ["exitosaaprobada", "aprobada"]:
            error_msg = f"Transacción no aprobada. Estado: {status}"
            print(f"!!! {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        # 7. Actualizar base de datos (solo si todo está correcto)
        print("\nActualizando base de datos...")
        
        payment.pay_state = "aprobado"
        payment.pay_transaction_id = transaction_id
        
        order = payment.order
        order.order_state = "completado"
        
        #db.commit()

        print("¡Base de datos actualizada correctamente!")
        
        return {"status": "success", "message": "Webhook procesado correctamente"}

    except json.JSONDecodeError:
        error_msg = "Cuerpo de la petición no es JSON válido"
        print(f"!!! {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error inesperado: {str(e)}"
        print(f"!!! {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

def verify_signature(body: bytes, signature: str) -> bool:
    """Verifica la firma HMAC-SHA256 del webhook"""
    try:
        # Obtener tu clave secreta de Wompi (debes configurarla en tus variables de entorno)
        secret_key = "TU_CLAVE_SECRETA_WOMPI"  # Reemplaza con tu clave real
        
        if not secret_key or not signature:
            print("Advertencia: No se proporcionó clave secreta o firma")
            return False

        # Calcular HMAC
        computed_signature = hmac.new(
            secret_key.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()

        print(f"\nVerificación de firma:")
        print(f"Firma recibida: {signature}")
        print(f"Firma calculada: {computed_signature}")

        # Comparación segura contra ataques de timing
        return hmac.compare_digest(computed_signature, signature)
    
    except Exception as e:
        print(f"Error al verificar firma: {str(e)}")
        return False