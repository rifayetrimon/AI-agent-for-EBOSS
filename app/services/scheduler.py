import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from app.db.models import ScheduledMessage
from app.db.session import SessionLocal
from app.services.send_client import send_message

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone="UTC")


def _job_id(message_id: int) -> str:
    return f"scheduled-message-{message_id}"


def dispatch(message_id: int) -> None:
    """Called by APScheduler at scheduled_at_utc — sends the drafted message."""
    db = SessionLocal()
    try:
        msg = db.query(ScheduledMessage).get(message_id)
        if msg is None:
            logger.error("[dispatch] message %s not found", message_id)
            return
        if msg.status not in ("scheduled",):
            logger.info("[dispatch] message %s skipped (status=%s)", message_id, msg.status)
            return

        payload = {
            "recipient_ids": msg.recipient_ids,
            "recipients": msg.recipient_payload,
            "channel": msg.channel,
            "subject": msg.draft_subject,
            "html": msg.draft_html,
            "sms": msg.draft_sms,
            "intent": msg.intent,
            "scheduled_message_id": msg.id,
        }

        try:
            send_message(payload)
            msg.status = "sent"
            msg.sent_at = datetime.now(timezone.utc)
            msg.error = None
        except Exception as e:
            logger.exception("[dispatch] send failed for message %s", message_id)
            msg.status = "failed"
            msg.error = str(e)

        db.commit()
    finally:
        db.close()


def schedule_message(message_id: int, run_at_utc: datetime) -> None:
    scheduler.add_job(
        dispatch,
        trigger="date",
        run_date=run_at_utc,
        args=[message_id],
        id=_job_id(message_id),
        replace_existing=True,
        misfire_grace_time=60 * 10,
    )


def cancel_message(message_id: int) -> None:
    try:
        scheduler.remove_job(_job_id(message_id))
    except Exception:
        pass


def start_scheduler() -> None:
    if scheduler.running:
        return
    scheduler.start()
    _rehydrate_jobs()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)


def _rehydrate_jobs() -> None:
    """On startup, re-register APScheduler jobs for any rows still 'scheduled' with a future time."""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        rows = (
            db.query(ScheduledMessage)
            .filter(ScheduledMessage.status == "scheduled")
            .all()
        )
        rehydrated = 0
        for msg in rows:
            if msg.scheduled_at_utc <= now:
                msg.status = "failed"
                msg.error = "missed dispatch window before server restart"
                continue
            schedule_message(msg.id, msg.scheduled_at_utc.replace(tzinfo=timezone.utc))
            rehydrated += 1
        db.commit()
        logger.info("[scheduler] rehydrated %d pending job(s)", rehydrated)
    finally:
        db.close()
