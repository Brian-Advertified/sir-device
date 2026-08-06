from app.core.config import get_settings
from app.domain.enums import NotificationStatus, NotificationTemplate
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.notifications.smtp_sender import SmtpEmailSender
from app.infrastructure.repositories.operations_repository import OperationsRepository


SUBJECTS = {
    NotificationTemplate.ORDER_CREATED.value: "Your Sir Device order was created",
    NotificationTemplate.APPLICATION_SUBMITTED.value: "Your Sir Device application was submitted",
    NotificationTemplate.APPLICATION_STATUS_CHANGED.value: "Your Sir Device application status changed",
    NotificationTemplate.BUSINESS_QUOTE_SUBMITTED.value: "Your Sir Device quote request was submitted",
    NotificationTemplate.BUSINESS_QUOTE_STATUS_CHANGED.value: "Your Sir Device quote status changed",
    NotificationTemplate.ORDER_STATUS_CHANGED.value: "Your Sir Device order status changed",
    NotificationTemplate.SALES_QUOTE_RECEIVED.value: "New Sir Device business quote request",
}


def render_body(template_key: str, payload: dict) -> str:
    reference = payload.get("reference", "")
    status = payload.get("status")
    lines = [f"Reference: {reference}"]
    if status:
        lines.append(f"Status: {str(status).replace('_', ' ').title()}")
    lines.append("Sign in or use the request tracker for the latest information.")
    return "\n\n".join(lines)


def main() -> None:
    sender = SmtpEmailSender(get_settings())
    with SessionLocal() as session:
        repository = OperationsRepository(session)
        for notification in repository.pending_notifications():
            try:
                sender.send(
                    recipient=notification.recipient,
                    subject=SUBJECTS.get(notification.template_key, "Sir Device update"),
                    body=render_body(notification.template_key, notification.payload),
                )
                notification.status = NotificationStatus.SENT
                notification.error_message = None
            except Exception as exc:  # noqa: BLE001 - dispatcher records provider failures
                notification.status = NotificationStatus.FAILED
                notification.error_message = str(exc)[:1000]
        session.commit()


if __name__ == "__main__":
    main()
