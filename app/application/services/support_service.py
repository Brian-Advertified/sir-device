from sqlalchemy.orm import Session

from app.core.constants import REFERENCE_PREFIX_SUPPORT
from app.core.errors import ValidationError
from app.core.ids import new_reference
from app.domain.enums import SupportStatus
from app.infrastructure.db.models import SupportTicket
from app.infrastructure.repositories.operations_repository import OperationsRepository


class SupportService:
    def __init__(self, session: Session) -> None:
        self._operations = OperationsRepository(session)

    def create_ticket(
        self,
        *,
        user_id: str | None,
        name: str,
        email: str,
        phone: str | None,
        subject: str,
        message: str,
    ) -> SupportTicket:
        if any(not value.strip() for value in (name, email, subject, message)):
            raise ValidationError("Complete all required support fields")
        ticket = SupportTicket(
            reference=new_reference(REFERENCE_PREFIX_SUPPORT),
            user_id=user_id,
            name=name.strip(),
            email=email.strip().lower(),
            phone=phone.strip() if phone else None,
            subject=subject.strip(),
            message=message.strip(),
            status=SupportStatus.OPEN,
        )
        return self._operations.add_support_ticket(ticket)
