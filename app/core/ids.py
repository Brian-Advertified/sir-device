from datetime import UTC, datetime
from secrets import token_hex
from uuid import uuid4


def new_id() -> str:
    return str(uuid4())


def new_reference(prefix: str) -> str:
    timestamp = datetime.now(UTC).strftime("%y%m%d")
    return f"{prefix}-{timestamp}-{token_hex(3).upper()}"
