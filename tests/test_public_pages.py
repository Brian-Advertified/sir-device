from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.domain.enums import DealType, ProductCategory, StockStatus, UseContext
from app.infrastructure.db.models import Deal, Network, Product
from app.main import app


def test_public_pages_render_without_seed_data():
    with TestClient(app) as client:
        for path in (
            "/",
            "/devices",
            "/mobile-plans",
            "/internet",
            "/promotions",
            "/business-solutions",
            "/support",
            "/application-status",
            "/login",
            "/register",
        ):
            response = client.get(path)
            assert response.status_code == 200, path
            assert "Sir Device" in response.text


def test_homepage_shop_by_need_uses_icons():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.text.count('class="need-icon"><svg') == 7
        assert 'class="need-icon">P</span>' not in response.text


def test_catalogue_keeps_global_navigation():
    with TestClient(app) as client:
        response = client.get("/devices")
        assert '<nav class="primary-nav" data-primary-nav>' in response.text
        assert 'data-nav-toggle' in response.text


def test_catalogue_pagination_preserves_filters(db_session):
    network = Network(code="test-network", display_name="Test Network", accent_color="#7ACC00")
    db_session.add(network)
    verified_at = datetime.now(UTC)
    for index in range(25):
        product = Product(
            sku=f"TEST-{index}",
            slug=f"test-phone-{index}",
            name=f"Test Phone {index}",
            brand="Acme",
            category=ProductCategory.SMARTPHONE,
            use_context=UseContext.BOTH,
            primary_image_url="https://example.test/phone.png",
        )
        db_session.add(Deal(
            product=product,
            network=network,
            source_key=f"test:{index}",
            deal_type=DealType.DEVICE_CONTRACT,
            monthly_price_cents=49900,
            contract_months=24,
            stock_status=StockStatus.IN_STOCK,
            verified_at=verified_at,
            published=True,
        ))
    db_session.commit()

    with TestClient(app) as client:
        response = client.get("/devices?page=2&brand=Acme")

    assert response.status_code == 200
    assert "25 verified offers" in response.text
    assert response.text.count('class="compact-card"') == 12
    assert "brand=Acme&amp;page=1" in response.text


def test_health_endpoint():
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}
