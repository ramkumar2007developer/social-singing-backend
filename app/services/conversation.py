from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.repositories.conversation import conversation_repo
from app.repositories.user import user_repo
from app.models.conversation import Conversation


class ConversationService:

    def get_or_create(
        self, db: Session, current_user_id: int, participant_id: int
    ) -> Conversation:
        """
        Create a private one-to-one conversation between current_user and participant.
        If one already exists, return it instead (idempotent).
        """
        if current_user_id == participant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create a conversation with yourself",
            )

        other_user = user_repo.get(db, user_id=participant_id)
        if not other_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        existing = conversation_repo.get_between_users(db, current_user_id, participant_id)
        if existing:
            return existing

        return conversation_repo.create(db, current_user_id, participant_id)

    def list_conversations(self, db: Session, user_id: int) -> List[Conversation]:
        return conversation_repo.list_for_user(db, user_id)

    def get_conversation(
        self, db: Session, conversation_id: int, current_user_id: int
    ) -> Conversation:
        """Retrieve a conversation, enforcing participant authorization."""
        conversation = conversation_repo.get(db, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        if not conversation_repo.is_participant(db, conversation_id, current_user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this conversation",
            )
        return conversation

    def assert_participant(
        self, db: Session, conversation_id: int, user_id: int
    ) -> None:
        """
        Shared authorization guard used by the Message service.
        Raises 403 if the user is not a participant.
        Raises 404 if the conversation does not exist.
        """
        conversation = conversation_repo.get(db, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        if not conversation_repo.is_participant(db, conversation_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this conversation",
            )


conversation_service = ConversationService()
