from dataclasses import dataclass
import re

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
    contract_term: str | None = None
    sort: str = "popular"
    search: str | None = None
    featured_only: bool = False


class CatalogService:
    def __init__(self, session: Session) -> None:
        self._catalogue = CatalogRepository(session)

    def featured_deals(self, limit: int = 8, use_context: UseContext | None = None) -> list[Deal]:
        networks = self._catalogue.list_networks()
        network_codes = [network.code for network in networks]
        network_codes.sort(key=lambda code: (code not in {"vodacom", "mtn"}, code))
        candidates = [
            deal
            for code in network_codes
            for deal in self._catalogue.list_featured_candidates(
                use_context=use_context, network_code=code
            )
        ]
        if not candidates:
            return []

        selected: list[Deal] = []
        selected_products: set[str] = set()
        brand_counts: dict[str, int] = {}
        candidates_by_network: dict[str, list[Deal]] = {}
        for deal in sorted(candidates, key=self._featured_score, reverse=True):
            code = deal.network.code if deal.network else "unlocked"
            candidates_by_network.setdefault(code, []).append(deal)

        preferred_order = [code for code in ("vodacom", "mtn") if code in candidates_by_network]
        preferred_order.extend(code for code in candidates_by_network if code not in preferred_order)
        while len(selected) < limit:
            added = False
            for code in preferred_order:
                choice = self._next_featured_choice(
                    candidates_by_network[code], selected_products, brand_counts
                )
                if not choice:
                    continue
                selected.append(choice)
                product = self._product_family(choice.product.name)
                selected_products.add(product)
                brand = choice.product.brand.lower()
                brand_counts[brand] = brand_counts.get(brand, 0) + 1
                added = True
                if len(selected) >= limit:
                    break
            if not added:
                break
        return selected

    @classmethod
    def _next_featured_choice(
        cls,
        candidates: list[Deal],
        selected_products: set[str],
        brand_counts: dict[str, int],
    ) -> Deal | None:
        for deal in candidates:
            product = cls._product_family(deal.product.name)
            brand = deal.product.brand.lower()
            if product not in selected_products and brand_counts.get(brand, 0) < 2:
                return deal
        return None

    @staticmethod
    def _product_family(name: str) -> str:
        normalized = name.lower()
        normalized = re.sub(r"\s*\([^)]*(?:gb|tb)[^)]*\)", "", normalized)
        return re.sub(r"\s+", " ", normalized).strip()

    @staticmethod
    def _featured_score(deal: Deal) -> float:
        name = deal.product.name.lower()
        current_family_scores = (
            (r"iphone 17|galaxy s26", 120),
            (r"honor 600|nova 15", 115),
            (r"iphone 16|galaxy s25", 110),
            (r"honor 400|pura 80", 105),
            (r"iphone 15|galaxy s24|nova 14", 100),
            (r"galaxy a56|galaxy a36|galaxy a26", 95),
        )
        score = next((value for pattern, value in current_family_scores if re.search(pattern, name)), 30)
        if deal.contract_months == 24:
            score += 15
        plan = str((deal.product.specifications or {}).get("price_plan") or "").lower()
        if "topup" not in plan:
            score += 5
        if deal.featured:
            score += 25
        score -= (deal.monthly_price_cents or 0) / 100_000
        return score

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
            contract_months=int(filters.contract_term) if filters.contract_term and filters.contract_term.isdigit() else None,
            sort=filters.sort,
            search=filters.search,
            featured_only=filters.featured_only,
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
            contract_months=int(filters.contract_term) if filters.contract_term and filters.contract_term.isdigit() else None,
            sort=filters.sort,
            search=filters.search,
            featured_only=filters.featured_only,
        )

    def get_public_deal(self, deal_id: str) -> Deal | None:
        return self._catalogue.get_public_deal(deal_id)

    def grouped_offers(self, deal: Deal) -> list[dict]:
        groups: dict[str, list[Deal]] = {}
        seen: set[tuple] = set()
        for offer in self._catalogue.list_related_public_deals(deal):
            specifications = offer.product.specifications or {}
            plan = str(specifications.get("price_plan") or "Plan to be confirmed")
            signature = (
                plan,
                offer.contract_months,
                offer.monthly_price_cents,
                offer.upfront_cost_cents,
                str(specifications.get("freebies_device") or ""),
                str(specifications.get("freebies_plan") or ""),
            )
            if signature in seen:
                continue
            seen.add(signature)
            groups.setdefault(plan, []).append(offer)
        return [{"name": name, "offers": offers} for name, offers in groups.items()]

    def compare(self, deal_ids: list[str]) -> list[Deal]:
        return self._catalogue.get_deals_by_ids(deal_ids[:3])

    def filter_options(self, use_context: UseContext | None = None) -> dict:
        return {
            "networks": self._catalogue.list_networks(),
            "brands": self._catalogue.list_brands(use_context=use_context),
            "categories": list(ProductCategory),
            "contexts": list(UseContext),
        }
