from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.application.services.catalog_service import CatalogueFilters, CatalogService
from app.core.money import format_money
from app.domain.enums import DealType, ProductCategory, UseContext
from app.infrastructure.db.session import get_db


router = APIRouter(prefix="/api/v1")


def _enum(enum_type, value: str | None):
    try:
        return enum_type(value) if value else None
    except ValueError:
        return None


def _deal_payload(deal) -> dict:
    return {
        "id": deal.id,
        "product": {
            "sku": deal.product.sku,
            "name": deal.product.name,
            "brand": deal.product.brand,
            "category": deal.product.category.value,
            "image_url": deal.product.primary_image_url,
            "specifications": deal.product.specifications,
        },
        "network": (
            {
                "code": deal.network.code,
                "name": deal.network.display_name,
                "accent_color": deal.network.accent_color,
            }
            if deal.network
            else None
        ),
        "deal_type": deal.deal_type.value,
        "monthly_price_cents": deal.monthly_price_cents,
        "cash_price_cents": deal.cash_price_cents,
        "monthly_price": format_money(deal.monthly_price_cents),
        "cash_price": format_money(deal.cash_price_cents),
        "upfront_cost_cents": deal.upfront_cost_cents,
        "contract_months": deal.contract_months,
        "data_mb": deal.data_mb,
        "voice_minutes": deal.voice_minutes,
        "sms_count": deal.sms_count,
        "speed_mbps": deal.speed_mbps,
        "stock_status": deal.stock_status.value,
        "verified_at": deal.verified_at.isoformat() if deal.verified_at else None,
        "expires_at": deal.expires_at.isoformat() if deal.expires_at else None,
    }


@router.get("/catalog/deals")
def catalogue_api(
    category: str | None = None,
    deal_type: str | None = None,
    network: str | None = None,
    brand: str | None = None,
    use_context: str | None = None,
    q: str | None = None,
    limit: int = Query(default=40, ge=1, le=100),
    session: Session = Depends(get_db),
):
    filters = CatalogueFilters(
        category=_enum(ProductCategory, category),
        deal_type=_enum(DealType, deal_type),
        network_code=network,
        brand=brand,
        use_context=_enum(UseContext, use_context),
        search=q,
    )
    deals = CatalogService(session).search(filters, limit=limit)
    return {"items": [_deal_payload(deal) for deal in deals], "count": len(deals)}


@router.get("/catalog/deals/{deal_id}")
def deal_api(deal_id: str, session: Session = Depends(get_db)):
    deal = CatalogService(session).get_public_deal(deal_id)
    return {"item": _deal_payload(deal) if deal else None}
