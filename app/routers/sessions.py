from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.memory_service import MemoryService
from app.schemas.session import (
    SessionListResponse,
    SessionMessagesResponse,
    SessionDeleteResponse,
)

router = APIRouter(prefix="/api/v1/sessions", tags=["Session Management"])


@router.get("", response_model=SessionListResponse)
def list_sessions(
    limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Retrieve recent conversation sessions stored in PostgreSQL.
    """
    memory_service = MemoryService(db)
    sessions = memory_service.list_sessions(limit=limit)
    return SessionListResponse(
        status="success",
        total_sessions=len(sessions),
        sessions=sessions,
    )


@router.get("/{session_id}/messages", response_model=SessionMessagesResponse)
def get_session_messages(session_id: str, db: Session = Depends(get_db)):
    """
    Retrieve chronological message history for a specific session.
    """
    memory_service = MemoryService(db)
    session_data = memory_service.get_session_messages(session_id)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )

    messages = session_data["messages"]
    return SessionMessagesResponse(
        status="success",
        session_id=session_data["session_id"],
        title=session_data["title"],
        total_messages=len(messages),
        messages=messages,
    )


@router.delete("/{session_id}", response_model=SessionDeleteResponse)
def delete_session(session_id: str, db: Session = Depends(get_db)):
    """
    Delete a conversation session and its message history from PostgreSQL.
    """
    memory_service = MemoryService(db)
    deleted = memory_service.delete_session(session_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )

    return SessionDeleteResponse(
        status="success",
        session_id=session_id,
        message="Session and associated messages deleted successfully.",
    )