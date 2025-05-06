from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from models.models import Order, Payment
from config import SessionLocal, WOMPI_CLIENT_SECRET
import json, logging

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

@router.post("/transaction/complete")
async def handle_wompi_webhook(request: Request, db: Session = Depends(get_db)):
    logger.info("\n=== Received Wompi Webhook ===")
    try:
        # 1. Read and parse the request
        body_bytes = await request.body()
        body = json.loads(body_bytes.decode('utf-8'))
        signature = request.headers.get("x-wompi-signature", "")
        
        logger.info(f"Headers: {dict(request.headers)}")
        logger.info(f"Body: {json.dumps(body, indent=2)}")

        # 2. Validate required fields
        required_fields = [
            "IdTransaccion", 
            "ResultadoTransaccion", 
            "Monto", 
            "EnlacePago",
            "esReal",
            "esAprobada"
        ]
        
        for field in required_fields:
            if field not in body:
                error_msg = f"Missing required field: {field}"
                logger.error(error_msg)
                raise HTTPException(status_code=400, detail=error_msg)

        transaction_id = body["IdTransaccion"]
        status = body["ResultadoTransaccion"].lower()
        amount = float(body["Monto"])
        reference = body["EnlacePago"]["IdentificadorEnlaceComercio"]
        is_real = body["esReal"]
        is_approved = body["esAprobada"]

        logger.info(f"\nTransaction details:")
        logger.info(f"ID: {transaction_id}")
        logger.info(f"Reference: {reference}")
        logger.info(f"Status: {status}")
        logger.info(f"Amount: {amount}")
        logger.info(f"Is Real: {is_real}")
        logger.info(f"Is Approved: {is_approved}")

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    return {"message": "Webhook processed successfully"}
