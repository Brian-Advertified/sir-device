from sqlalchemy.orm import Session

from app.core.errors import AuthenticationError, ValidationError
from app.core.security import hash_password, verify_password
from app.domain.enums import UserRole
from app.infrastructure.db.models import User
from app.infrastructure.repositories.identity_repository import IdentityRepository


class AuthService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._users = IdentityRepository(session)

    @staticmethod
    def _normalise_email(email: str) -> str:
        normalised = email.strip().lower()
        if "@" not in normalised or len(normalised) > 320:
            raise ValidationError("Enter a valid email address")
        return normalised

    def register_customer(
        self, *, email: str, password: str, full_name: str, phone: str | None
    ) -> User:
        normalised_email = self._normalise_email(email)
        if self._users.get_by_email(normalised_email):
            raise ValidationError("An account already exists for this email address")
        if not full_name.strip():
            raise ValidationError("Full name is required")
        user = User(
            email=normalised_email,
            password_hash=hash_password(password),
            full_name=full_name.strip(),
            phone=phone.strip() if phone else None,
            role=UserRole.CUSTOMER,
        )
        return self._users.add(user)

    def create_staff_user(
        self,
        *,
        email: str,
        password: str,
        full_name: str,
        phone: str | None,
        role: UserRole,
    ) -> User:
        if role == UserRole.CUSTOMER:
            raise ValidationError("Use customer registration for customer accounts")
        normalised_email = self._normalise_email(email)
        if self._users.get_by_email(normalised_email):
            raise ValidationError("An account already exists for this email address")
        user = User(
            email=normalised_email,
            password_hash=hash_password(password),
            full_name=full_name.strip(),
            phone=phone.strip() if phone else None,
            role=role,
        )
        return self._users.add(user)

    def authenticate(self, email: str, password: str) -> User:
        user = self._users.get_by_email(self._normalise_email(email))
        if not user or not user.is_active or not verify_password(password, user.password_hash):
            raise AuthenticationError("The email address or password is incorrect")
        return user
