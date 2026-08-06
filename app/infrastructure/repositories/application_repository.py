from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.infrastructure.db.models import BusinessQuote, ContractApplication, UploadedDocument


class ApplicationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_application(self, application: ContractApplication) -> ContractApplication:
        self._session.add(application)
        self._session.flush()
        return application

    def get_application(self, application_id: str) -> ContractApplication | None:
        statement = (
            select(ContractApplication)
            .options(joinedload(ContractApplication.documents))
            .where(ContractApplication.id == application_id)
        )
        return self._session.scalars(statement).unique().one_or_none()

    def get_application_by_reference(self, reference: str) -> ContractApplication | None:
        statement = (
            select(ContractApplication)
            .options(joinedload(ContractApplication.documents))
            .where(ContractApplication.reference == reference)
        )
        return self._session.scalars(statement).unique().one_or_none()

    def list_applications(
        self, *, user_id: str | None = None, limit: int = 300
    ) -> list[ContractApplication]:
        statement = select(ContractApplication)
        if user_id:
            statement = statement.where(ContractApplication.user_id == user_id)
        statement = statement.order_by(ContractApplication.created_at.desc()).limit(limit)
        return list(self._session.scalars(statement))

    def add_document(self, document: UploadedDocument) -> UploadedDocument:
        self._session.add(document)
        self._session.flush()
        return document

    def add_quote(self, quote: BusinessQuote) -> BusinessQuote:
        self._session.add(quote)
        self._session.flush()
        return quote

    def get_quote_by_reference(self, reference: str) -> BusinessQuote | None:
        return self._session.scalar(
            select(BusinessQuote).where(BusinessQuote.reference == reference)
        )

    def list_quotes(self, *, user_id: str | None = None, limit: int = 300) -> list[BusinessQuote]:
        statement = select(BusinessQuote)
        if user_id:
            statement = statement.where(BusinessQuote.user_id == user_id)
        statement = statement.order_by(BusinessQuote.created_at.desc()).limit(limit)
        return list(self._session.scalars(statement))

    def find_status_record(self, reference: str, email: str):
        application = self._session.scalar(
            select(ContractApplication).where(
                ContractApplication.reference == reference,
                ContractApplication.email == email.lower(),
            )
        )
        if application:
            return application
        return self._session.scalar(
            select(BusinessQuote).where(
                BusinessQuote.reference == reference,
                BusinessQuote.email == email.lower(),
            )
        )
