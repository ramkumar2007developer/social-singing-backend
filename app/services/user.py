from sqlalchemy.orm import Session
from app.repositories.user import user_repo
from app.schemas.user import UserCreate
from app.models.user import User
from fastapi import HTTPException, status

class UserService:
    def create_user(self, db: Session, user_in: UserCreate) -> User:
        user = user_repo.get_by_email(db, email=user_in.email)
        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The user with this email already exists in the system.",
            )
        user = user_repo.get_by_username(db, username=user_in.username)
        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The user with this username already exists in the system.",
            )
        return user_repo.create(db, obj_in=user_in)

    def get_user(self, db: Session, user_id: int) -> User:
        user = user_repo.get(db, user_id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

user_service = UserService()
