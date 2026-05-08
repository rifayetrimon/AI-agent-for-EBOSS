from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agents.router import run_router_agent
from app.db.session import get_db
from app.schemas.agent_schemas import StaffRecord
from app.tools.registry import all_tools

router = APIRouter()


class AgentRouterRequest(BaseModel):
    command: str
    context: dict[str, Any] = {}
    auto_confirm: bool = False


class ToolCallRecord(BaseModel):
    tool: str
    args: dict[str, Any]
    result: dict[str, Any]


class AgentRouterResponse(BaseModel):
    summary: str
    tool_calls: List[ToolCallRecord]


def _summarize_context(context: dict, staff: list[StaffRecord]) -> str:
    parts = []
    if staff:
        parts.append(f"- staff directory available with {len(staff)} member(s)")
    if context.get("user_timezone"):
        parts.append(f"- user_timezone: {context['user_timezone']}")
    if context.get("current_palette"):
        parts.append("- current_palette: available (current CMS color config)")
    headers = context.get("headers")
    if headers:
        parts.append(f"- headers: available ({len(headers)} site headlines/titles)")
    templates = context.get("available_templates")
    if templates:
        parts.append(f"- available_templates: available ({len(templates)} options)")
    if context.get("auto_confirm"):
        parts.append("- auto_confirm: true (high-blast-radius applies are pre-authorised)")
    return "\n".join(parts) if parts else "(no extra context provided)"


@router.post("/command", response_model=AgentRouterResponse)
def agent_command(req: AgentRouterRequest, db: Session = Depends(get_db)):
    raw_staff = req.context.get("staff", [])
    try:
        staff = [StaffRecord(**s) for s in raw_staff] if raw_staff else []
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"invalid staff payload in context: {e}")

    ctx: dict = {**req.context}
    ctx["db"] = db
    ctx["staff"] = staff
    ctx["auto_confirm"] = req.auto_confirm
    ctx.setdefault("user_timezone", "UTC")
    log: list[dict] = []

    try:
        summary = run_router_agent(req.command, ctx, log, _summarize_context(ctx, staff))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"router agent failed: {e}")

    return AgentRouterResponse(
        summary=summary,
        tool_calls=[ToolCallRecord(**c) for c in log],
    )


@router.get("/tools")
def list_tools():
    return [
        {
            "name": t.name,
            "description": t.description,
            "args_schema": t.args_model.model_json_schema(),
            "requires_confirmation": t.requires_confirmation,
        }
        for t in all_tools()
    ]
