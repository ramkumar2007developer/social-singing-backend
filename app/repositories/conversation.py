from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.models.conversation import Conversation, ConversationParticipant


class ConversationRepository:

    # ------------------------------------------------------------------
    # Conversation queries
    # ------------------------------------------------------------------

    def get(self, db: Session, conversation_id: int) -> Optional[Conversation]:
        return db.query(Conversation).filter(Conversation.id == conversation_id).first()

    def get_between_users(
        self, db: Session, user1_id: int, user2_id: int
    ) -> Optional[Conversation]:
        """
        Return the existing one-to-one conversation between two users, or None.
        Uses a self-join on conversation_participants to find conversations
        where both users are participants.
        """
        cp1 = ConversationParticipant
        cp2 = ConversationParticipant

        result = (
            db.query(Conversation)
            .join(cp1, cp1.conversation_id == Conversation.id)
            .filter(cp1.user_id == user1_id)
            .filter(
                Conversation.id.in_(
                    db.query(cp2.conversation_id).filter(cp2.user_id == user2_id)
                )
            )
            .first()
        )
        return result

    def create(self, db: Session, user1_id: int, user2_id: int) -> Conversation:
        """Create a new conversation and add both participants atomically."""
        conversation = Conversation()
        db.add(conversation)
        db.flush()   # get conversation.id before committing

        p1 = ConversationParticipant(conversation_id=conversation.id, user_id=user1_id)
        p2 = ConversationParticipant(conversation_id=conversation.id, user_id=user2_id)
        db.add_all([p1, p2])
        db.commit()
        db.refresh(conversation)
        return conversation

    def list_for_user(self, db: Session, user_id: int) -> List[Conversation]:
        """Return all conversations the user participates in, newest first."""
        return (
            db.query(Conversation)
            .join(ConversationParticipant, ConversationParticipant.conversation_id == Conversation.id)
            .filter(ConversationParticipant.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .all()
        )

    # ------------------------------------------------------------------
    # Participant queries
    # ------------------------------------------------------------------

    def is_participant(self, db: Session, conversation_id: int, user_id: int) -> bool:
        return (
            db.query(ConversationParticipant)
            .filter(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.user_id == user_id,
            )
            .first()
            is not None
        )


conversation_repo = ConversationRepository()
