from crewai import Task
from app.schemas.hr_schemas import DraftMessageRequest, DraftMessageResponse
from app.agents.hr.agents import get_hr_communication_agent

def get_draft_message_task(request: DraftMessageRequest) -> Task:
    agent = get_hr_communication_agent()
    
    return Task(
        description=(
            f"Draft an email and an SMS based on the following prompt: '{request.prompt}'.\n"
            f"The sender is: '{request.sender}'.\n"
            f"The recipients are: {', '.join(request.recipient_list)}.\n"
            f"The tone should be: '{request.tone}'.\n"
            "Ensure the SMS is no longer than 160 characters."
        ),
        expected_output="A JSON object containing the email subject, html body, and sms text.",
        agent=agent,
        output_pydantic=DraftMessageResponse
    )
