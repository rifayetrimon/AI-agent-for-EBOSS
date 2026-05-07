from crewai import Crew, Process
from app.schemas.cms_schemas import NewsMetaRequest, NewsMetaResponse
from app.agents.cms.agents import get_cms_copywriter_agent
from app.agents.cms.tasks import get_news_meta_task

def run_news_meta_crew(request: NewsMetaRequest) -> NewsMetaResponse:
    agent = get_cms_copywriter_agent()
    task = get_news_meta_task(request)
    
    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )
    
    result = crew.kickoff()
    return result.pydantic
