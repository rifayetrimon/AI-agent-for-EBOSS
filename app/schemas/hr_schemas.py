from pydantic import BaseModel
from typing import List, Optional

class DraftMessageRequest(BaseModel):
    recipient_list: List[str]
    sender: str
    prompt: str
    tone: Optional[str] = "formal"

class DraftMessageResponse(BaseModel):
    subject: str
    html: str
    sms: str
