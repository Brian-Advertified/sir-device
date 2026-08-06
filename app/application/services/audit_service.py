from sqlalchemy.orm import Session

from app.infrastructure.repositories.operations_repository import OperationsRepository


class AuditService:
    def __init__(self, session: Session) -> None:
        self._operations = OperationsRepository(session)

    def record(
        self,
        *,
        actor_user_id: str | None,
        action: str,
        entity_type: str,
        entity_id: str | None,
        details: dict | None = None,
    ) -> None:
        self._operations.add_audit(
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details or {},
        )
