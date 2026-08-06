from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.ids import new_id
from app.domain.enums import DealType, ProductCategory, StockStatus, UseContext
from app.infrastructure.db.base import Base, TimestampMixin


class Network(Base, TimestampMixin):
    __tablename__ = "networks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(100))
    accent_color: Mapped[str] = mapped_column(String(20), default="#7ACC00")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    deals: Mapped[list[Deal]] = relationship(back_populates="network")


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    sku: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(180), index=True)
    brand: Mapped[str] = mapped_column(String(100), index=True)
    category: Mapped[ProductCategory] = mapped_column(
        Enum(ProductCategory, native_enum=False, length=40), index=True
    )
    description: Mapped[str | None] = mapped_column(Text)
    use_context: Mapped[UseContext] = mapped_column(
        Enum(UseContext, native_enum=False, length=20), default=UseContext.BOTH
    )
    primary_image_url: Mapped[str | None] = mapped_column(String(1000))
    specifications: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    deals: Mapped[list[Deal]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )


class Deal(Base, TimestampMixin):
    __tablename__ = "deals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    network_id: Mapped[str | None] = mapped_column(
        ForeignKey("networks.id", ondelete="SET NULL"), nullable=True
    )
    source_key: Mapped[str | None] = mapped_column(String(180), unique=True, index=True)
    deal_type: Mapped[DealType] = mapped_column(
        Enum(DealType, native_enum=False, length=40), index=True
    )
    monthly_price_cents: Mapped[int | None] = mapped_column(Integer)
    cash_price_cents: Mapped[int | None] = mapped_column(Integer)
    upfront_cost_cents: Mapped[int | None] = mapped_column(Integer)
    contract_months: Mapped[int | None] = mapped_column(Integer)
    data_mb: Mapped[int | None] = mapped_column(Integer)
    voice_minutes: Mapped[int | None] = mapped_column(Integer)
    sms_count: Mapped[int | None] = mapped_column(Integer)
    speed_mbps: Mapped[int | None] = mapped_column(Integer)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    stock_status: Mapped[StockStatus] = mapped_column(
        Enum(StockStatus, native_enum=False, length=40), index=True
    )
    source_document: Mapped[str | None] = mapped_column(String(500))
    administrator_notes: Mapped[str | None] = mapped_column(Text)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    terms_url: Mapped[str | None] = mapped_column(String(1000))
    published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    featured: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    product: Mapped[Product] = relationship(back_populates="deals")
    network: Mapped[Network | None] = relationship(back_populates="deals")


class PromotionBanner(Base, TimestampMixin):
    __tablename__ = "promotion_banners"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    title: Mapped[str] = mapped_column(String(160))
    body: Mapped[str | None] = mapped_column(String(500))
    image_url: Mapped[str | None] = mapped_column(String(1000))
    link_url: Mapped[str | None] = mapped_column(String(1000))
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published: Mapped[bool] = mapped_column(Boolean, default=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)


class SavedProduct(Base, TimestampMixin):
    __tablename__ = "saved_products"
    __table_args__ = (UniqueConstraint("user_id", "product_id", name="uq_saved_user_product"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
