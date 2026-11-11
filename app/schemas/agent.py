from enum import Enum
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional


class AgentIntent(str, Enum):
    KNOWLEDGE_BASE = "KNOWLEDGE_BASE_QUERY"
    DIRECT_CHAT = "DIRECT_CHAT"
    WEB_SEARCH = "WEB_SEARCH"
    CALCULATOR = "CALCULATOR"


class AgentRequest(BaseModel):
    """
    Schema for Multi-Agent routing request.
    """
    query: str = Field(..., description="User input message or question")
    session_id: Optional[str] = Field(default="default_session", description="Session identifier for state persistence")


class AgentResponse(BaseModel):
    """
    Schema for Multi-Agent router response.
    """
    status: str
    intent: AgentIntent
    confidence_score: float
    reasoning: str
    executed_action: str
    result: Dict[str, Any]