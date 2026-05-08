import json
from typing import List, Optional
from crewai import Agent, Crew, Process, Task
from app.schemas.cms_schemas import TemplateOption, TemplateRecommendation
from app.services.llm_factory import get_llm

def _agent() -> Agent:
    return Agent(
        role="Content Strategist",
        goal="Recommend the best CMS template by analysing the site's actual headers and tone.",
        backstory=(
            "You read a site's existing headlines and titles to determine which layout fits its content. "
            "You consider audience, content density, visual emphasis, and information hierarchy. "
            "Your recommendations always cite signal from the actual headers, never hand-wave."
        ),
        verbose=False,
        allow_delegation=False,
        llm=get_llm(),
    )


def _task(
    agent: Agent,
    headers: List[str],
    templates: List[TemplateOption],
    additional: Optional[str],
) -> Task:
    templates_block = json.dumps([t.model_dump() for t in templates], indent=2)
    headers_block = "\n".join(f"- {h}" for h in headers[:200])
    extra = f"\nAdditional context: {additional}\n" if additional else ""
    description = (
        f"Sample of the site's existing headers / titles:\n{headers_block}\n\n"
        f"Available templates (pick recommended_template_id from this list only):\n{templates_block}\n"
        f"{extra}"
        "Pick the single best template, then a runner-up. Reasoning must be 2-3 sentences and reference "
        "concrete patterns you noticed in the headers above. audience_fit should describe who this template "
        "best serves given the headers."
    )
    return Task(
        description=description,
        expected_output="A JSON object matching the TemplateRecommendation schema.",
        agent=agent,
        output_pydantic=TemplateRecommendation,
    )


def run_template_recommender(
    headers: List[str],
    templates: List[TemplateOption],
    additional: Optional[str],
) -> TemplateRecommendation:
    agent = _agent()
    task = _task(agent, headers, templates, additional)
    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=False)
    result = crew.kickoff()
    return result.pydantic
