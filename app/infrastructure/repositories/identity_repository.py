from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.db.models import User


class IdentityRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, user_id: str) -> User | None:
        return self._session.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email.strip().lower())
        return self._session.scalar(statement)

    def add(self, user: User) -> User:
        self._session.add(user)
        self._session.flush()
        return user

    def list_users(self, limit: int = 200) -> list[User]:
        statement = select(User).order_by(User.created_at.desc()).limit(limit)
        return list(self._session.scalars(statement))
