from crewai import Agent
from app.services.llm_factory import get_llm

def get_cms_copywriter_agent() -> Agent:
    return Agent(
        role='CMS Content Copywriter',
        goal='Generate engaging headlines and summaries for news articles.',
        backstory=(
            'You are a skilled CMS Content Copywriter. You know how to extract '
            'the core message of an article and craft multiple catchy headlines '
            'and a concise SEO-friendly summary tailored to the target audience.'
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_llm()
    )
