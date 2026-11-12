from pydantic import BaseModel
from typing import List, Optional


class SessionSummary(BaseModel):
    id: str
    title: str
    message_count: int
    created_at: str
    updated_at: str


class SessionListResponse(BaseModel):
    status: str
    total_sessions: int
    sessions: List[SessionSummary]


class SessionMessageItem(BaseModel):
    id: str
    role: str
    content: str
    intent: Optional[str] = None
    created_at: str


class SessionMessagesResponse(BaseModel):
    status: str
    session_id: str
    title: str
    total_messages: int
    messages: List[SessionMessageItem]


class SessionDeleteResponse(BaseModel):
    status: str
    session_id: str
    message: str