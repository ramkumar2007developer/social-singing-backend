from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.repositories.friend import friend_repo
from app.repositories.user import user_repo
from app.models.friend import FriendRequest, Friendship
from typing import List

class FriendService:
    def send_request(self, db: Session, sender_id: int, receiver_id: int) -> FriendRequest:
        if sender_id == receiver_id:
            raise HTTPException(status_code=400, detail="Cannot send friend request to yourself")
        
        receiver = user_repo.get(db, user_id=receiver_id)
        if not receiver:
            raise HTTPException(status_code=404, detail="User not found")
            
        if friend_repo.is_friend(db, sender_id, receiver_id):
            raise HTTPException(status_code=400, detail="Already friends")
            
        active_req = friend_repo.get_any_active_request_between(db, sender_id, receiver_id)
        if active_req:
            if active_req.sender_id == receiver_id:
                # Reverse request exists, auto-accept it to become friends
                friend_repo.update_request_status(db, active_req, "accepted")
                friend_repo.add_friendship(db, sender_id, receiver_id)
                return active_req
            raise HTTPException(status_code=400, detail="Friend request already pending")
            
        return friend_repo.create_request(db, sender_id=sender_id, receiver_id=receiver_id)

    def accept_request(self, db: Session, user_id: int, request_id: int) -> FriendRequest:
        req = friend_repo.get_request(db, request_id)
        if not req:
            raise HTTPException(status_code=404, detail="Request not found")
        if req.receiver_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to accept this request")
        if req.status != "pending":
            raise HTTPException(status_code=400, detail="Request is already processed")
            
        friend_repo.update_request_status(db, req, "accepted")
        if not friend_repo.is_friend(db, req.sender_id, req.receiver_id):
            friend_repo.add_friendship(db, req.sender_id, req.receiver_id)
            
        return req

    def reject_request(self, db: Session, user_id: int, request_id: int) -> FriendRequest:
        req = friend_repo.get_request(db, request_id)
        if not req:
            raise HTTPException(status_code=404, detail="Request not found")
        if req.receiver_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to reject this request")
        if req.status != "pending":
            raise HTTPException(status_code=400, detail="Request is already processed")
            
        return friend_repo.update_request_status(db, req, "rejected")

    def get_pending_requests(self, db: Session, user_id: int) -> List[FriendRequest]:
        return friend_repo.get_pending_requests(db, user_id)

    def get_friends(self, db: Session, user_id: int) -> List[Friendship]:
        return friend_repo.get_friends(db, user_id)

    def remove_friend(self, db: Session, user_id: int, friend_id: int):
        if not friend_repo.is_friend(db, user_id, friend_id):
            raise HTTPException(status_code=400, detail="Not friends")
        friend_repo.remove_friendship(db, user_id, friend_id)

friend_service = FriendService()
