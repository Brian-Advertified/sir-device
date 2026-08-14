from contextlib import nullcontext

from app.infrastructure.db.models import Deal, Network
from scripts import sync_mtn_inventory
from scripts.convert_mtn_inventory_to_deals import _infer_category


MTN_CSV = """source_key,network_code,network_name,network_color,sku,product_name,slug,brand,category,deal_type,monthly_price,cash_price,upfront_cost,contract_months,data_mb,voice_minutes,sms_count,speed_mbps,start_at,expires_at,stock_status,source_document,verified_at,terms_url,published,featured,image_url,description,use_context,specifications_json
mtn:test-001,mtn,MTN,#ffcc00,MTN-001,Test Phone,test-phone,Test,smartphone,device_contract,499,,,24,,,,,,,in_stock,test.csv,2026-08-14T00:00:00Z,,true,false,https://example.test/phone.png,,personal,"{""price_plan"":""Made For Me""}"
"""


def test_mtn_converter_classifies_non_phone_inventory():
    assert _infer_category("Use Your Own") == "mobile_plan"
    assert _infer_category("Huawei MatePad SE 11 128GB LTE") == "tablet"
    assert _infer_category("HP 15 Intel i7") == "laptop"
    assert _infer_category("Huawei E5576-321") == "lte"
    assert _infer_category("ZTE MC888 5G") == "5g"
    assert _infer_category("Huawei Mesh 3 WiFi 2-Pack") == "accessory"
    assert _infer_category("MTN YelloCart voucher - R600") == "accessory"
    # The leading product determines the category when a phone bundle includes a tablet.
    assert _infer_category("Samsung Galaxy A27 + Samsung Galaxy Tab A11") == "smartphone"


def test_mtn_import_preserves_vodacom_inventory(db_session, tmp_path, monkeypatch):
    db_session.add(Network(code="vodacom", display_name="Vodacom", accent_color="#e60000"))
    db_session.commit()
    source = tmp_path / "mtn.csv"
    source.write_text(MTN_CSV, encoding="utf-8")
    monkeypatch.setattr(sync_mtn_inventory, "create_schema", lambda: None)
    monkeypatch.setattr(sync_mtn_inventory, "SessionLocal", lambda: nullcontext(db_session))

    assert sync_mtn_inventory.import_mtn_inventory(source) == 1
    assert {network.code for network in db_session.query(Network)} == {"mtn", "vodacom"}
    assert db_session.query(Deal).filter_by(source_key="mtn:test-001").one().published is True
