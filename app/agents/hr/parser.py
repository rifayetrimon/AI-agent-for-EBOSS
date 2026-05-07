import json
from datetime import datetime
from zoneinfo import ZoneInfo
from crewai import Agent, Task, Crew, Process

from app.schemas.agent_schemas import ParsedPlan, StaffRecord
from app.services.llm_factory import get_llm


def _parser_agent() -> Agent:
    return Agent(
        role="HR Scheduling Parser",
        goal="Translate freeform HR scheduling commands into a strict JSON plan.",
        backstory=(
            "You are an HR scheduling specialist. You read a manager's natural-language request "
            "and turn it into a precise plan: who the message goes to, what channel (email/sms/both), "
            "what intent it serves, and exactly when it should be sent. You always pick recipients only "
            "from the provided staff directory and you always emit a future scheduled time in ISO 8601 "
            "with a timezone offset. If anything is ambiguous, you record a warning."
        ),
        verbose=False,
        allow_delegation=False,
        llm=get_llm(),
    )


def _parser_task(agent: Agent, command: str, staff: list[StaffRecord], user_timezone: str) -> Task:
    try:
        tz = ZoneInfo(user_timezone)
    except Exception:
        tz = ZoneInfo("UTC")
    now_local = datetime.now(tz).isoformat()

    staff_table = json.dumps(
        [s.model_dump(exclude_none=True) for s in staff],
        ensure_ascii=False,
    )

    description = (
        f"User command:\n\"{command}\"\n\n"
        f"Current local time: {now_local}\n"
        f"User timezone: {user_timezone}\n\n"
        f"Staff directory (the only valid recipients):\n{staff_table}\n\n"
        "Rules:\n"
        "1. Pick recipient_ids ONLY from the directory above. If the command says 'all staff', include every id.\n"
        "2. If the command names a person and multiple staff match by name, pick the closest match and add a warning.\n"
        "3. If the command names a person and no staff match, return an empty recipient_ids list and a warning.\n"
        "4. scheduled_at_iso must be a future timestamp in ISO 8601 with the offset for the user's timezone "
        "(e.g. 2026-04-21T00:01:00+08:00). If the command is vague (e.g. 'tomorrow morning'), pick a reasonable concrete time and add a warning.\n"
        "5. intent should be a short snake_case slug like birthday_wish, vacation_wish, reminder, announcement, holiday_greeting.\n"
        "6. channel must be one of: email, sms, both. Default to email unless the user clearly asks for SMS.\n"
        "7. tone should match the spirit of the request (friendly, formal, celebratory, urgent)."
    )

    return Task(
        description=description,
        expected_output="A JSON object matching the ParsedPlan schema.",
        agent=agent,
        output_pydantic=ParsedPlan,
    )


def run_parser_crew(command: str, staff: list[StaffRecord], user_timezone: str) -> ParsedPlan:
    agent = _parser_agent()
    task = _parser_task(agent, command, staff, user_timezone)
    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=False)
    result = crew.kickoff()
    return result.pydantic
