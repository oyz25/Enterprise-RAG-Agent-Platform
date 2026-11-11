from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.chat import ChatSession, ChatMessage


class MemoryService:
    """
    Service for persisting, retrieving, and managing conversation state in PostgreSQL.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_or_create_session(self, session_id: str) -> ChatSession:
        """
        Fetch existing session by ID or create a new one if it does not exist.
        """
        session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            session = ChatSession(id=session_id)
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
        return session

    def add_message(
        self, 
        session_id: str, 
        role: str, 
        content: str, 
        intent: Optional[str] = None
    ) -> ChatMessage:
        """
        Record a chat message in PostgreSQL for a given session ID.
        """
        self.get_or_create_session(session_id)
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            intent=intent
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_recent_history(self, session_id: str, limit: int = 6) -> List[Dict[str, Any]]:
        """
        Retrieve recent conversation history formatted for model/agent context window.
        """
        messages = (
            self.db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
            .all()
        )
        messages.reverse()
        return [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "intent": m.intent,
                "created_at": m.created_at.isoformat()
            }
            for m in messages
        ]