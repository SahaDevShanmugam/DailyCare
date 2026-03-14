from datetime import datetime
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    recent_summary: str = ""


class ChatResponse(BaseModel):
    response: str


class ChatMessageRead(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}
