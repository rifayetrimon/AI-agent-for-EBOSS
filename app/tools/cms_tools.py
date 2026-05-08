from typing import Optional

from pydantic import BaseModel, Field

from app.agents.cms.color_crew import run_color_suggester
from app.agents.cms.template_crew import run_template_recommender
from app.schemas.cms_schemas import TemplateOption
from app.services.cms_client import update_color_config, update_template
from app.services.logo_analyzer import safe_extract_colors
from app.tools.registry import tool, tool_ctx


# ---------- suggest colors ----------

def _looks_like_image_source(s: Optional[str]) -> bool:
    if not s or not isinstance(s, str):
        return False
    s = s.strip()
    return s.startswith(("http://", "https://", "data:image/"))


class SuggestColorsArgs(BaseModel):
    brand_context: str = Field(description="Free-form description of the brand: name, vibe, audience, industry")
    num_options: int = Field(default=3, ge=1, le=5)
    logo_url: Optional[str] = Field(
        default=None,
        description=(
            "OPTIONAL: only set this if the user explicitly typed a logo URL or data-URI in their command. "
            "Do NOT invent a value (e.g. 'our logo', 'the logo'). When omitted, the system automatically "
            "uses the logo URL from the request context."
        ),
    )


@tool(
    name="suggest_cms_colors",
    description=(
        "Suggest brand colour palettes for the CMS theme. Use whenever the user asks for colour suggestions, "
        "new palettes, or to refresh the site's colours — including phrases like 'based on our logo' or "
        "'matching our brand'. The system automatically reads the logo URL from request context and extracts "
        "the logo's actual colours so the palettes harmonise with them; you do not need to pass logo_url "
        "unless the user typed an explicit URL. This tool only suggests — it does NOT save anything."
    ),
    args_model=SuggestColorsArgs,
)
def suggest_cms_colors(args: SuggestColorsArgs) -> dict:
    ctx = tool_ctx.get() or {}
    current_palette = ctx.get("current_palette")

    # Prefer ctx (frontend-supplied source of truth). Only honour args.logo_url if it
    # actually looks like a URL — the LLM tends to hallucinate strings like "our logo".
    ctx_logo = ctx.get("logo_url")
    args_logo = args.logo_url if _looks_like_image_source(args.logo_url) else None
    logo_source = ctx_logo or args_logo
    logo_colors = safe_extract_colors(logo_source) if logo_source else None

    result = run_color_suggester(
        args.brand_context, current_palette, logo_colors, args.num_options
    )
    return {
        "ok": True,
        "palettes": [p.model_dump() for p in result.palettes],
        "logo_colors": logo_colors,
    }


# ---------- apply colors ----------

class ApplyColorArgs(BaseModel):
    name: str = Field(description="Palette name")
    primary: str
    secondary: str
    accent: str
    background: str
    text: str


@tool(
    name="apply_cms_color_palette",
    description=(
        "Apply a chosen colour palette by saving it to the CMS configuration. "
        "Use whenever the user asks to apply, save, set, or use a specific palette — including direct commands "
        "like 'apply this palette', 'save the second one', 'use the Ocean Sunrise palette'. "
        "The full palette (name + 5 hex colours) must be passed in the args."
    ),
    args_model=ApplyColorArgs,
    requires_confirmation=True,
)
def apply_cms_color_palette(args: ApplyColorArgs) -> dict:
    payload = args.model_dump()
    save_result = update_color_config(payload)
    return {
        "ok": True,
        "applied_palette": payload,
        "save_response": save_result,
    }


# ---------- recommend template ----------

class RecommendTemplateArgs(BaseModel):
    additional_context: Optional[str] = Field(
        default=None,
        description="Optional extra context the user provided (e.g. 'we are pivoting to e-commerce')",
    )


@tool(
    name="recommend_cms_template",
    description=(
        "Recommend the best CMS template by reading the site's existing headers/content and picking from the "
        "available templates. The headers list and available_templates list come from the request context — "
        "do NOT pass them as args. Use whenever the user asks 'which template should I use', 'recommend a "
        "template', or 'pick a layout'."
    ),
    args_model=RecommendTemplateArgs,
)
def recommend_cms_template(args: RecommendTemplateArgs) -> dict:
    ctx = tool_ctx.get() or {}
    headers = ctx.get("headers") or []
    templates_raw = ctx.get("available_templates") or []
    if not headers:
        return {"ok": False, "error": "no headers provided in request context"}
    if not templates_raw:
        return {"ok": False, "error": "no available_templates provided in request context"}
    templates = [TemplateOption(**t) if isinstance(t, dict) else t for t in templates_raw]

    rec = run_template_recommender(headers, templates, args.additional_context)
    return {
        "ok": True,
        "recommendation": rec.model_dump(),
        "available_templates": [t.model_dump() for t in templates],
    }


# ---------- apply template ----------

class ApplyTemplateArgs(BaseModel):
    template_id: str = Field(description="The id of the template to apply (from available_templates)")


@tool(
    name="apply_cms_template",
    description=(
        "Apply a chosen template by saving it to the CMS. "
        "Use whenever the user asks to apply, switch to, set, or use a specific template by id or name — "
        "including direct commands like 'apply template t4', 'switch to Minimal Blog', 'use t1', "
        "or as a follow-up after recommend_cms_template when the user accepts."
    ),
    args_model=ApplyTemplateArgs,
    requires_confirmation=True,
)
def apply_cms_template(args: ApplyTemplateArgs) -> dict:
    save_result = update_template({"template_id": args.template_id})
    return {
        "ok": True,
        "applied_template_id": args.template_id,
        "save_response": save_result,
    }
