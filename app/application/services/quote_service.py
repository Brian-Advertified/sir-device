from sqlalchemy.orm import Session

from app.application.services.notification_service import NotificationService
from app.core.constants import REFERENCE_PREFIX_QUOTE
from app.core.errors import ValidationError
from app.core.ids import new_reference
from app.domain.enums import NotificationTemplate, QuoteStatus
from app.infrastructure.db.models import BusinessQuote
from app.infrastructure.repositories.application_repository import ApplicationRepository


class QuoteService:
    def __init__(self, session: Session, sales_team_email: str | None = None) -> None:
        self._quotes = ApplicationRepository(session)
        self._notifications = NotificationService(session)
        self._sales_team_email = sales_team_email

    def create(
        self,
        *,
        user_id: str | None,
        company_name: str,
        contact_name: str,
        email: str,
        phone: str,
        details: dict[str, str],
    ) -> BusinessQuote:
        required = (company_name, contact_name, email, phone)
        if any(not value.strip() for value in required):
            raise ValidationError("Complete the required company and contact fields")
        quote = BusinessQuote(
            reference=new_reference(REFERENCE_PREFIX_QUOTE),
            user_id=user_id,
            status=QuoteStatus.SUBMITTED,
            company_name=company_name.strip(),
            contact_name=contact_name.strip(),
            email=email.strip().lower(),
            phone=phone.strip(),
            details={key: value.strip() for key, value in details.items()},
        )
        self._quotes.add_quote(quote)
        self._notifications.enqueue_email(
            recipient=quote.email,
            template_key=NotificationTemplate.BUSINESS_QUOTE_SUBMITTED.value,
            payload={"reference": quote.reference},
        )
        if self._sales_team_email:
            self._notifications.enqueue_email(
                recipient=self._sales_team_email,
                template_key=NotificationTemplate.SALES_QUOTE_RECEIVED.value,
                payload={"reference": quote.reference, "company_name": quote.company_name},
            )
        return quote

    def change_status(self, quote_id: str, status: QuoteStatus) -> BusinessQuote:
        quotes = self._quotes.list_quotes(limit=1000)
        quote = next((item for item in quotes if item.id == quote_id), None)
        if not quote:
            raise ValidationError("Quote request not found")
        quote.status = status
        self._notifications.enqueue_email(
            recipient=quote.email,
            template_key=NotificationTemplate.BUSINESS_QUOTE_STATUS_CHANGED.value,
            payload={"reference": quote.reference, "status": status.value},
        )
        return quote
