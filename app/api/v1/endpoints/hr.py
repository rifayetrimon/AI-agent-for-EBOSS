from datetime import datetime, timezone
from typing import List, Optional

from dateutil import parser as date_parser
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.agents.hr.crew import run_draft_message_crew
from app.agents.hr.drafter import run_drafter_crew
from app.agents.hr.parser import run_parser_crew
from app.db.models import ScheduledMessage
from app.db.session import get_db
from app.schemas.agent_schemas import (
    AgentCommandRequest,
    AgentCommandResponse,
    ScheduledMessageOut,
    StaffRecord,
)
from app.schemas.hr_schemas import DraftMessageRequest, DraftMessageResponse
from app.services.scheduler import cancel_message, schedule_message

router = APIRouter()


@router.post("/draft-message", response_model=DraftMessageResponse)
def draft_message(request: DraftMessageRequest):
    try:
        return run_draft_message_crew(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _to_out(msg: ScheduledMessage) -> ScheduledMessageOut:
    return ScheduledMessageOut(
        id=msg.id,
        status=msg.status,
        intent=msg.intent,
        intent_description=msg.intent_description,
        channel=msg.channel,
        tone=msg.tone,
        scheduled_at_utc=msg.scheduled_at_utc,
        user_timezone=msg.user_timezone,
        recipients=[StaffRecord(**r) for r in msg.recipient_payload],
        draft_subject=msg.draft_subject,
        draft_html=msg.draft_html,
        draft_sms=msg.draft_sms,
        warnings=msg.warnings or [],
        created_at=msg.created_at,
        confirmed_at=msg.confirmed_at,
        sent_at=msg.sent_at,
        error=msg.error,
    )


@router.post("/agent-command", response_model=AgentCommandResponse)
def agent_command(req: AgentCommandRequest, db: Session = Depends(get_db)):
    if not req.staff:
        raise HTTPException(status_code=400, detail="staff list cannot be empty")

    try:
        plan = run_parser_crew(req.command, req.staff, req.user_timezone)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"parser failed: {e}")

    staff_by_id = {s.id: s for s in req.staff}
    resolved_recipients = [staff_by_id[i] for i in plan.recipient_ids if i in staff_by_id]
    warnings = list(plan.warnings or [])
    missing = [i for i in plan.recipient_ids if i not in staff_by_id]
    if missing:
        warnings.append(f"agent referenced unknown staff ids: {missing}")
    if not resolved_recipients:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "no valid recipients resolved from the command",
                "warnings": warnings,
                "plan": plan.model_dump(),
            },
        )

    try:
        scheduled_at = date_parser.isoparse(plan.scheduled_at_iso)
    except Exception:
        raise HTTPException(status_code=422, detail=f"invalid scheduled_at_iso: {plan.scheduled_at_iso!r}")
    if scheduled_at.tzinfo is None:
        raise HTTPException(status_code=422, detail="scheduled_at_iso must include a timezone offset")
    scheduled_at_utc = scheduled_at.astimezone(timezone.utc).replace(tzinfo=None)
    if scheduled_at_utc <= datetime.utcnow():
        raise HTTPException(status_code=422, detail="scheduled_at_iso is in the past")

    try:
        draft = run_drafter_crew(plan, resolved_recipients)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"drafter failed: {e}")

    msg = ScheduledMessage(
        user_command=req.command,
        user_timezone=req.user_timezone,
        intent=plan.intent,
        intent_description=plan.intent_description,
        recipient_ids=[r.id for r in resolved_recipients],
        recipient_payload=[r.model_dump(exclude_none=True) for r in resolved_recipients],
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

    return AgentCommandResponse(
        plan_id=msg.id,
        status=msg.status,
        plan=_to_out(msg),
        needs_confirmation=True,
    )


@router.post("/agent-command/{plan_id}/confirm", response_model=ScheduledMessageOut)
def confirm_plan(plan_id: int, db: Session = Depends(get_db)):
    msg = db.query(ScheduledMessage).get(plan_id)
    if msg is None:
        raise HTTPException(status_code=404, detail="plan not found")
    if msg.status != "pending_confirmation":
        raise HTTPException(status_code=409, detail=f"cannot confirm in status {msg.status!r}")
    if msg.scheduled_at_utc <= datetime.utcnow():
        raise HTTPException(status_code=409, detail="scheduled_at is in the past — recreate the plan")

    schedule_message(msg.id, msg.scheduled_at_utc.replace(tzinfo=timezone.utc))
    msg.status = "scheduled"
    msg.confirmed_at = datetime.utcnow()
    db.commit()
    db.refresh(msg)
    return _to_out(msg)


@router.get("/scheduled-messages", response_model=List[ScheduledMessageOut])
def list_scheduled(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(ScheduledMessage).order_by(ScheduledMessage.scheduled_at_utc.asc())
    if status:
        q = q.filter(ScheduledMessage.status == status)
    return [_to_out(m) for m in q.all()]


@router.get("/scheduled-messages/{message_id}", response_model=ScheduledMessageOut)
def get_scheduled(message_id: int, db: Session = Depends(get_db)):
    msg = db.query(ScheduledMessage).get(message_id)
    if msg is None:
        raise HTTPException(status_code=404, detail="not found")
    return _to_out(msg)


@router.delete("/scheduled-messages/{message_id}", response_model=ScheduledMessageOut)
def cancel_scheduled(message_id: int, db: Session = Depends(get_db)):
    msg = db.query(ScheduledMessage).get(message_id)
    if msg is None:
        raise HTTPException(status_code=404, detail="not found")
    if msg.status not in ("pending_confirmation", "scheduled"):
        raise HTTPException(status_code=409, detail=f"cannot cancel in status {msg.status!r}")
    cancel_message(msg.id)
    msg.status = "cancelled"
    db.commit()
    db.refresh(msg)
    return _to_out(msg)
