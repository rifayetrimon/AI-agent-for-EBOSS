from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.cms.color_crew import run_color_suggester
from app.agents.cms.crew import run_news_meta_crew
from app.agents.cms.template_crew import run_template_recommender
from app.schemas.cms_schemas import (
    ApplyColorPaletteRequest,
    ApplyTemplateRequest,
    ColorSuggestionResult,
    NewsMetaRequest,
    NewsMetaResponse,
    RecommendTemplateRequest,
    SuggestColorsRequest,
    TemplateRecommendation,
)
from app.services.cms_client import update_color_config, update_template
from app.services.logo_analyzer import safe_extract_colors

router = APIRouter()


@router.post("/news-meta", response_model=NewsMetaResponse)
def news_meta(request: NewsMetaRequest):
    try:
        return run_news_meta_crew(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggest-colors", response_model=ColorSuggestionResult)
def suggest_colors(req: SuggestColorsRequest):
    try:
        logo_colors = safe_extract_colors(req.logo_url) if req.logo_url else None
        return run_color_suggester(
            req.brand_context, req.current_palette, logo_colors, req.num_options
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ApplyColorResponse(BaseModel):
    ok: bool
    applied_palette: dict
    save_response: dict


@router.post("/apply-color-palette", response_model=ApplyColorResponse)
def apply_color(req: ApplyColorPaletteRequest):
    try:
        save_result = update_color_config(req.palette.model_dump())
        return ApplyColorResponse(
            ok=True,
            applied_palette=req.palette.model_dump(),
            save_response=save_result,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend-template", response_model=TemplateRecommendation)
def recommend_template(req: RecommendTemplateRequest):
    if not req.headers:
        raise HTTPException(status_code=400, detail="headers cannot be empty")
    if not req.available_templates:
        raise HTTPException(status_code=400, detail="available_templates cannot be empty")
    try:
        return run_template_recommender(req.headers, req.available_templates, req.additional_context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ApplyTemplateResponse(BaseModel):
    ok: bool
    applied_template_id: str
    save_response: dict


@router.post("/apply-template", response_model=ApplyTemplateResponse)
def apply_template(req: ApplyTemplateRequest):
    try:
        save_result = update_template({"template_id": req.template_id})
        return ApplyTemplateResponse(
            ok=True,
            applied_template_id=req.template_id,
            save_response=save_result,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
