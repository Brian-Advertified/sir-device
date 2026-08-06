from scripts.sync_vodacom_inventory import brand_for, category_for, integer, normalise_item


def test_brand_for_handles_known_and_connectivity_products():
    assert brand_for("Samsung Galaxy S25") == "Samsung"
    assert brand_for("100GB Data SIM") == "Vodacom"


def test_category_for_prioritises_source_categories():
    assert category_for({"name": "5G Router", "package_description": "", "categories": [{"url_key": "router-deals"}]}) == "router"
    assert category_for({"name": "100GB Data SIM", "package_description": "", "categories": [{"url_key": "phones-and-sim"}, {"url_key": "sim-only-deals"}]}) == "sim_only"
    assert category_for({"name": "Samsung phone + Watch LTE", "package_description": "", "categories": [{"url_key": "smartphones"}, {"url_key": "wearable-tech-deals"}]}) == "smartphone"
    assert category_for({"name": "Tablet + 5G Router", "package_description": "", "categories": [{"url_key": "tablets"}, {"url_key": "router-deals"}]}) == "tablet"
    assert category_for({"name": "Business Laptop + Router", "package_description": "", "categories": [{"url_key": "tablets-laptops"}, {"url_key": "laptop-deals"}, {"url_key": "router-deals"}]}) == "laptop"
    assert category_for({"name": "Uncapped Fibre", "package_description": "", "categories": [{"url_key": "fibre-deals"}]}) == "fibre"
    assert category_for({"name": "USB-C Charger", "package_description": "", "categories": [{"url_key": "accessories"}]}) == "accessory"


def test_integer_and_normalise_item_create_import_fields():
    assert integer("36 months") == 36
    row = normalise_item(
        {
            "name": "Samsung Galaxy S25 256GB",
            "url_key": "samsung-galaxy-s25",
            "sku": "SKU-1",
            "primary_product_image": None,
            "primary_product_sku": "DEVICE-1",
            "image": {"url": "https://example.test/phone.webp"},
            "payment_terms_label": "36",
            "package_description": "RED Core",
            "monthly_recurring": 999,
            "tariff": 400,
            "installment": 599,
            "stock_status": "IN_STOCK",
            "categories": [{"name": "Smartphones", "url_key": "smartphones"}],
        },
        0,
        "2026-08-06",
    )
    assert row["brand"] == "Samsung"
    assert row["contract_months"] == "36"
    assert row["image_url"] == "https://example.test/phone.webp"
    assert row["featured"] == "true"
    assert '"storage_options":["256GB"]' in row["specifications_json"]
    assert '"gallery"' in row["specifications_json"]
