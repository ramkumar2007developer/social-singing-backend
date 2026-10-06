from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.message import MessageCreate, MessageResponse
from app.services.message import message_service

router = APIRouter()


@router.post("", response_model=MessageResponse)
def send_message(
    conversation_id: int,
    message_in: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send a text message in a specific conversation.
    """
    return message_service.send_text_message(
        db,
        conversation_id=conversation_id,
        sender_id=current_user.id,
        message_in=message_in,
    )


@router.get("", response_model=List[MessageResponse])
def list_messages(
    conversation_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List messages in a specific conversation (oldest first).
    Supports pagination with skip and limit.
    """
    return message_service.get_messages(
        db,
        conversation_id=conversation_id,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )
