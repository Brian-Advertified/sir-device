from sqlalchemy.orm import Session

from app.infrastructure.repositories.application_repository import ApplicationRepository
from app.infrastructure.repositories.commerce_repository import CommerceRepository


class StatusService:
    def __init__(self, session: Session) -> None:
        self._applications = ApplicationRepository(session)
        self._commerce = CommerceRepository(session)

    def find(self, *, reference: str, email: str):
        normalised_reference = reference.strip().upper()
        normalised_email = email.strip().lower()
        record = self._applications.find_status_record(normalised_reference, normalised_email)
        if record:
            return record
        order = self._commerce.get_order_by_reference(normalised_reference)
        if order and order.email == normalised_email:
            return order
        return None
