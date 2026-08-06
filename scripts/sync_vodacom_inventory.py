from __future__ import annotations

import csv
from datetime import UTC, datetime
import json
from pathlib import Path
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sqlalchemy import select

from app.application.services.import_service import CsvDealImporter
from app.infrastructure.db.models import Deal
from app.infrastructure.db.session import SessionLocal, create_schema

GRAPHQL_URL = "https://shop.vodacom.co.za/graphql"
SOURCE_URL = "https://www.vodacom.co.za/shopping/deals"
PAGE_SIZE = 500
BRANDS = (
    "Apple", "Samsung", "Huawei", "Xiaomi", "Nokia", "Honor", "Motorola",
    "Oppo", "Vivo", "Google", "Lenovo", "Dell", "HP", "Acer", "Asus",
    "Hisense", "TCL", "ZTE", "Alcatel", "JBL", "Garmin", "Fitbit", "TP-Link",
)


def fetch_items(limit: int = PAGE_SIZE, skus: list[str] | None = None) -> list[dict]:
    query = """query products($filter: ProductAttributeFilterInput, $sort: ProductAttributeSortInput, $pageSize: Int, $currentPage: Int) {
      products(filter: $filter, sort: $sort, pageSize: $pageSize, currentPage: $currentPage) {
        items { name url_key sku primary_product_image primary_product_sku payment_terms_label
          package_description monthly_recurring tariff installment stock_status image { url label } small_image { url label } media_gallery { url label } categories { name url_key } }
      }
    }"""
    product_filter = {"is_deal_product": {"eq": "1"}, "is_hidden_product": {"eq": "0"}}
    if skus:
        product_filter["sku"] = {"in": skus}
    variables = {"filter": product_filter, "sort": {"product_ranking": "DESC"}, "pageSize": limit, "currentPage": 1}
    request_url = f"{GRAPHQL_URL}?{urlencode({'query': query, 'variables': json.dumps(variables)})}"
    request = Request(request_url, headers={"Accept": "application/json", "Store": "cbu"})
    with urlopen(request, timeout=60) as response:
        payload = json.load(response)
    items = payload.get("data", {}).get("products", {}).get("items", [])
    return items[:limit]


def brand_for(name: str) -> str:
    lowered = name.lower()
    if lowered.startswith(("home ", "data ", "sim ")) or lowered[:1].isdigit():
        return "Vodacom"
    return next((brand for brand in BRANDS if lowered.startswith(brand.lower())), name.split()[0] or "Vodacom")


def category_for(item: dict) -> str:
    name = str(item.get("name") or "").lower()
    category_keys = {str(c.get("url_key") or "").lower() for c in item.get("categories", [])}
    text = " ".join([name, str(item.get("package_description") or "").lower()] + [str(c.get("name") or "").lower() for c in item.get("categories", [])])
    if category_keys.intersection({"sim-only-deals", "sim", "sim-only"}) or name.startswith("sim ") or "data sim" in name:
        return "sim_only"
    if category_keys.intersection({"smartphones", "smartphone-deals", "pre-owned-deals"}):
        return "smartphone"
    if category_keys.intersection({"laptops", "laptop-deals"}):
        return "laptop"
    if category_keys.intersection({"tablets", "tablet-deals"}):
        return "tablet"
    if category_keys.intersection({"fibre", "fibre-deals"}):
        return "fibre"
    if category_keys.intersection({"lte", "lte-deals"}):
        return "lte"
    if category_keys.intersection({"5g", "5g-deals", "5g-home-internet"}):
        return "5g"
    if category_keys.intersection({"mobile-plans", "mobile-plan-deals"}):
        return "mobile_plan"
    if category_keys.intersection({"routers", "router-deals", "home-internet", "connectivity"}):
        return "router"
    if category_keys.intersection({"wearable-tech-deals", "accessories", "accessory-deals"}):
        return "accessory"
    if any(word in text for word in ("laptop", "notebook", "macbook")):
        return "laptop"
    if "tablet" in text or "ipad" in text:
        return "tablet"
    if any(word in text for word in ("smartphone", "iphone", "galaxy", "pixel", "phone")):
        return "smartphone"
    if any(word in text for word in ("fibre", "fiber")):
        return "fibre"
    if "lte" in text:
        return "lte"
    if "5g" in text or "internet" in text or "router" in text or "wi-fi" in text or "wifi" in text:
        return "router"
    if any(word in text for word in ("watch", "headphone", "earbud", "charger", "case", "accessory")):
        return "accessory"
    return "smartphone"


def integer(value) -> int | None:
    match = re.search(r"\d+", str(value or ""))
    return int(match.group()) if match else None


def normalise_item(item: dict, index: int, timestamp: str) -> dict[str, str]:
    category = category_for(item)
    monthly = item.get("monthly_recurring") or item.get("tariff") or item.get("installment")
    name = (item.get("name") or item.get("sku") or "Vodacom product").strip()[:180]
    sku = str(item.get("sku") or "").strip()
    gallery = [{"url": image.get("url"), "label": image.get("label") or name} for image in item.get("media_gallery", []) if image.get("url")]
    for image in [item.get("primary_product_image"), (item.get("image") or {}).get("url"), (item.get("small_image") or {}).get("url")]:
        if image and not any(existing["url"] == image for existing in gallery):
            gallery.append({"url": image, "label": name})
    storage_options = sorted(set(re.findall(r"\b(?:64|128|256|512|1024)GB\b", name, re.IGNORECASE)), key=lambda value: int(value[:-2]))
    specifications = {"package": item.get("package_description"), "tariff": item.get("tariff"), "device_installment": item.get("installment"), "source_sku": item.get("primary_product_sku"), "gallery": gallery, "storage_options": storage_options}
    return {
        "source_key": f"vodacom:{sku}", "network_code": "vodacom", "network_name": "Vodacom", "network_color": "#E60000",
        "sku": sku, "product_name": name, "slug": (item.get("url_key") or sku.lower())[:180], "brand": brand_for(name),
        "category": category, "deal_type": "sim_only" if category in {"sim_only", "mobile_plan"} else "internet" if category in {"router", "fibre", "lte", "5g"} else "accessory" if category == "accessory" else "device_contract",
        "monthly_price": str(monthly or ""), "cash_price": "", "upfront_cost": "", "contract_months": str(integer(item.get("payment_terms_label")) or ""),
        "data_mb": "", "voice_minutes": "", "sms_count": "", "speed_mbps": "", "start_at": "", "expires_at": "",
        "stock_status": str(item.get("stock_status") or "subject_to_confirmation").lower(), "source_document": SOURCE_URL,
        "administrator_notes": f"Vodacom catalogue snapshot fetched on {timestamp}; confirm partner pricing, stock, and terms before fulfilment.",
        "verified_at": f"{timestamp}T00:00:00Z", "terms_url": SOURCE_URL, "published": "true", "featured": "true" if index < 8 else "false",
        "image_url": str(item.get("primary_product_image") or (item.get("image") or {}).get("url") or (item.get("small_image") or {}).get("url") or ""), "description": (item.get("package_description") or name)[:500], "use_context": "both",
        "specifications_json": json.dumps(specifications, separators=(",", ":")),
    }


def main() -> int:
    timestamp = datetime.now(UTC).date().isoformat()
    rows = [normalise_item(item, index, timestamp) for index, item in enumerate(fetch_items()) if item.get("sku") and (item.get("primary_product_image") or (item.get("image") or {}).get("url") or (item.get("small_image") or {}).get("url"))]
    if not rows:
        raise RuntimeError("Vodacom returned no importable products")
    fieldnames = list(rows[0])
    snapshot = Path("data/vodacom-inventory-latest.csv")
    with snapshot.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    create_schema()
    source_keys = {row["source_key"] for row in rows}
    with SessionLocal() as session:
        result = CsvDealImporter(session).import_text(snapshot.read_text(encoding="utf-8"))
        if result.issues:
            session.rollback()
            raise RuntimeError("; ".join(f"row {i.row_number}: {i.message}" for i in result.issues))
        stale = session.scalars(select(Deal).where(Deal.source_key.like("vodacom:%"), ~Deal.source_key.in_(source_keys))).all()
        for deal in stale:
            deal.published = False
            deal.featured = False
        session.commit()
    brands = sorted({row["brand"] for row in rows})
    print(f"Imported {len(rows)} Vodacom rows across {len(brands)} brands; unpublished {len(stale)} stale rows: {', '.join(brands)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
