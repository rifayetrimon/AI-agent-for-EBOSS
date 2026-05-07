from crewai import Agent
from app.services.llm_factory import get_llm

def get_finance_collection_agent() -> Agent:
    return Agent(
        role='Finance Collection Specialist',
        goal='Draft polite and effective payment reminder emails based on invoice overdue status.',
        backstory=(
            'You are a professional Finance Collection Specialist. Your job is to ensure '
            'customers pay their overdue invoices while maintaining a good relationship. '
            'You escalate the urgency appropriately based on how many days the invoice is overdue.'
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_llm()
    )
