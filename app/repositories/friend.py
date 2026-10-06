from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.models.friend import FriendRequest, Friendship

class FriendRepository:
    def get_request(self, db: Session, request_id: int) -> Optional[FriendRequest]:
        return db.query(FriendRequest).filter(FriendRequest.id == request_id).first()

    def get_active_request(self, db: Session, sender_id: int, receiver_id: int) -> Optional[FriendRequest]:
        return db.query(FriendRequest).filter(
            FriendRequest.sender_id == sender_id,
            FriendRequest.receiver_id == receiver_id,
            FriendRequest.status == "pending"
        ).first()

    def get_any_active_request_between(self, db: Session, user1_id: int, user2_id: int) -> Optional[FriendRequest]:
        return db.query(FriendRequest).filter(
            FriendRequest.status == "pending",
            or_(
                and_(FriendRequest.sender_id == user1_id, FriendRequest.receiver_id == user2_id),
                and_(FriendRequest.sender_id == user2_id, FriendRequest.receiver_id == user1_id)
            )
        ).first()

    def create_request(self, db: Session, sender_id: int, receiver_id: int) -> FriendRequest:
        req = FriendRequest(sender_id=sender_id, receiver_id=receiver_id)
        db.add(req)
        db.commit()
        db.refresh(req)
        return req

    def update_request_status(self, db: Session, req: FriendRequest, status: str):
        req.status = status
        db.commit()
        db.refresh(req)
        return req

    def get_pending_requests(self, db: Session, user_id: int) -> List[FriendRequest]:
        return db.query(FriendRequest).filter(
            FriendRequest.receiver_id == user_id,
            FriendRequest.status == "pending"
        ).all()

    def is_friend(self, db: Session, user1_id: int, user2_id: int) -> bool:
        return db.query(Friendship).filter(
            Friendship.user_id == user1_id,
            Friendship.friend_id == user2_id
        ).first() is not None

    def add_friendship(self, db: Session, user1_id: int, user2_id: int):
        f1 = Friendship(user_id=user1_id, friend_id=user2_id)
        f2 = Friendship(user_id=user2_id, friend_id=user1_id)
        db.add_all([f1, f2])
        db.commit()

    def remove_friendship(self, db: Session, user1_id: int, user2_id: int):
        db.query(Friendship).filter(
            or_(
                and_(Friendship.user_id == user1_id, Friendship.friend_id == user2_id),
                and_(Friendship.user_id == user2_id, Friendship.friend_id == user1_id)
            )
        ).delete()
        db.commit()

    def get_friends(self, db: Session, user_id: int) -> List[Friendship]:
        return db.query(Friendship).filter(Friendship.user_id == user_id).all()

friend_repo = FriendRepository()
