from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.base_class import Base


class MessageType(str, enum.Enum):
    """
    Discriminator for polymorphic message types.
    Currently only TEXT is implemented.
    SINGING is reserved for future integration by the main backend owner.
    """
    TEXT = "text"
    SINGING = "singing"  # Reserved — DO NOT implement yet


class Message(Base):
    """
    A message inside a conversation.

    The `message_type` column is the extension point for the future singing system.
    When the main backend owner adds singing messages they can:
      - Filter/query by message_type
      - Add a SingingMessage table that FKs to this Message (one-to-one)
      - Or store audio metadata in additional nullable columns here

    For Phase 4 only TEXT messages are sent/received.
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content = Column(String, nullable=True)   # nullable for future singing messages that have no text
    message_type = Column(
        String,
        nullable=False,
        default=MessageType.TEXT,
        index=True,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    conversation = relationship("Conversation")
    sender = relationship("User")
