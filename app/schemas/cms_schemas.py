from typing import List, Optional
from pydantic import BaseModel, Field


class NewsMetaRequest(BaseModel):
    body_text: str
    target_audience: Optional[str] = "general public"


class NewsMetaResponse(BaseModel):
    headlines: List[str]
    summary: str
    slug: str


# --- color suggester ---

class ColorPalette(BaseModel):
    name: str = Field(description="Short evocative palette name, e.g. 'Ocean Sunrise'")
    primary: str = Field(description="Primary brand colour, hex (e.g. #0066CC)")
    secondary: str = Field(description="Secondary colour, hex")
    accent: str = Field(description="Accent / call-to-action colour, hex")
    background: str = Field(description="Page background colour, hex")
    text: str = Field(description="Body text colour, hex")
    rationale: str = Field(description="One sentence on why this palette fits the brand")


class LogoColors(BaseModel):
    dominant: str = Field(description="Hex code of the logo's dominant colour")
    palette: List[str] = Field(description="Hex codes of the logo's top N colours")


class ColorSuggestionResult(BaseModel):
    palettes: List[ColorPalette]
    logo_colors: Optional[LogoColors] = None


class SuggestColorsRequest(BaseModel):
    brand_context: str
    current_palette: Optional[dict] = None
    logo_url: Optional[str] = Field(
        default=None,
        description="URL or data-URI of the brand logo. If provided, palettes will harmonise with the logo's actual colours.",
    )
    num_options: int = 3


# --- template recommender ---

class TemplateOption(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    suited_for: Optional[str] = None


class TemplateRecommendation(BaseModel):
    recommended_template_id: str
    runner_up_template_id: Optional[str] = None
    reasoning: str = Field(description="2-3 sentences citing signals from the actual headers")
    audience_fit: str = Field(description="Short note on who this template best serves given the headers")


class RecommendTemplateRequest(BaseModel):
    headers: List[str]
    available_templates: List[TemplateOption]
    additional_context: Optional[str] = None


class ApplyColorPaletteRequest(BaseModel):
    palette: ColorPalette


class ApplyTemplateRequest(BaseModel):
    template_id: str
