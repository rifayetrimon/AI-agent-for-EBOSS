from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class StaffRecord(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    dob: Optional[str] = None


class AgentCommandRequest(BaseModel):
    command: str
    staff: List[StaffRecord]
    user_timezone: str = "UTC"


class ParsedPlan(BaseModel):
    intent: str = Field(description="Short slug like birthday_wish, vacation_wish, reminder, announcement")
    intent_description: str = Field(description="One-sentence summary of what the message should convey")
    recipient_ids: List[int]
    channel: Literal["email", "sms", "both"]
    scheduled_at_iso: str = Field(description="ISO 8601 with offset, in the user's timezone")
    tone: str = "friendly"
    warnings: List[str] = []


class DraftedContent(BaseModel):
    subject: Optional[str] = None
    html: Optional[str] = None
    sms: Optional[str] = None


class ScheduledMessageOut(BaseModel):
    id: int
    status: str
    intent: str
    intent_description: str
    channel: str
    tone: str
    scheduled_at_utc: datetime
    user_timezone: str
    recipients: List[StaffRecord]
    draft_subject: Optional[str]
    draft_html: Optional[str]
    draft_sms: Optional[str]
    warnings: List[str]
    created_at: datetime
    confirmed_at: Optional[datetime]
    sent_at: Optional[datetime]
    error: Optional[str]

    class Config:
        from_attributes = True


class AgentCommandResponse(BaseModel):
    plan_id: int
    status: str
    plan: ScheduledMessageOut
    needs_confirmation: bool = True
