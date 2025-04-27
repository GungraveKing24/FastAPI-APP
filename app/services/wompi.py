from fastapi import APIRouter, HTTPException 
from pydantic import BaseModel
from config import WOMPI_PRIVATE_KEY, WOMPI_PUBLIC_KEY, WOMPI_URL
import httpx 

class WompiPaymentRequest(BaseModel):
    amount_in_cents: int
    currency: str = "COP"
    reference: str
    customer_email: str
    customer_name: str
    customer_cellphone: str
    customer_address: str

async def create_payment(request: WompiPaymentRequest):
    url = WOMPI_URL + "/api/v0/charges"
    