from pydantic import BaseModel
from typing import Optional

class PaymentReminderRequest(BaseModel):
    customer_name: str
    amount: float
    due_date: str
    days_overdue: int

class PaymentReminderResponse(BaseModel):
    subject: str
    body: str
    tone: str
