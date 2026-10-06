from pydantic import BaseModel
from datetime import datetime
from typing import List


class ConversationCreate(BaseModel):
    """Client sends only the other participant's ID. Sender comes from current_user."""
    participant_id: int


class ParticipantResponse(BaseModel):
    user_id: int
    joined_at: datetime

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    participants: List[ParticipantResponse]

    model_config = {"from_attributes": True}
