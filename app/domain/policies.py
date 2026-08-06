from dataclasses import dataclass
from datetime import UTC, datetime

from app.domain.enums import DealType, StockStatus


@dataclass(frozen=True)
class DealAvailabilityPolicy:
    """Pure domain policy used by catalogue and checkout services."""

    @staticmethod
    def is_public(
        *,
        published: bool,
        starts_at: datetime | None,
        expires_at: datetime | None,
        stock_status: StockStatus,
        now: datetime | None = None,
    ) -> bool:
        current = now or datetime.now(UTC)
        if not published or stock_status == StockStatus.OUT_OF_STOCK:
            return False
        if starts_at and starts_at > current:
            return False
        return not expires_at or expires_at >= current

    @staticmethod
    def is_direct_purchase(deal_type: DealType, cash_price_cents: int | None) -> bool:
        eligible_types = {
            DealType.CASH_PURCHASE,
            DealType.ACCESSORY,
            DealType.DEPOSIT,
        }
        return deal_type in eligible_types and cash_price_cents is not None
