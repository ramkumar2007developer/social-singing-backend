from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.friend import FriendRequestCreate, FriendRequestResponse, FriendshipResponse
from app.services.friend import friend_service

router = APIRouter()

@router.post("/requests", response_model=FriendRequestResponse)
def send_friend_request(
    request_in: FriendRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return friend_service.send_request(db, current_user.id, request_in.receiver_id)

@router.get("/requests", response_model=List[FriendRequestResponse])
def get_pending_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return friend_service.get_pending_requests(db, current_user.id)

@router.post("/requests/{id}/accept", response_model=FriendRequestResponse)
def accept_friend_request(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return friend_service.accept_request(db, current_user.id, id)

@router.post("/requests/{id}/reject", response_model=FriendRequestResponse)
def reject_friend_request(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return friend_service.reject_request(db, current_user.id, id)

@router.get("", response_model=List[FriendshipResponse])
def get_friends_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return friend_service.get_friends(db, current_user.id)

@router.delete("/{user_id}", status_code=204)
def remove_friend(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    friend_service.remove_friend(db, current_user.id, user_id)
