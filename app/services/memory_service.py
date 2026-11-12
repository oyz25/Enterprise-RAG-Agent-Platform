from datetime import datetime, timezone
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
        Record a chat message in PostgreSQL and auto-title new sessions from the first user prompt.
        """
        session = self.get_or_create_session(session_id)

        if role == "user" and (not session.title or session.title == "New Conversation"):
            clean_title = " ".join(content.strip().split())
            session.title = clean_title[:45] + ("..." if len(clean_title) > 45 else "")

        session.updated_at = datetime.now(timezone.utc)

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

    def list_sessions(self, limit: int = 30) -> List[Dict[str, Any]]:
        """
        List recent chat sessions ordered by most recently updated.
        """
        sessions = (
            self.db.query(ChatSession)
            .order_by(ChatSession.updated_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": s.id,
                "title": s.title or "New Conversation",
                "message_count": len(s.messages),
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat() if s.updated_at else s.created_at.isoformat(),
            }
            for s in sessions
        ]

    def get_session_messages(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch full chronological message log for a specific session ID.
        """
        session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            return None

        messages = (
            self.db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )
        return {
            "session_id": session.id,
            "title": session.title or "New Conversation",
            "messages": [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "intent": m.intent,
                    "created_at": m.created_at.isoformat(),
                }
                for m in messages
            ],
        }

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a chat session and all associated messages via cascade.
        """
        session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            return False

        self.db.delete(session)
        self.db.commit()
        return True