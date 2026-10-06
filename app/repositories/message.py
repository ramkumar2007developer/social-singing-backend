from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import asc
from app.models.message import Message, MessageType


class MessageRepository:

    def create(
        self,
        db: Session,
        conversation_id: int,
        sender_id: int,
        content: str,
        message_type: str = MessageType.TEXT,
    ) -> Message:
        msg = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=content,
            message_type=message_type,
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return msg

    def list_for_conversation(
        self,
        db: Session,
        conversation_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Message]:
        """
        Return messages for a conversation ordered by created_at ascending
        (oldest first — natural chat reading order).
        Pagination via skip/limit.
        """
        return (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(asc(Message.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_for_conversation(self, db: Session, conversation_id: int) -> int:
        return (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .count()
        )


message_repo = MessageRepository()
