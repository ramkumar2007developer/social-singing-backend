from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional
from app.models.message import MessageType


MAX_MESSAGE_LENGTH = 4000   # characters


class MessageCreate(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Message content must not be empty or whitespace only")
        if len(stripped) > MAX_MESSAGE_LENGTH:
            raise ValueError(
                f"Message content must not exceed {MAX_MESSAGE_LENGTH} characters"
            )
        return stripped   # store trimmed value


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    content: Optional[str]
    message_type: str
    created_at: datetime

    model_config = {"from_attributes": True}
