from fastapi import APIRouter, HTTPException
from app.schemas.cms_schemas import NewsMetaRequest, NewsMetaResponse
from app.agents.cms.crew import run_news_meta_crew

router = APIRouter()

@router.post("/news-meta", response_model=NewsMetaResponse)
def news_meta(request: NewsMetaRequest):
    try:
        result = run_news_meta_crew(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
