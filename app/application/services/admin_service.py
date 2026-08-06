import json

from sqlalchemy.orm import Session

from app.core.dates import parse_optional_datetime
from app.core.errors import NotFoundError, ValidationError
from app.core.money import parse_money_to_cents
from app.domain.enums import DealType, ProductCategory, StockStatus, UseContext
from app.infrastructure.db.models import Deal, Network, Product, PromotionBanner
from app.infrastructure.repositories.catalog_repository import CatalogRepository


class AdminService:
    def __init__(self, session: Session) -> None:
        self._catalogue = CatalogRepository(session)

    def save_network(self, data: dict[str, str], network_id: str | None = None) -> Network:
        network = self._catalogue.get_network_by_code(data.get("code", "").strip().lower())
        if network_id:
            network = next(
                (item for item in self._catalogue.list_networks(active_only=False) if item.id == network_id),
                None,
            )
        if not data.get("code", "").strip() or not data.get("display_name", "").strip():
            raise ValidationError("Network code and display name are required")
        if not network:
            network = Network()
        network.code = data["code"].strip().lower()
        network.display_name = data["display_name"].strip()
        network.accent_color = data.get("accent_color", "#7ACC00").strip()
        network.is_active = data.get("is_active") == "on"
        if not network.id:
            self._catalogue.add(network)
        return network

    def save_product(self, data: dict[str, str], product_id: str | None = None) -> Product:
        product = self._catalogue.get_product(product_id) if product_id else None
        required = ("sku", "slug", "name", "brand", "category")
        if any(not data.get(field, "").strip() for field in required):
            raise ValidationError("SKU, slug, name, brand and category are required")
        try:
            specifications = json.loads(data.get("specifications", "{}") or "{}")
        except json.JSONDecodeError as exc:
            raise ValidationError("Specifications must be a valid JSON object") from exc
        if not isinstance(specifications, dict):
            raise ValidationError("Specifications must be a JSON object")
        if not product:
            product = Product()
        product.sku = data["sku"].strip()
        product.slug = data["slug"].strip()
        product.name = data["name"].strip()
        product.brand = data["brand"].strip()
        product.category = ProductCategory(data["category"])
        product.description = data.get("description", "").strip() or None
        product.use_context = UseContext(data.get("use_context", UseContext.BOTH.value))
        product.primary_image_url = data.get("primary_image_url", "").strip() or None
        product.specifications = specifications
        product.is_active = data.get("is_active") == "on"
        if not product.id:
            self._catalogue.add(product)
        return product

    def save_deal(self, data: dict[str, str], deal_id: str | None = None) -> Deal:
        deal = self._catalogue.get_deal(deal_id) if deal_id else None
        product = self._catalogue.get_product(data.get("product_id", ""))
        network = next(
            (
                item
                for item in self._catalogue.list_networks(active_only=False)
                if item.id == data.get("network_id")
            ),
            None,
        )
        if not product:
            raise ValidationError("Select a valid product")
        if not deal:
            deal = Deal()
        deal.source_key = data.get("source_key", "").strip() or None
        deal.product_id = product.id
        deal.network_id = network.id if network else None
        deal.deal_type = DealType(data["deal_type"])
        deal.monthly_price_cents = parse_money_to_cents(data.get("monthly_price"))
        deal.cash_price_cents = parse_money_to_cents(data.get("cash_price"))
        deal.upfront_cost_cents = parse_money_to_cents(data.get("upfront_cost"))
        deal.contract_months = self._optional_int(data.get("contract_months"))
        deal.data_mb = self._optional_int(data.get("data_mb"))
        deal.voice_minutes = self._optional_int(data.get("voice_minutes"))
        deal.sms_count = self._optional_int(data.get("sms_count"))
        deal.speed_mbps = self._optional_int(data.get("speed_mbps"))
        deal.starts_at = parse_optional_datetime(data.get("starts_at"))
        deal.expires_at = parse_optional_datetime(data.get("expires_at"))
        deal.stock_status = StockStatus(data["stock_status"])
        deal.source_document = data.get("source_document", "").strip() or None
        deal.administrator_notes = data.get("administrator_notes", "").strip() or None
        deal.verified_at = parse_optional_datetime(data.get("verified_at"))
        deal.terms_url = data.get("terms_url", "").strip() or None
        deal.published = data.get("published") == "on"
        deal.featured = data.get("featured") == "on"
        if not deal.id:
            self._catalogue.add(deal)
        return deal

    def save_banner(self, data: dict[str, str], banner_id: str | None = None) -> PromotionBanner:
        banner = next(
            (item for item in self._catalogue.list_banners() if item.id == banner_id),
            None,
        )
        if not data.get("title", "").strip():
            raise ValidationError("Banner title is required")
        if not banner:
            banner = PromotionBanner()
        banner.title = data["title"].strip()
        banner.body = data.get("body", "").strip() or None
        banner.image_url = data.get("image_url", "").strip() or None
        banner.link_url = data.get("link_url", "").strip() or None
        banner.starts_at = parse_optional_datetime(data.get("starts_at"))
        banner.expires_at = parse_optional_datetime(data.get("expires_at"))
        banner.published = data.get("published") == "on"
        banner.display_order = self._optional_int(data.get("display_order")) or 0
        if not banner.id:
            self._catalogue.add(banner)
        return banner

    @staticmethod
    def _optional_int(value: str | None) -> int | None:
        if not value or not value.strip():
            return None
        parsed = int(value)
        if parsed < 0:
            raise ValidationError("Numeric values cannot be negative")
        return parsed
