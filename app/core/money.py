from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


CENTS = Decimal("100")


def parse_money_to_cents(value: str | None) -> int | None:
    if value is None or not value.strip():
        return None
    try:
        amount = Decimal(value.strip()).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise ValueError("Invalid monetary amount") from exc
    if amount < 0:
        raise ValueError("Monetary amounts cannot be negative")
    return int(amount * CENTS)


def format_money(cents: int | None) -> str:
    if cents is None:
        return "Price on request"
    return f"R{Decimal(cents) / CENTS:,.2f}"
