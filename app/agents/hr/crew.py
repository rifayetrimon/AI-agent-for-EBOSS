from crewai import Crew, Process
from app.schemas.hr_schemas import DraftMessageRequest, DraftMessageResponse
from app.agents.hr.agents import get_hr_communication_agent
from app.agents.hr.tasks import get_draft_message_task

def run_draft_message_crew(request: DraftMessageRequest) -> DraftMessageResponse:
    agent = get_hr_communication_agent()
    task = get_draft_message_task(request)
    
    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )
    
    result = crew.kickoff()
    return result.pydantic
