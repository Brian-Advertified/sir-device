from typing import BinaryIO

from sqlalchemy.orm import Session

from app.application.services.notification_service import NotificationService
from app.core.constants import REFERENCE_PREFIX_APPLICATION
from app.core.errors import NotFoundError, ValidationError
from app.core.ids import new_reference
from app.domain.enums import (
    ApplicationIntent,
    ApplicationStatus,
    CustomerType,
    DocumentStatus,
    DocumentType,
    NotificationTemplate,
)
from app.domain.ports import FileStorage
from app.infrastructure.db.models import ContractApplication, UploadedDocument
from app.infrastructure.repositories.application_repository import ApplicationRepository
from app.infrastructure.repositories.catalog_repository import CatalogRepository


class ApplicationService:
    def __init__(self, session: Session, file_storage: FileStorage, max_upload_bytes: int) -> None:
        self._applications = ApplicationRepository(session)
        self._catalogue = CatalogRepository(session)
        self._storage = file_storage
        self._max_upload_bytes = max_upload_bytes
        self._notifications = NotificationService(session)

    def create(
        self,
        *,
        user_id: str | None,
        selected_deal_id: str | None,
        customer_type: CustomerType,
        email: str,
        phone: str,
        details: dict[str, str],
    ) -> ContractApplication:
        if selected_deal_id and not self._catalogue.get_public_deal(selected_deal_id):
            raise ValidationError("The selected offer is no longer available")
        required_common = ("full_name", "address") if customer_type == CustomerType.PERSONAL else (
            "company_name",
            "contact_name",
            "business_address",
        )
        if any(not details.get(field, "").strip() for field in required_common):
            raise ValidationError("Complete all required application fields")
        intent = details.get("intent")
        if intent and intent not in {item.value for item in ApplicationIntent}:
            raise ValidationError("Select a valid application type")
        application = ContractApplication(
            reference=new_reference(REFERENCE_PREFIX_APPLICATION),
            user_id=user_id,
            selected_deal_id=selected_deal_id,
            customer_type=customer_type,
            status=ApplicationStatus.SUBMITTED,
            email=email.strip().lower(),
            phone=phone.strip(),
            details={key: value.strip() for key, value in details.items()},
        )
        self._applications.add_application(application)
        self._notifications.enqueue_email(
            recipient=application.email,
            template_key=NotificationTemplate.APPLICATION_SUBMITTED.value,
            payload={"reference": application.reference},
        )
        return application

    def upload_document(
        self,
        *,
        reference: str,
        document_type: DocumentType,
        source: BinaryIO,
        original_name: str,
        content_type: str,
    ) -> UploadedDocument:
        application = self._applications.get_application_by_reference(reference)
        if not application:
            raise NotFoundError("Application not found")
        allowed_types = {
            "application/pdf",
            "image/jpeg",
            "image/png",
            "image/webp",
        }
        if content_type not in allowed_types:
            raise ValidationError("Upload a PDF, JPEG, PNG or WebP file")
        stored = self._storage.save(
            source=source,
            original_name=original_name,
            content_type=content_type,
            namespace=f"applications/{application.id}",
            max_bytes=self._max_upload_bytes,
        )
        document = UploadedDocument(
            application_id=application.id,
            document_type=document_type,
            status=DocumentStatus.RECEIVED,
            storage_key=stored.key,
            original_name=original_name,
            content_type=stored.content_type,
            size_bytes=stored.size_bytes,
        )
        self._applications.add_document(document)
        return document

    def change_status(
        self,
        *,
        application_id: str,
        status: ApplicationStatus,
    ) -> ContractApplication:
        application = self._applications.get_application(application_id)
        if not application:
            raise NotFoundError("Application not found")
        application.status = status
        self._notifications.enqueue_email(
            recipient=application.email,
            template_key=NotificationTemplate.APPLICATION_STATUS_CHANGED.value,
            payload={"reference": application.reference, "status": status.value},
        )
        return application
