from datetime import UTC, datetime


def utc_now() -> datetime:
    return datetime.now(UTC)


def parse_optional_datetime(value: str | None) -> datetime | None:
    if value is None or not value.strip():
        return None
    parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)
