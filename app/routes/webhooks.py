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

@router.post("/transaction/complete")
async def handle_wompi_webhook(request: Request, db: Session = Depends(get_db)):
    logger.info("Webhook recibido")
    try:
        # 1. Read and parse the request
        body_bytes = await request.body()
        body = json.loads(body_bytes.decode('utf-8'))
        signature = request.headers.get("x-wompi-signature", "")
        
        logger.info(f"Headers: {dict(request.headers)}")
        logger.info(f"Body: {json.dumps(body, indent=2)}")
    except Exception as e:
        logger.error(f"Error al leer el webhook: {str(e)}")
        raise HTTPException(status_code=400, detail="Error al leer el webhook")

    return {"message": "Webhook recibido"}