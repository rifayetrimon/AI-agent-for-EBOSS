from fastapi import APIRouter, HTTPException
from app.schemas.finance_schemas import PaymentReminderRequest, PaymentReminderResponse
from app.agents.finance.crew import run_payment_reminder_crew

router = APIRouter()

@router.post("/payment-reminder", response_model=PaymentReminderResponse)
def payment_reminder(request: PaymentReminderRequest):
    try:
        result = run_payment_reminder_crew(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
