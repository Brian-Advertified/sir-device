from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, ValidationError
from app.infrastructure.db.models import User
from app.infrastructure.repositories.catalog_repository import CatalogRepository
from app.infrastructure.repositories.identity_repository import IdentityRepository


class CustomerService:
    def __init__(self, session: Session) -> None:
        self._users = IdentityRepository(session)
        self._catalogue = CatalogRepository(session)

    def update_profile(
        self,
        *,
        user_id: str,
        full_name: str,
        phone: str | None,
    ) -> User:
        user = self._users.get_by_id(user_id)
        if not user:
            raise NotFoundError("Customer account not found")
        if not full_name.strip():
            raise ValidationError("Full name is required")
        user.full_name = full_name.strip()
        user.phone = phone.strip() if phone else None
        return user

    def save_product(self, *, user_id: str, product_id: str) -> None:
        if not self._catalogue.get_product(product_id):
            raise NotFoundError("Product not found")
        self._catalogue.save_product_for_user(user_id, product_id)

    def remove_saved_product(self, *, user_id: str, product_id: str) -> None:
        self._catalogue.remove_saved_product(user_id, product_id)
