import json
from crewai import Agent, Task, Crew, Process

from app.schemas.agent_schemas import DraftedContent, ParsedPlan, StaffRecord
from app.services.llm_factory import get_llm


def _drafter_agent() -> Agent:
    return Agent(
        role="HR Communication Specialist",
        goal="Draft on-brand, personalised HR messages from a structured plan.",
        backstory=(
            "You are an expert HR communication writer. Given a plan describing intent, recipients and tone, "
            "you produce a polished email (subject + html body) and/or an SMS (≤160 chars) that addresses "
            "recipients by name and reflects their role where relevant. You return strict JSON only."
        ),
        verbose=False,
        allow_delegation=False,
        llm=get_llm(),
    )


def _drafter_task(agent: Agent, plan: ParsedPlan, recipients: list[StaffRecord]) -> Task:
    recipients_json = json.dumps(
        [r.model_dump(exclude_none=True) for r in recipients],
        ensure_ascii=False,
    )

    needs_email = plan.channel in ("email", "both")
    needs_sms = plan.channel in ("sms", "both")

    description = (
        f"Intent: {plan.intent}\n"
        f"Intent description: {plan.intent_description}\n"
        f"Tone: {plan.tone}\n"
        f"Channel: {plan.channel}\n"
        f"Scheduled to send at: {plan.scheduled_at_iso}\n\n"
        f"Recipients (full profiles):\n{recipients_json}\n\n"
        "Rules:\n"
        f"- {'Produce' if needs_email else 'Do NOT produce'} email subject + html body. "
        f"{'' if needs_email else 'Set subject and html to null.'}\n"
        f"- {'Produce' if needs_sms else 'Do NOT produce'} an sms string (≤160 chars). "
        f"{'' if needs_sms else 'Set sms to null.'}\n"
        "- If there is exactly one recipient, address them by first name in the greeting.\n"
        "- If there are many recipients, use a generic greeting (e.g. 'Dear Team').\n"
        "- The HTML body should be valid simple HTML (paragraphs, basic formatting).\n"
        "- Keep the message culturally appropriate to the intent."
    )

    return Task(
        description=description,
        expected_output="A JSON object matching the DraftedContent schema.",
        agent=agent,
        output_pydantic=DraftedContent,
    )


def run_drafter_crew(plan: ParsedPlan, recipients: list[StaffRecord]) -> DraftedContent:
    agent = _drafter_agent()
    task = _drafter_task(agent, plan, recipients)
    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=False)
    result = crew.kickoff()
    return result.pydantic
