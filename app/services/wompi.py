from fastapi import HTTPException 
from pydantic import BaseModel
from config import WOMPI_CLIENT_ID, WOMPI_CLIENT_SECRET, WOMPI_URL
import httpx

async def create_token():
    url = "https://id.wompi.sv/connect/token"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url, 
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            }, 
            data={
                "grant_type": "client_credentials",
                "client_id": WOMPI_CLIENT_ID,
                "client_secret": WOMPI_CLIENT_SECRET,
                "audience": "https://api.wompi.sv/",
            }
        )

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.json()["message"])
        else:
            return response.json()["access_token"]
        
# Desc = Description
async def create_payment_link(amount: float, description: str, reference: str, customer_email: str):
    token = await create_token()
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{WOMPI_URL}/EnlacePago",  # Asegúrate que esta es la URL correcta para enlaces
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={
                    "nombreProducto": "Compra en tu tienda",  # Nombre genérico o personalizable
                    "monto": amount,
                    "informacionAdicional": description,
                    "identificadorEnlaceComercio": reference,
                    "configuracion": {
                        "urlRedirect": "https://tudominio.com/confirmacion",
                        "urlWebhook": "https://tuapi.com/webhook/wompi",
                        "emailsNotificacion": customer_email
                    }
                }
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"Error creating Wompi payment: {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail="Error al crear pago con Wompi"
            )

async def create_payment_3ds(data: dict):
    token = await create_token()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            WOMPI_URL + "/TransaccionCompra/3DS" ,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json=data
        )

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.json())
        
        return response.json()