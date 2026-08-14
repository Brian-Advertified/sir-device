from datetime import UTC, datetime

from sqlalchemy import Select, and_, case, func, or_, select, update
from sqlalchemy.orm import Session, joinedload

from app.domain.enums import DealType, ProductCategory, StockStatus, UseContext
from app.infrastructure.db.models import Deal, Network, Product, PromotionBanner, SavedProduct


class CatalogRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _public_statement(now: datetime | None = None, *, eager: bool = True) -> Select[tuple[Deal]]:
        current = now or datetime.now(UTC)
        statement = (
            select(Deal)
            .join(Deal.product)
            .where(
                Deal.published.is_(True),
                Product.is_active.is_(True),
                Product.primary_image_url.is_not(None),
                Product.primary_image_url != "/static/img/mtn-device-plan.svg",
                Product.primary_image_url != "/static/img/device-placeholder.svg",
                Deal.stock_status != StockStatus.OUT_OF_STOCK,
                or_(Deal.starts_at.is_(None), Deal.starts_at <= current),
                or_(Deal.expires_at.is_(None), Deal.expires_at >= current),
            )
        )
        if eager:
            statement = statement.options(joinedload(Deal.product), joinedload(Deal.network))
        return statement

    def list_public_deals(
        self,
        *,
        category: ProductCategory | None = None,
        categories: tuple[ProductCategory, ...] = (),
        deal_type: DealType | None = None,
        deal_types: tuple[DealType, ...] = (),
        network_code: str | None = None,
        brand: str | None = None,
        use_context: UseContext | None = None,
        min_monthly_cents: int | None = None,
        max_monthly_cents: int | None = None,
        contract_months: int | None = None,
        sort: str = "popular",
        search: str | None = None,
        featured_only: bool = False,
        limit: int = 60,
        offset: int = 0,
    ) -> list[Deal]:
        statement = self._public_statement(eager=False)
        if category:
            statement = statement.where(Product.category == category)
        elif categories:
            statement = statement.where(Product.category.in_(categories))
        if deal_type:
            statement = statement.where(Deal.deal_type == deal_type)
        elif deal_types:
            statement = statement.where(Deal.deal_type.in_(deal_types))
        if network_code:
            statement = statement.join(Deal.network).where(Network.code == network_code)
        if brand:
            statement = statement.where(Product.brand == brand)
        if use_context:
            statement = statement.where(
                or_(Product.use_context == use_context, Product.use_context == UseContext.BOTH)
            )
        if min_monthly_cents is not None:
            statement = statement.where(Deal.monthly_price_cents >= min_monthly_cents)
        if max_monthly_cents is not None:
            statement = statement.where(Deal.monthly_price_cents <= max_monthly_cents)
        if contract_months is not None:
            statement = statement.where(Deal.contract_months == contract_months)
        if search:
            term = f"%{search.strip()}%"
            statement = statement.where(
                or_(Product.name.ilike(term), Product.brand.ilike(term), Product.sku.ilike(term))
            )
        if featured_only:
            statement = statement.where(Deal.featured.is_(True))
        representative_ids = (
            statement
            .with_only_columns(Deal.id)
            .distinct(func.lower(Product.name))
            .order_by(
                func.lower(Product.name),
                Deal.monthly_price_cents.asc().nullslast(),
                Deal.verified_at.desc().nullslast(),
            )
            .subquery()
        )
        statement = (
            select(Deal)
            .join(representative_ids, Deal.id == representative_ids.c.id)
            .options(joinedload(Deal.product), joinedload(Deal.network))
        )
        if sort == "price_asc":
            ordering = (Deal.monthly_price_cents.asc().nullslast(), Deal.cash_price_cents.asc().nullslast())
        elif sort == "price_desc":
            ordering = (Deal.monthly_price_cents.desc().nullslast(), Deal.cash_price_cents.desc().nullslast())
        elif sort == "newest":
            ordering = (Deal.verified_at.desc().nullslast(),)
        else:
            ordering = (Deal.featured.desc(), Deal.verified_at.desc().nullslast())
        statement = statement.order_by(*ordering).offset(offset).limit(limit)
        return list(self._session.scalars(statement).unique())

    def count_public_deals(
        self,
        *,
        category: ProductCategory | None = None,
        categories: tuple[ProductCategory, ...] = (),
        deal_type: DealType | None = None,
        deal_types: tuple[DealType, ...] = (),
        network_code: str | None = None,
        brand: str | None = None,
        use_context: UseContext | None = None,
        min_monthly_cents: int | None = None,
        max_monthly_cents: int | None = None,
        contract_months: int | None = None,
        sort: str = "popular",
        search: str | None = None,
        featured_only: bool = False,
    ) -> int:
        statement = self._public_statement(eager=False)
        if category:
            statement = statement.where(Product.category == category)
        elif categories:
            statement = statement.where(Product.category.in_(categories))
        if deal_type:
            statement = statement.where(Deal.deal_type == deal_type)
        elif deal_types:
            statement = statement.where(Deal.deal_type.in_(deal_types))
        if network_code:
            statement = statement.join(Deal.network).where(Network.code == network_code)
        if brand:
            statement = statement.where(Product.brand == brand)
        if use_context:
            statement = statement.where(or_(Product.use_context == use_context, Product.use_context == UseContext.BOTH))
        if min_monthly_cents is not None:
            statement = statement.where(Deal.monthly_price_cents >= min_monthly_cents)
        if max_monthly_cents is not None:
            statement = statement.where(Deal.monthly_price_cents <= max_monthly_cents)
        if contract_months is not None:
            statement = statement.where(Deal.contract_months == contract_months)
        if search:
            term = f"%{search.strip()}%"
            statement = statement.where(or_(Product.name.ilike(term), Product.brand.ilike(term), Product.sku.ilike(term)))
        if featured_only:
            statement = statement.where(Deal.featured.is_(True))
        statement = statement.with_only_columns(func.count(func.distinct(func.lower(Product.name)))).order_by(None)
        return int(self._session.scalar(statement) or 0)

    def get_public_deal(self, deal_id: str) -> Deal | None:
        statement = self._public_statement().where(Deal.id == deal_id)
        return self._session.scalar(statement)

    def list_related_public_deals(self, deal: Deal, limit: int = 1200) -> list[Deal]:
        statement = (
            self._public_statement()
            .where(
                func.lower(Product.name) == deal.product.name.lower(),
                Product.use_context == deal.product.use_context,
            )
            .order_by(
                Product.specifications["price_plan"].as_string().asc().nullslast(),
                Deal.contract_months.asc().nullslast(),
                Deal.monthly_price_cents.asc().nullslast(),
            )
            .limit(limit)
        )
        return list(self._session.scalars(statement).unique())

    def list_featured_candidates(
        self,
        *,
        use_context: UseContext | None = None,
        network_code: str | None = None,
        limit: int = 1000,
    ) -> list[Deal]:
        statement = self._public_statement(eager=False).where(
            Deal.monthly_price_cents.is_not(None),
            Deal.deal_type == DealType.DEVICE_CONTRACT,
            Product.category.in_(
                (ProductCategory.SMARTPHONE, ProductCategory.TABLET, ProductCategory.LAPTOP)
            ),
            func.lower(Product.name) != "use your own",
            or_(
                Deal.featured.is_(True),
                Deal.administrator_notes.ilike("%promo%"),
            ),
        )
        if use_context:
            statement = statement.where(
                or_(Product.use_context == use_context, Product.use_context == UseContext.BOTH)
            )
        if network_code:
            statement = statement.join(Deal.network).where(Network.code == network_code)
        candidate_ids = (
            statement
            .with_only_columns(
                Deal.id.label("deal_id"),
                func.row_number().over(
                    partition_by=func.lower(Product.name),
                    order_by=(
                        case((Deal.contract_months == 24, 0), else_=1),
                        Deal.monthly_price_cents.asc().nullslast(),
                        Deal.verified_at.desc().nullslast(),
                    ),
                ).label("product_rank"),
            )
            .subquery()
        )
        statement = (
            select(Deal)
            .join(candidate_ids, Deal.id == candidate_ids.c.deal_id)
            .where(candidate_ids.c.product_rank == 1)
            .options(joinedload(Deal.product), joinedload(Deal.network))
            .limit(limit)
        )
        return list(self._session.scalars(statement).unique())

    def get_deals_by_ids(self, deal_ids: list[str], public_only: bool = True) -> list[Deal]:
        if not deal_ids:
            return []
        statement = self._public_statement() if public_only else select(Deal).options(
            joinedload(Deal.product), joinedload(Deal.network)
        )
        statement = statement.where(Deal.id.in_(deal_ids))
        deals = list(self._session.scalars(statement).unique())
        order = {deal_id: position for position, deal_id in enumerate(deal_ids)}
        return sorted(deals, key=lambda item: order.get(item.id, len(order)))

    def list_networks(self, active_only: bool = True) -> list[Network]:
        statement = select(Network)
        if active_only:
            statement = statement.where(Network.is_active.is_(True))
        return list(self._session.scalars(statement.order_by(Network.display_name)))

    def list_brands(self, use_context: UseContext | None = None) -> list[str]:
        statement = select(Product.brand).where(Product.is_active.is_(True)).distinct()
        if use_context:
            statement = statement.where(
                or_(Product.use_context == use_context, Product.use_context == UseContext.BOTH)
            )
        return sorted(item for item in self._session.scalars(statement) if item)

    def list_admin_products(self, limit: int = 500) -> list[Product]:
        statement = select(Product).order_by(Product.updated_at.desc()).limit(limit)
        return list(self._session.scalars(statement))

    def list_admin_deals(self, limit: int = 500) -> list[Deal]:
        statement = (
            select(Deal)
            .options(joinedload(Deal.product), joinedload(Deal.network))
            .order_by(Deal.updated_at.desc())
            .limit(limit)
        )
        return list(self._session.scalars(statement).unique())

    def list_banners(self, public_only: bool = False) -> list[PromotionBanner]:
        statement = select(PromotionBanner)
        if public_only:
            current = datetime.now(UTC)
            statement = statement.where(
                PromotionBanner.published.is_(True),
                or_(PromotionBanner.starts_at.is_(None), PromotionBanner.starts_at <= current),
                or_(PromotionBanner.expires_at.is_(None), PromotionBanner.expires_at >= current),
            )
        return list(
            self._session.scalars(
                statement.order_by(PromotionBanner.display_order, PromotionBanner.created_at.desc())
            )
        )

    def get_network_by_code(self, code: str) -> Network | None:
        return self._session.scalar(select(Network).where(Network.code == code))

    def get_product_by_sku(self, sku: str) -> Product | None:
        return self._session.scalar(select(Product).where(Product.sku == sku))

    def get_product(self, product_id: str) -> Product | None:
        return self._session.get(Product, product_id)

    def get_deal(self, deal_id: str) -> Deal | None:
        return self._session.get(Deal, deal_id)

    def add(self, entity: Network | Product | Deal | PromotionBanner):
        self._session.add(entity)
        self._session.flush()
        return entity


    def list_saved_products(self, user_id: str) -> list[Product]:
        statement = (
            select(Product)
            .join(SavedProduct, SavedProduct.product_id == Product.id)
            .where(SavedProduct.user_id == user_id, Product.is_active.is_(True))
            .order_by(SavedProduct.created_at.desc())
        )
        return list(self._session.scalars(statement))

    def save_product_for_user(self, user_id: str, product_id: str) -> None:
        exists = self._session.scalar(
            select(SavedProduct).where(
                SavedProduct.user_id == user_id, SavedProduct.product_id == product_id
            )
        )
        if not exists:
            self._session.add(SavedProduct(user_id=user_id, product_id=product_id))
            self._session.flush()

    def remove_saved_product(self, user_id: str, product_id: str) -> None:
        saved = self._session.scalar(
            select(SavedProduct).where(
                SavedProduct.user_id == user_id, SavedProduct.product_id == product_id
            )
        )
        if saved:
            self._session.delete(saved)
            self._session.flush()

    def expire_past_deals(self) -> int:
        current = datetime.now(UTC)
        statement = (
            update(Deal)
            .where(
                Deal.published.is_(True),
                Deal.expires_at.is_not(None),
                Deal.expires_at < current,
            )
            .values(published=False)
        )
        result = self._session.execute(statement)
        return int(result.rowcount or 0)
