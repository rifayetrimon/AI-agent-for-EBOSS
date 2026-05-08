import json
from typing import Optional

from crewai import Agent, Crew, Process, Task

from app.schemas.cms_schemas import ColorSuggestionResult
from app.services.llm_factory import get_llm


def _agent() -> Agent:
    return Agent(
        role="Brand Colour Designer",
        goal="Suggest harmonious, accessible colour palettes for a brand's CMS theme.",
        backstory=(
            "You are a senior brand designer. You produce palettes that balance brand expression and "
            "WCAG-AA contrast. You always return strict hex codes. You never repeat an existing palette. "
            "When given the actual logo's colours, you treat them as the harmony anchor — every suggested "
            "palette must visually fit the logo (matching, complementary, analogous, or neutral)."
        ),
        verbose=False,
        allow_delegation=False,
        llm=get_llm(),
    )


def _task(
    agent: Agent,
    brand_context: str,
    current_palette: Optional[dict],
    logo_colors: Optional[dict],
    num_options: int,
) -> Task:
    current_block = ""
    if current_palette:
        current_block = (
            f"Current palette in use (do NOT suggest the same one):\n{json.dumps(current_palette)}\n\n"
        )

    logo_block = ""
    if logo_colors:
        logo_block = (
            "LOGO COLOUR ANALYSIS — these are extracted from the actual brand logo:\n"
            f"  dominant: {logo_colors.get('dominant')}\n"
            f"  full palette: {', '.join(logo_colors.get('palette', []))}\n\n"
            "RULE: every suggested palette MUST harmonise with the logo's dominant colour. "
            "Use one of: matching (same hue family), complementary (opposite on the colour wheel), "
            "analogous (adjacent hues), or a neutral pairing. The logo's dominant colour should appear "
            "in EITHER the primary OR the accent slot of every palette you suggest. Do not propose any "
            "palette that visually clashes with the logo.\n\n"
        )

    description = (
        f"Brand context:\n{brand_context}\n\n"
        f"{logo_block}"
        f"{current_block}"
        f"Suggest exactly {num_options} distinct palettes. Each palette must include 5 hex colours: "
        "primary, secondary, accent, background, text. Ensure body-text-on-background contrast meets "
        "WCAG-AA (≥4.5:1). Avoid neon clashes. Each palette has a short evocative name and one-sentence "
        "rationale tying it to the brand AND (when logo colours are given) referencing how it harmonises "
        "with the logo."
    )
    return Task(
        description=description,
        expected_output="A JSON object matching the ColorSuggestionResult schema.",
        agent=agent,
        output_pydantic=ColorSuggestionResult,
    )


def run_color_suggester(
    brand_context: str,
    current_palette: Optional[dict],
    logo_colors: Optional[dict],
    num_options: int,
) -> ColorSuggestionResult:
    agent = _agent()
    task = _task(agent, brand_context, current_palette, logo_colors, num_options)
    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=False)
    result = crew.kickoff()
    out: ColorSuggestionResult = result.pydantic
    if logo_colors:
        out.logo_colors = logo_colors  # ensure the logo analysis travels back to the caller
    return out
