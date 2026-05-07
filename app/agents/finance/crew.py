from crewai import Crew, Process
from app.schemas.finance_schemas import PaymentReminderRequest, PaymentReminderResponse
from app.agents.finance.agents import get_finance_collection_agent
from app.agents.finance.tasks import get_payment_reminder_task

def run_payment_reminder_crew(request: PaymentReminderRequest) -> PaymentReminderResponse:
    agent = get_finance_collection_agent()
    task = get_payment_reminder_task(request)
    
    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )
    
    result = crew.kickoff()
    return result.pydantic
