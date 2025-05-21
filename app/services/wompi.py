from fastapi import HTTPException, logger 
from pydantic import BaseModel
from config import WOMPI_CLIENT_ID, WOMPI_CLIENT_SECRET, WOMPI_URL
import httpx, uuid

async def create_token():
    url = "https://id.wompi.sv/connect/token"

    print(f"WOMPI_URL: {WOMPI_URL}")
    print(f"WOMPI_CLIENT_ID: {WOMPI_CLIENT_ID}")
    print(f"WOMPI_CLIENT_SECRET: {WOMPI_CLIENT_SECRET}")

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
            print(f"\nToken obtenido: {response.json()['access_token'][:15]}...")
            return response.json()["access_token"]
        
# Desc = Description
async def create_payment_link(amount: float, description: str, reference: str, customer_email: str):
    try:
        # 1. Obtener token
        token = await create_token()
        if not token:
            raise HTTPException(status_code=401, detail="No se pudo obtener token de Wompi")
        
        # 2. Preparar payload
        payload = {
            "identificadorEnlaceComercio": reference,
            "monto": float(amount),
            "nombreProducto": "Compra de arreglos florales",
            "formaPago": {
                "permitirTarjetaCreditoDebido": True,
                "permitirPagoConPuntoAgricola": False,
                "permitirPagoEnCuotasAgricola": False
            },
            "configuracion": {
                "urlRedirect": f"https://arreglitosv.com/loading?reference={reference}",
                "urlWebhook": "https://fastapi-app-production-c2d5.up.railway.app/webhooks/transaction/complete",
                "emailsNotificacion": customer_email,
                "notificarTransaccionCliente": True
            }
        }

        print("\nPayload enviado a Wompi:")
        print(payload)

        # 3. Enviar solicitud

        # URL corregida
        url = f"{WOMPI_URL}/EnlacePago"  # Ahora tendrá solo una barra
        
        print(f"\nURL completa: {url}")  # Para depuración

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=30.0
            )

            print(f"\nRespuesta HTTP de Wompi: {response.status_code}")
            print(f"Contenido de respuesta: {response.text}")

            response.raise_for_status()
            
            try:
                return response.json()
            except ValueError as e:
                print(f"Error al parsear JSON: {e}")
                print(f"Contenido recibido: {response.text}")
                raise HTTPException(
                    status_code=500,
                    detail="Respuesta inválida de Wompi"
                )

    except httpx.HTTPStatusError as e:
        print(f"\nError en API Wompi: {str(e)}")
        print(f"Respuesta de error: {e.response.text if e.response else 'No response'}")
        raise HTTPException(
            status_code=e.response.status_code if e.response else 500,
            detail=f"Error en Wompi: {str(e)}"
        )
    except Exception as e:
        print(f"\nError inesperado en create_payment_link: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al comunicarse con Wompi: {str(e)}"
        )