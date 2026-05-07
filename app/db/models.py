from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from app.db.session import Base


class ScheduledMessage(Base):
    __tablename__ = "scheduled_messages"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user_command = Column(Text, nullable=False)
    user_timezone = Column(String, nullable=False, default="UTC")

    intent = Column(String, nullable=False)
    intent_description = Column(Text, nullable=False)
    recipient_ids = Column(JSON, nullable=False)
    recipient_payload = Column(JSON, nullable=False)
    channel = Column(String, nullable=False)
    tone = Column(String, nullable=False, default="friendly")
    scheduled_at_utc = Column(DateTime, nullable=False, index=True)

    draft_subject = Column(String, nullable=True)
    draft_html = Column(Text, nullable=True)
    draft_sms = Column(String, nullable=True)

    status = Column(String, nullable=False, default="pending_confirmation", index=True)
    confirmed_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)
    warnings = Column(JSON, nullable=False, default=list)
