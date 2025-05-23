from pydantic import BaseModel
from typing import List
from datetime import datetime

class ArrangementInOrder(BaseModel):
    arrangement_name: str
    arrangement_img_url: str
    quantity: int
    price: float
    discount: float

class OrderDetailResponse(BaseModel):
    order_id: int
    order_state: str
    order_date: datetime
    order_comments: str
    delivery_address: str
    payment_method: str
    payment_state: str
    total_paid: float
    arrangements: List[ArrangementInOrder]
