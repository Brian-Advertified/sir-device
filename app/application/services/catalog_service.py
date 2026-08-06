from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.money import parse_money_to_cents
from app.domain.enums import DealType, ProductCategory, UseContext
from app.infrastructure.db.models import Deal
from app.infrastructure.repositories.catalog_repository import CatalogRepository


@dataclass(frozen=True)
class CatalogueFilters:
    category: ProductCategory | None = None
    categories: tuple[ProductCategory, ...] = ()
    deal_type: DealType | None = None
    deal_types: tuple[DealType, ...] = ()
    network_code: str | None = None
    brand: str | None = None
    use_context: UseContext | None = None
    min_monthly: str | None = None
    max_monthly: str | None = None
    search: str | None = None


class CatalogService:
    def __init__(self, session: Session) -> None:
        self._catalogue = CatalogRepository(session)

    def featured_deals(self, limit: int = 8) -> list[Deal]:
        deals = self._catalogue.list_public_deals(featured_only=True, limit=limit)
        if deals:
            return deals
        return self._catalogue.list_public_deals(limit=limit)

    def search(self, filters: CatalogueFilters, limit: int = 12, offset: int = 0) -> list[Deal]:
        return self._catalogue.list_public_deals(
            category=filters.category,
            categories=filters.categories,
            deal_type=filters.deal_type,
            deal_types=filters.deal_types,
            network_code=filters.network_code,
            brand=filters.brand,
            use_context=filters.use_context,
            min_monthly_cents=parse_money_to_cents(filters.min_monthly),
            max_monthly_cents=parse_money_to_cents(filters.max_monthly),
            search=filters.search,
            limit=limit,
            offset=offset,
        )

    def count(self, filters: CatalogueFilters) -> int:
        return self._catalogue.count_public_deals(
            category=filters.category,
            categories=filters.categories,
            deal_type=filters.deal_type,
            deal_types=filters.deal_types,
            network_code=filters.network_code,
            brand=filters.brand,
            use_context=filters.use_context,
            min_monthly_cents=parse_money_to_cents(filters.min_monthly),
            max_monthly_cents=parse_money_to_cents(filters.max_monthly),
            search=filters.search,
        )

    def get_public_deal(self, deal_id: str) -> Deal | None:
        return self._catalogue.get_public_deal(deal_id)

    def compare(self, deal_ids: list[str]) -> list[Deal]:
        return self._catalogue.get_deals_by_ids(deal_ids[:3])

    def filter_options(self) -> dict:
        return {
            "networks": self._catalogue.list_networks(),
            "brands": self._catalogue.list_brands(),
            "categories": list(ProductCategory),
            "contexts": list(UseContext),
        }
