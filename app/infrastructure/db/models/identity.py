from __future__ import annotations

from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.ids import new_id
from app.domain.enums import UserRole
from app.infrastructure.db.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(160))
    phone: Mapped[str | None] = mapped_column(String(40))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, length=40), default=UserRole.CUSTOMER
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    addresses: Mapped[list[Address]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Address(Base, TimestampMixin):
    __tablename__ = "addresses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    label: Mapped[str] = mapped_column(String(50), default="delivery")
    line1: Mapped[str] = mapped_column(String(180))
    line2: Mapped[str | None] = mapped_column(String(180))
    city: Mapped[str] = mapped_column(String(100))
    province: Mapped[str] = mapped_column(String(100))
    postal_code: Mapped[str] = mapped_column(String(20))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped[User] = relationship(back_populates="addresses")
