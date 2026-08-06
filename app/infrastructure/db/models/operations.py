from typing import Any

from sqlalchemy import Enum, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.ids import new_id
from app.domain.enums import (
    NotificationChannel,
    NotificationStatus,
    SupportStatus,
)
from app.infrastructure.db.base import Base, TimestampMixin


class SupportTicket(Base, TimestampMixin):
    __tablename__ = "support_tickets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    reference: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str] = mapped_column(String(320), index=True)
    phone: Mapped[str | None] = mapped_column(String(40))
    subject: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[SupportStatus] = mapped_column(
        Enum(SupportStatus, native_enum=False, length=30), index=True
    )


class NotificationOutbox(Base, TimestampMixin):
    __tablename__ = "notification_outbox"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(NotificationChannel, native_enum=False, length=20)
    )
    recipient: Mapped[str] = mapped_column(String(320), index=True)
    template_key: Mapped[str] = mapped_column(String(100))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus, native_enum=False, length=20), index=True
    )
    error_message: Mapped[str | None] = mapped_column(String(1000))


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    actor_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(120), index=True)
    entity_type: Mapped[str] = mapped_column(String(100), index=True)
    entity_id: Mapped[str | None] = mapped_column(String(80), index=True)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[str] = mapped_column(String(40))
