from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.enums import NotificationStatus
from app.infrastructure.db.models import (
    AuditLog,
    BusinessQuote,
    ContractApplication,
    NotificationOutbox,
    Order,
    SupportTicket,
)


class OperationsRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_audit(
        self,
        *,
        actor_user_id: str | None,
        action: str,
        entity_type: str,
        entity_id: str | None,
        details: dict,
    ) -> AuditLog:
        audit = AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            created_at=datetime.now(UTC).isoformat(),
        )
        self._session.add(audit)
        self._session.flush()
        return audit

    def add_notification(self, notification: NotificationOutbox) -> NotificationOutbox:
        self._session.add(notification)
        self._session.flush()
        return notification

    def pending_notifications(self, limit: int = 50) -> list[NotificationOutbox]:
        statement = (
            select(NotificationOutbox)
            .where(NotificationOutbox.status == NotificationStatus.PENDING)
            .order_by(NotificationOutbox.created_at)
            .limit(limit)
        )
        return list(self._session.scalars(statement))

    def add_support_ticket(self, ticket: SupportTicket) -> SupportTicket:
        self._session.add(ticket)
        self._session.flush()
        return ticket

    def list_support_tickets(self, limit: int = 300) -> list[SupportTicket]:
        statement = select(SupportTicket).order_by(SupportTicket.created_at.desc()).limit(limit)
        return list(self._session.scalars(statement))

    def dashboard_counts(self) -> dict[str, int]:
        models = {
            "orders": Order,
            "applications": ContractApplication,
            "quotes": BusinessQuote,
            "support": SupportTicket,
        }
        return {
            key: int(self._session.scalar(select(func.count()).select_from(model)) or 0)
            for key, model in models.items()
        }
