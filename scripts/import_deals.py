from pathlib import Path
import sys

from app.application.services.import_service import CsvDealImporter
from app.infrastructure.db.session import SessionLocal, create_schema


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.import_deals path/to/deals.csv")
        return 2
    create_schema()
    path = Path(sys.argv[1])
    with SessionLocal() as session:
        result = CsvDealImporter(session).import_text(path.read_text(encoding="utf-8-sig"))
        if result.issues:
            session.rollback()
            for issue in result.issues:
                print(f"row {issue.row_number}: {issue.message}")
            return 1
        session.commit()
        print(
            f"Imported {result.rows_processed} rows; "
            f"{result.deals_created} created, {result.deals_updated} updated"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
