from sqlalchemy.orm import Session

from app.domain.enums import NotificationChannel, NotificationStatus
from app.infrastructure.db.models import NotificationOutbox
from app.infrastructure.repositories.operations_repository import OperationsRepository


class NotificationService:
    def __init__(self, session: Session) -> None:
        self._operations = OperationsRepository(session)

    def enqueue_email(self, *, recipient: str, template_key: str, payload: dict) -> None:
        notification = NotificationOutbox(
            channel=NotificationChannel.EMAIL,
            recipient=recipient.strip().lower(),
            template_key=template_key,
            payload=payload,
            status=NotificationStatus.PENDING,
        )
        self._operations.add_notification(notification)
