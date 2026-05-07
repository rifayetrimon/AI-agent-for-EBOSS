from pydantic import BaseModel
from typing import List, Optional

class NewsMetaRequest(BaseModel):
    body_text: str
    target_audience: Optional[str] = "general public"

class NewsMetaResponse(BaseModel):
    headlines: List[str]
    summary: str
    slug: str
