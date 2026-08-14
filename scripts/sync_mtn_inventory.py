from __future__ import annotations

import argparse
import csv
import io
import json
import re
import time
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.application.services.import_service import CsvDealImporter
from app.infrastructure.db.session import SessionLocal, create_schema
from scripts.mtn_plan_catalogue import plan_benefits


STORE_API = "https://mtndeals.co.za/wp-json/wc/store/v1/products"
LOCAL_DEVICE_IMAGE = "/static/img/mtn-device-plan.svg"
LOCAL_DATA_IMAGE = "/static/img/mtn-data-plan.svg"
LOCAL_SIM_IMAGE = "/static/img/mtn-sim-plan.svg"


def _packaged_image_url(source_url: str) -> str:
    """Use a bundled MTN image when available, otherwise keep the source URL."""
    import hashlib
    from pathlib import Path
    from urllib.parse import urlparse

    suffix = Path(urlparse(source_url).path).suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        suffix = ".jpg"
    filename = f"{hashlib.sha256(source_url.encode('utf-8')).hexdigest()[:20]}{suffix}"
    image_path = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "presentation"
        / "static"
        / "img"
        / "products"
        / filename
    )
    return f"/static/img/products/{filename}" if image_path.is_file() else source_url
BRANDS = {
    "apple", "samsung", "huawei", "honor", "oppo", "vivo", "xiaomi", "zte",
    "hisense", "mobicel", "cat", "crosscall", "nokia", "nothing", "tozed",
    "lenovo", "hp", "dell", "asus", "acer", "motorola",
}
COLOUR_TOKENS = {
    "black", "white", "blue", "green", "grey", "gray", "gold", "silver", "pink",
    "purple", "violet", "orange", "graphite", "charcoal", "midnight", "titanium",
}


def _fetch_store_products() -> list[dict[str, str]]:
    products: list[dict[str, str]] = []
    page = 1
    per_page = 25
    while True:
        query = urlencode({"per_page": per_page, "page": page})
        request = Request(f"{STORE_API}?{query}", headers={"User-Agent": "SirDevice-MTN-Sync/1.0"})
        payload = None
        for attempt in range(3):
            try:
                with urlopen(request, timeout=60) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                break
            except TimeoutError:
                if attempt == 2:
                    raise
                time.sleep(2 * (attempt + 1))
        assert payload is not None
        if not payload:
            break
        for item in payload:
            images = item.get("images") or []
            image = images[0].get("src", "") if images else ""
            if item.get("name") and image:
                products.append({
                    "name": item["name"],
                    "image": image,
                    "page": item.get("permalink", ""),
                })
        if len(payload) < per_page:
            break
        page += 1
    return products


def _ascii(value: str) -> str:
    return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")


def _tokens(value: str) -> list[str]:
    normalized = _ascii(value).lower().replace("+", " plus ")
    normalized = re.sub(r"\bwi[ -]?fi\b", "wifi", normalized)
    return re.findall(r"[a-z]+\d+[a-z]*|\d+[a-z]+|[a-z]+|\d+", normalized)


def _match_key(value: str) -> str:
    tokens = [
        token for token in _tokens(value)
        if token not in BRANDS and token not in COLOUR_TOKENS and token not in {"smartphone", "phone"}
    ]
    return " ".join(tokens)


def _score(target: str, candidate: str) -> float:
    left = _match_key(target)
    right = _match_key(candidate)
    if not left or not right:
        return 0.0
    left_compact = left.replace(" ", "")
    right_compact = right.replace(" ", "")
    if left_compact == right_compact:
        return 1.0
    ratio = max(
        SequenceMatcher(None, left, right).ratio(),
        SequenceMatcher(None, left_compact, right_compact).ratio(),
    )
    if left_compact in right_compact or right_compact in left_compact:
        ratio = max(ratio, 0.9 - abs(len(left_compact) - len(right_compact)) / 200)
    target_numbers = {token for token in _tokens(left) if any(char.isdigit() for char in token)}
    candidate_numbers = {token for token in _tokens(right) if any(char.isdigit() for char in token)}
    if target_numbers and not target_numbers.intersection(candidate_numbers):
        ratio -= 0.35
    return ratio


def _match_product(name: str, products: list[dict[str, str]]) -> tuple[dict[str, str] | None, float]:
    primary_name = re.split(r"\s+\+\s+", name, maxsplit=1)[0]
    best: dict[str, str] | None = None
    best_score = 0.0
    for product in products:
        score = _score(primary_name, product["name"])
        if score > best_score:
            best = product
            best_score = score
    return (best, best_score) if best_score >= 0.76 else (None, best_score)


def _enrich_rows(source: Path, output: Path) -> tuple[int, int, int, int]:
    with source.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    store_products = _fetch_store_products()
    matches: dict[str, tuple[dict[str, str] | None, float]] = {}
    for name in sorted({row["product_name"] for row in rows}):
        lowered = name.lower()
        if "uncapped data" in lowered:
            matches[name] = ({"name": "MTN uncapped data", "image": LOCAL_DATA_IMAGE, "page": ""}, 1.0)
        elif lowered in {"sim only", "use your own"} or lowered.startswith("use your own"):
            matches[name] = ({"name": "MTN SIM-only", "image": LOCAL_SIM_IMAGE, "page": ""}, 1.0)
        else:
            matches[name] = _match_product(name, store_products)

    exact_names = 0
    exact_rows = 0
    for name, (match, score) in matches.items():
        if match and match["image"].startswith("https://mtndeals.co.za/"):
            exact_names += 1
    for row in rows:
        match, score = matches[row["product_name"]]
        if match:
            row["image_url"] = _packaged_image_url(match["image"])
            if match["image"].startswith("https://mtndeals.co.za/"):
                exact_rows += 1
            specs = json.loads(row.get("specifications_json") or "{}")
            specs.update({"image_match": match["name"], "image_match_score": round(score, 3)})
            if match.get("page"):
                specs["image_source"] = match["page"]
            row["specifications_json"] = json.dumps(specs, separators=(",", ":"))
        else:
            row["image_url"] = LOCAL_DEVICE_IMAGE
            row["administrator_notes"] += "; using MTN fallback artwork because device is absent from current MTN store"
        row["published"] = "true"

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows), len(matches), exact_rows, exact_names


def import_mtn_inventory(csv_path: Path) -> int:
    create_schema()
    with SessionLocal() as session:
        source_text = csv_path.read_text(encoding="utf-8-sig")
        reader = csv.DictReader(io.StringIO(source_text))
        fieldnames = list(reader.fieldnames or [])
        normalized = io.StringIO()
        writer = csv.DictWriter(normalized, fieldnames=fieldnames)
        writer.writeheader()
        for row in reader:
            try:
                specifications = json.loads(row.get("specifications_json") or "{}")
            except (TypeError, json.JSONDecodeError):
                specifications = {}
            price_plan = str(specifications.get("price_plan") or "").strip().lower()
            benefits = plan_benefits(price_plan)
            specifications["plan_benefits"] = benefits
            row["specifications_json"] = json.dumps(specifications, separators=(",", ":"))
            row["data_mb"] = str(benefits["data_mb"] or "")
            row["voice_minutes"] = str(benefits["voice_minutes"] or "")
            row["sms_count"] = str(benefits["sms_count"] or "")
            row["speed_mbps"] = str(benefits["speed_mbps"] or "")
            row["use_context"] = (
                "business"
                if "business" in price_plan or "made for executive" in price_plan or "made to share" in price_plan
                else "personal"
            )
            base_slug = row.get("slug", "mtn-contract").rsplit("-", 1)[0]
            deal_suffix = re.sub(r"[^a-z0-9]+", "-", row.get("sku", "").lower()).strip("-")
            row["slug"] = f"{base_slug}-{deal_suffix}"[:180]
            writer.writerow(row)
        result = CsvDealImporter(session).import_text(normalized.getvalue())
        if result.issues:
            session.rollback()
            details = "; ".join(f"row {issue.row_number}: {issue.message}" for issue in result.issues[:20])
            raise RuntimeError(f"MTN import rejected; all database changes rolled back. {details}")
        session.commit()
        return result.rows_processed


def main() -> int:
    parser = argparse.ArgumentParser(description="Enrich and import MTN contracts without changing other networks.")
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, default=Path("data/mtn-contracts-ready.csv"))
    parser.add_argument("--prepared", action="store_true", help="Source is already enriched; skip the MTN store fetch.")
    parser.add_argument("--import", dest="import_inventory", action="store_true", help="Import the prepared MTN rows while preserving other network inventories.")
    args = parser.parse_args()

    import_path = args.source
    if args.prepared:
        print(f"Using prepared MTN import {import_path}.")
    else:
        rows, names, exact_rows, exact_names = _enrich_rows(args.source, args.output)
        import_path = args.output
        print(f"Prepared {rows} MTN contract rows across {names} product names; MTN store images matched {exact_rows} rows / {exact_names} names.")
    if args.import_inventory:
        imported = import_mtn_inventory(import_path)
        print(f"Imported {imported} MTN rows; other network inventories were preserved.")
    else:
        print(f"Review {import_path}, then rerun with --prepared --import to update the database.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
