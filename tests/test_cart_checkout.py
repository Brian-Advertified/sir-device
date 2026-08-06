from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.domain.enums import DealType, ProductCategory, StockStatus, UseContext
from app.infrastructure.db.models import Deal, Network, Product
from app.main import app


def _create_cash_deal(session) -> str:
    network = Network(code="network-a", display_name="Network A", accent_color="#ffcc00")
    product = Product(
        sku="SKU-CASH-1",
        slug="generic-cash-device",
        name="Generic Cash Device",
        brand="Generic",
        category=ProductCategory.SMARTPHONE,
        use_context=UseContext.BOTH,
        specifications={},
        is_active=True,
    )
    session.add_all([network, product])
    session.flush()
    deal = Deal(
        source_key="cash-deal-1",
        product_id=product.id,
        network_id=network.id,
        deal_type=DealType.CASH_PURCHASE,
        monthly_price_cents=None,
        cash_price_cents=250000,
        upfront_cost_cents=0,
        contract_months=None,
        data_mb=None,
        voice_minutes=None,
        sms_count=None,
        speed_mbps=None,
        starts_at=datetime.now(UTC) - timedelta(days=1),
        expires_at=datetime.now(UTC) + timedelta(days=30),
        stock_status=StockStatus.IN_STOCK,
        verified_at=datetime.now(UTC),
        published=True,
        featured=True,
    )
    session.add(deal)
    session.commit()
    return deal.id


def test_guest_can_add_eligible_item_and_create_awaiting_payment_order(db_session):
    deal_id = _create_cash_deal(db_session)
    with TestClient(app) as client:
        add_response = client.post(
            "/api/v1/cart/items", json={"deal_id": deal_id, "quantity": 1}
        )
        assert add_response.status_code == 200
        assert add_response.json()["item_count"] == 1
        assert client.get("/cart").status_code == 200
        checkout = client.post(
            "/checkout",
            data={
                "full_name": "Test Customer",
                "email": "customer@example.com",
                "phone": "0100000000",
                "line1": "1 Test Street",
                "line2": "",
                "city": "Johannesburg",
                "province": "Gauteng",
                "postal_code": "2000",
                "csrf_token": "",
            },
        )
        assert checkout.status_code == 200
        assert "Order SDO-" in checkout.text
        assert "Payment gateway is not configured" in checkout.text
