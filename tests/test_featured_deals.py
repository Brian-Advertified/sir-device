from datetime import UTC, datetime

from app.application.services.catalog_service import CatalogService
from app.domain.enums import DealType, ProductCategory, StockStatus, UseContext
from app.infrastructure.db.models import Deal, Network, Product


def _add_device_deal(session, network, index: int, *, featured: bool, promo: bool):
    product = Product(
        sku=f"{network.code.upper()}-{index}",
        slug=f"{network.code}-phone-{index}",
        name=f"{network.display_name} Promo Phone {index}",
        brand=f"Brand {network.code} {index}",
        category=ProductCategory.SMARTPHONE,
        use_context=UseContext.PERSONAL,
        primary_image_url=f"https://example.test/{network.code}-{index}.png",
        specifications={"price_plan": "Gold" if network.code == "mtn" else "RED Core"},
    )
    session.add(
        Deal(
            product=product,
            network=network,
            source_key=f"{network.code}:promo-{index}",
            deal_type=DealType.DEVICE_CONTRACT,
            monthly_price_cents=(499 + index) * 100,
            contract_months=24,
            stock_status=StockStatus.IN_STOCK,
            administrator_notes="Imported from promo source" if promo else "Live deal",
            verified_at=datetime.now(UTC),
            published=True,
            featured=featured,
        )
    )


def test_featured_devices_include_vodacom_and_mtn_promotions(db_session):
    vodacom = Network(code="vodacom", display_name="Vodacom", accent_color="#e60000")
    mtn = Network(code="mtn", display_name="MTN", accent_color="#ffd100")
    db_session.add_all([vodacom, mtn])
    for index in range(4):
        _add_device_deal(db_session, vodacom, index, featured=True, promo=False)
        _add_device_deal(db_session, mtn, index, featured=False, promo=True)
    db_session.commit()

    service = CatalogService(db_session)
    deals = service.featured_deals(limit=8, use_context=UseContext.PERSONAL)

    assert [deal.network.code for deal in deals] == ["vodacom", "mtn"] * 4
    assert all(deal.deal_type == DealType.DEVICE_CONTRACT for deal in deals)
    assert all(deal.product.category == ProductCategory.SMARTPHONE for deal in deals)
    assert all(deal.featured or "promo" in (deal.administrator_notes or "").lower() for deal in deals)
    assert {network.code for network in service.filter_options()["networks"]} == {"mtn", "vodacom"}
