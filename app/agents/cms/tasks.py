from crewai import Task
from app.schemas.cms_schemas import NewsMetaRequest, NewsMetaResponse
from app.agents.cms.agents import get_cms_copywriter_agent

def get_news_meta_task(request: NewsMetaRequest) -> Task:
    agent = get_cms_copywriter_agent()
    
    return Task(
        description=(
            f"Read the following news article body:\n\n{request.body_text}\n\n"
            f"The target audience is: {request.target_audience}.\n"
            "Generate 3 distinct and catchy headline options.\n"
            "Generate a concise meta-description summary (max 160 chars).\n"
            "Generate a URL-friendly slug based on the best headline."
        ),
        expected_output="A JSON object containing the headlines array, summary string, and slug string.",
        agent=agent,
        output_pydantic=NewsMetaResponse
    )
