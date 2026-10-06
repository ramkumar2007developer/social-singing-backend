from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FriendRequestCreate(BaseModel):
    receiver_id: int

class FriendRequestResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}

class FriendshipResponse(BaseModel):
    user_id: int
    friend_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
