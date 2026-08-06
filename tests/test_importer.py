from app.application.services.import_service import CsvDealImporter
from app.infrastructure.db.models import Deal, Network, Product


CSV_TEXT = """source_key,network_code,network_name,network_color,sku,product_name,slug,brand,category,deal_type,monthly_price,cash_price,upfront_cost,contract_months,data_mb,voice_minutes,sms_count,speed_mbps,start_at,expires_at,stock_status,source_document,verified_at,terms_url,published,featured,image_url,description,use_context,specifications_json
external-001,network-a,Network A,#ffcc00,SKU-001,Generic Phone,generic-phone,Generic,smartphone,cash_purchase,,1499.00,0,,,,,,2026-01-01T00:00:00+00:00,2027-01-01T00:00:00+00:00,in_stock,verified-source.csv,2026-01-01T00:00:00+00:00,,true,true,,,both,"{""storage"":""128GB""}"
"""


def test_csv_import_is_validated_and_idempotent(db_session):
    importer = CsvDealImporter(db_session)
    first = importer.import_text(CSV_TEXT)
    assert not first.issues
    db_session.commit()
    assert db_session.query(Network).count() == 1
    assert db_session.query(Product).count() == 1
    assert db_session.query(Deal).count() == 1

    second = importer.import_text(CSV_TEXT.replace("1499.00", "1399.00"))
    assert second.deals_updated == 1
    db_session.commit()
    assert db_session.query(Deal).count() == 1
    assert db_session.query(Deal).one().cash_price_cents == 139900


def test_invalid_import_has_no_partial_changes(db_session):
    invalid = CSV_TEXT.replace("cash_purchase", "unsupported-deal-type")
    result = CsvDealImporter(db_session).import_text(invalid)
    assert result.issues
    assert db_session.query(Network).count() == 0
    assert db_session.query(Product).count() == 0
    assert db_session.query(Deal).count() == 0


def test_xlsx_import_uses_same_validation_and_upsert_rules(db_session):
    from io import BytesIO

    from openpyxl import Workbook

    workbook = Workbook()
    worksheet = workbook.active
    rows = list(__import__("csv").reader(CSV_TEXT.strip().splitlines()))
    for row in rows:
        worksheet.append(row)
    buffer = BytesIO()
    workbook.save(buffer)
    result = CsvDealImporter(db_session).import_xlsx_bytes(buffer.getvalue())
    assert not result.issues
    assert result.deals_created == 1
