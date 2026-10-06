from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.repositories.message import message_repo
from app.services.conversation import conversation_service
from app.schemas.message import MessageCreate
from app.models.message import Message


class MessageService:

    def send_text_message(
        self,
        db: Session,
        conversation_id: int,
        sender_id: int,
        message_in: MessageCreate,
    ) -> Message:
        """
        Send a text message in a conversation.
        Raises 403 or 404 via conversation_service if not authorized.
        """
        # Ensure sender is part of this conversation
        conversation_service.assert_participant(db, conversation_id, sender_id)

        # The message content validation is already handled by Pydantic MessageCreate
        return message_repo.create(
            db,
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=message_in.content,
        )

    def get_messages(
        self,
        db: Session,
        conversation_id: int,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Message]:
        """
        List messages for a conversation, newest first? Wait, the natural chat order is oldest first.
        Raises 403 or 404 via conversation_service if not authorized.
        """
        # Ensure reader is part of this conversation
        conversation_service.assert_participant(db, conversation_id, user_id)

        return message_repo.list_for_conversation(
            db, conversation_id=conversation_id, skip=skip, limit=limit
        )


message_service = MessageService()
