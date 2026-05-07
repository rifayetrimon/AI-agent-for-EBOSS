from crewai import Agent
from app.services.llm_factory import get_llm

def get_hr_communication_agent() -> Agent:
    return Agent(
        role='HR Communication Specialist',
        goal='Draft clear, professional, and empathetic communications for employees.',
        backstory=(
            'You are an expert HR Communication Specialist. You excel at taking '
            'brief notes or prompts and expanding them into well-crafted emails and SMS messages. '
            'You always maintain the requested tone and ensure all necessary details are included.'
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_llm()
    )
