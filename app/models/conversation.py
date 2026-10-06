from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base


class Conversation(Base):
    """
    Represents a private one-to-one conversation between two users.

    Designed to be future-compatible: other message types (e.g. SingingMessage)
    can later be added as separate models that FK to this conversation.
    """
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    participants = relationship("ConversationParticipant", back_populates="conversation", cascade="all, delete-orphan")


class ConversationParticipant(Base):
    """
    Join table linking users to conversations.
    A one-to-one conversation always has exactly 2 participants.

    Using a separate table (rather than two FK columns on Conversation) keeps
    the schema open for potential group conversations later without migration pain.
    """
    __tablename__ = "conversation_participants"

    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Enforce uniqueness at the DB level as well (composite PK already does this)
    __table_args__ = (
        UniqueConstraint("conversation_id", "user_id", name="uq_participant"),
    )

    # Relationships
    conversation = relationship("Conversation", back_populates="participants")
    user = relationship("User")
