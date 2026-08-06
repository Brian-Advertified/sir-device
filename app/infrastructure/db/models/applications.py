from __future__ import annotations

from typing import Any

from sqlalchemy import Enum, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.ids import new_id
from app.domain.enums import (
    ApplicationStatus,
    CustomerType,
    DocumentStatus,
    DocumentType,
    QuoteStatus,
)
from app.infrastructure.db.base import Base, TimestampMixin


class ContractApplication(Base, TimestampMixin):
    __tablename__ = "contract_applications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    reference: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    selected_deal_id: Mapped[str | None] = mapped_column(
        ForeignKey("deals.id", ondelete="SET NULL"), nullable=True
    )
    customer_type: Mapped[CustomerType] = mapped_column(
        Enum(CustomerType, native_enum=False, length=20)
    )
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, native_enum=False, length=40), index=True
    )
    email: Mapped[str] = mapped_column(String(320), index=True)
    phone: Mapped[str] = mapped_column(String(40))
    details: Mapped[dict[str, Any]] = mapped_column(JSON)

    documents: Mapped[list[UploadedDocument]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )


class BusinessQuote(Base, TimestampMixin):
    __tablename__ = "business_quotes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    reference: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[QuoteStatus] = mapped_column(
        Enum(QuoteStatus, native_enum=False, length=30), index=True
    )
    company_name: Mapped[str] = mapped_column(String(180))
    contact_name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str] = mapped_column(String(320), index=True)
    phone: Mapped[str] = mapped_column(String(40))
    details: Mapped[dict[str, Any]] = mapped_column(JSON)


class UploadedDocument(Base, TimestampMixin):
    __tablename__ = "uploaded_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    application_id: Mapped[str] = mapped_column(
        ForeignKey("contract_applications.id", ondelete="CASCADE"), index=True
    )
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, native_enum=False, length=50)
    )
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, native_enum=False, length=30), default=DocumentStatus.RECEIVED
    )
    storage_key: Mapped[str] = mapped_column(String(1000))
    original_name: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(120))
    size_bytes: Mapped[int]

    application: Mapped[ContractApplication] = relationship(back_populates="documents")
