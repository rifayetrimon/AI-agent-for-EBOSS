from datetime import datetime, timezone
from typing import Optional

from dateutil import parser as date_parser
from pydantic import BaseModel, Field

from app.agents.hr.drafter import run_drafter_crew
from app.agents.hr.parser import run_parser_crew
from app.db.models import ScheduledMessage
from app.services.scheduler import cancel_message, schedule_message
from app.tools.registry import tool, tool_ctx


class ScheduleHrMessageArgs(BaseModel):
    command: str = Field(description="Original user command verbatim describing who, what, and when")
    user_timezone: str = Field(default="UTC", description="IANA timezone like Asia/Kuala_Lumpur")


@tool(
    name="schedule_hr_message",
    description=(
        "Schedule an HR email/SMS to one or more staff at a specific future time. "
        "Use whenever the user asks to send/schedule a personalised message at a future time "
        "(e.g. 'wish Ahmad happy birthday on April 21', 'remind all staff about the meeting tomorrow at 9am'). "
        "Staff directory and timezone are pulled from the request context automatically — do not invent or pass them."
    ),
    args_model=ScheduleHrMessageArgs,
)
def schedule_hr_message(args: ScheduleHrMessageArgs) -> dict:
    ctx = tool_ctx.get() or {}
    db = ctx.get("db")
    staff = ctx.get("staff") or []
    auto_confirm = bool(ctx.get("auto_confirm", False))

    if db is None:
        return {"ok": False, "error": "no db session in tool context"}
    if not staff:
        return {"ok": False, "error": "no staff directory provided in request context"}

    user_tz = args.user_timezone or ctx.get("user_timezone") or "UTC"

    plan = run_parser_crew(args.command, staff, user_tz)

    staff_by_id = {s.id: s for s in staff}
    resolved = [staff_by_id[i] for i in plan.recipient_ids if i in staff_by_id]
    warnings = list(plan.warnings or [])
    missing = [i for i in plan.recipient_ids if i not in staff_by_id]
    if missing:
        warnings.append(f"agent referenced unknown staff ids: {missing}")
    if not resolved:
        return {"ok": False, "error": "no valid recipients resolved", "warnings": warnings}

    try:
        scheduled_at = date_parser.isoparse(plan.scheduled_at_iso)
    except Exception:
        return {"ok": False, "error": f"invalid scheduled_at_iso: {plan.scheduled_at_iso!r}"}
    if scheduled_at.tzinfo is None:
        return {"ok": False, "error": "scheduled_at_iso missing timezone offset"}
    scheduled_at_utc = scheduled_at.astimezone(timezone.utc).replace(tzinfo=None)
    if scheduled_at_utc <= datetime.utcnow():
        return {"ok": False, "error": "scheduled_at is in the past"}

    draft = run_drafter_crew(plan, resolved)

    msg = ScheduledMessage(
        user_command=args.command,
        user_timezone=user_tz,
        intent=plan.intent,
        intent_description=plan.intent_description,
        recipient_ids=[r.id for r in resolved],
        recipient_payload=[r.model_dump(exclude_none=True) for r in resolved],
        channel=plan.channel,
        tone=plan.tone,
        scheduled_at_utc=scheduled_at_utc,
        draft_subject=draft.subject,
        draft_html=draft.html,
        draft_sms=draft.sms,
        warnings=warnings,
        status="pending_confirmation",
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    if auto_confirm:
        schedule_message(msg.id, msg.scheduled_at_utc.replace(tzinfo=timezone.utc))
        msg.status = "scheduled"
        msg.confirmed_at = datetime.utcnow()
        db.commit()
        db.refresh(msg)

    return {
        "ok": True,
        "plan_id": msg.id,
        "status": msg.status,
        "intent": msg.intent,
        "channel": msg.channel,
        "scheduled_at_utc": msg.scheduled_at_utc.isoformat(),
        "recipients": [r.model_dump(exclude_none=True) for r in resolved],
        "draft_subject": msg.draft_subject,
        "draft_html": msg.draft_html,
        "draft_sms": msg.draft_sms,
        "warnings": warnings,
    }


class ConfirmArgs(BaseModel):
    plan_id: int = Field(description="Plan id returned by schedule_hr_message")


@tool(
    name="confirm_scheduled_message",
    description=(
        "Arm a pending_confirmation scheduled message so it actually fires at its scheduled time. "
        "Only use when the user explicitly confirms a previously created plan."
    ),
    args_model=ConfirmArgs,
)
def confirm_scheduled_message(args: ConfirmArgs) -> dict:
    ctx = tool_ctx.get() or {}
    db = ctx.get("db")
    if db is None:
        return {"ok": False, "error": "no db session in tool context"}
    msg = db.query(ScheduledMessage).get(args.plan_id)
    if msg is None:
        return {"ok": False, "error": "plan not found"}
    if msg.status != "pending_confirmation":
        return {"ok": False, "error": f"cannot confirm in status {msg.status!r}"}
    if msg.scheduled_at_utc <= datetime.utcnow():
        return {"ok": False, "error": "scheduled_at is in the past"}
    schedule_message(msg.id, msg.scheduled_at_utc.replace(tzinfo=timezone.utc))
    msg.status = "scheduled"
    msg.confirmed_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "plan_id": msg.id, "status": msg.status}


class CancelArgs(BaseModel):
    plan_id: int


@tool(
    name="cancel_scheduled_message",
    description="Cancel a scheduled or pending HR message so it will not be sent.",
    args_model=CancelArgs,
)
def cancel_scheduled_message(args: CancelArgs) -> dict:
    ctx = tool_ctx.get() or {}
    db = ctx.get("db")
    if db is None:
        return {"ok": False, "error": "no db session in tool context"}
    msg = db.query(ScheduledMessage).get(args.plan_id)
    if msg is None:
        return {"ok": False, "error": "not found"}
    if msg.status not in ("pending_confirmation", "scheduled"):
        return {"ok": False, "error": f"cannot cancel in status {msg.status!r}"}
    cancel_message(msg.id)
    msg.status = "cancelled"
    db.commit()
    return {"ok": True, "plan_id": msg.id, "status": msg.status}


class ListArgs(BaseModel):
    status: Optional[str] = Field(
        default=None,
        description="Optional filter: pending_confirmation, scheduled, sent, failed, cancelled",
    )


@tool(
    name="list_scheduled_messages",
    description=(
        "List HR scheduled messages, optionally filtered by status. "
        "Use when the user asks 'what's scheduled', 'show pending messages', or 'what did I schedule for John'."
    ),
    args_model=ListArgs,
)
def list_scheduled_messages(args: ListArgs) -> dict:
    ctx = tool_ctx.get() or {}
    db = ctx.get("db")
    if db is None:
        return {"ok": False, "error": "no db session in tool context"}
    q = db.query(ScheduledMessage).order_by(ScheduledMessage.scheduled_at_utc.asc())
    if args.status:
        q = q.filter(ScheduledMessage.status == args.status)
    rows = q.all()
    return {
        "ok": True,
        "count": len(rows),
        "messages": [
            {
                "plan_id": m.id,
                "status": m.status,
                "intent": m.intent,
                "scheduled_at_utc": m.scheduled_at_utc.isoformat(),
                "draft_subject": m.draft_subject,
                "recipients": [r.get("name") for r in (m.recipient_payload or [])],
            }
            for m in rows
        ],
    }
