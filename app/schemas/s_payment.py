from pydantic import BaseModel
from typing import Optional

class PaymentLinkResponse(BaseModel):
    payment_url: str
    reference: str
    amount: float
    # Campos opcionales que Wompi podría devolver
    idEnlace: Optional[int] = None
    urlQrCodeEnlace: Optional[str] = None
    estaProductivo: Optional[bool] = None