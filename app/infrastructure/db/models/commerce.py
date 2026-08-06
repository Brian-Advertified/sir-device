from __future__ import annotations

from typing import Any

from sqlalchemy import Enum, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.ids import new_id
from app.domain.enums import CartStatus, OrderStatus, PaymentStatus
from app.infrastructure.db.base import Base, TimestampMixin


class Cart(Base, TimestampMixin):
    __tablename__ = "carts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    session_token: Mapped[str | None] = mapped_column(String(100), unique=True, index=True)
    status: Mapped[CartStatus] = mapped_column(
        Enum(CartStatus, native_enum=False, length=20), default=CartStatus.ACTIVE
    )

    items: Mapped[list[CartItem]] = relationship(
        back_populates="cart", cascade="all, delete-orphan"
    )


class CartItem(Base, TimestampMixin):
    __tablename__ = "cart_items"
    __table_args__ = (UniqueConstraint("cart_id", "deal_id", name="uq_cart_deal"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    cart_id: Mapped[str] = mapped_column(ForeignKey("carts.id", ondelete="CASCADE"))
    deal_id: Mapped[str] = mapped_column(ForeignKey("deals.id", ondelete="CASCADE"))
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    cart: Mapped[Cart] = relationship(back_populates="items")
    deal: Mapped[Any] = relationship("Deal")


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    reference: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    email: Mapped[str] = mapped_column(String(320))
    phone: Mapped[str] = mapped_column(String(40))
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, native_enum=False, length=40), index=True
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, native_enum=False, length=30), index=True
    )
    subtotal_cents: Mapped[int] = mapped_column(Integer)
    delivery_cents: Mapped[int] = mapped_column(Integer, default=0)
    total_cents: Mapped[int] = mapped_column(Integer)
    customer_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON)
    delivery_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON)

    items: Mapped[list[OrderItem]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    payments: Mapped[list[Payment]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base, TimestampMixin):
    __tablename__ = "order_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    deal_id: Mapped[str | None] = mapped_column(
        ForeignKey("deals.id", ondelete="SET NULL"), nullable=True
    )
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price_cents: Mapped[int] = mapped_column(Integer)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON)

    order: Mapped[Order] = relationship(back_populates="items")


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    provider: Mapped[str] = mapped_column(String(50))
    provider_reference: Mapped[str | None] = mapped_column(String(160), index=True)
    amount_cents: Mapped[int] = mapped_column(Integer)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, native_enum=False, length=30)
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    order: Mapped[Order] = relationship(back_populates="payments")
