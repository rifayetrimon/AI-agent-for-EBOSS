from crewai import Task
from app.schemas.finance_schemas import PaymentReminderRequest, PaymentReminderResponse
from app.agents.finance.agents import get_finance_collection_agent

def get_payment_reminder_task(request: PaymentReminderRequest) -> Task:
    agent = get_finance_collection_agent()
    
    return Task(
        description=(
            f"Draft a payment reminder email for customer '{request.customer_name}'.\n"
            f"The outstanding amount is {request.amount}.\n"
            f"The original due date was {request.due_date}.\n"
            f"The invoice is currently {request.days_overdue} days overdue.\n"
            "Adjust the tone based on the days overdue: 3 days should be a polite nudge, "
            "14 days should be firm, and 30+ days should be urgent.\n"
        ),
        expected_output="A JSON object containing the email subject, body, and tone used.",
        agent=agent,
        output_pydantic=PaymentReminderResponse
    )
