from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.conversation import ConversationCreate, ConversationResponse
from app.services.conversation import conversation_service

router = APIRouter()


@router.post("", response_model=ConversationResponse, status_code=200)
def create_or_get_conversation(
    conversation_in: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a private conversation with another user.
    If a conversation already exists between the two users, return it.
    Sender is always derived from the authenticated token — never from the request body.
    """
    return conversation_service.get_or_create(
        db, current_user.id, conversation_in.participant_id
    )


@router.get("", response_model=List[ConversationResponse])
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all conversations the current user participates in, newest first."""
    return conversation_service.list_conversations(db, current_user.id)


@router.get("/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve a specific conversation by ID.
    Returns 403 if the current user is not a participant.
    Returns 404 if the conversation does not exist.
    """
    return conversation_service.get_conversation(db, conversation_id, current_user.id)
