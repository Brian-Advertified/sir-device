from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, ValidationError
from app.domain.policies import DealAvailabilityPolicy
from app.infrastructure.db.models import Cart, CartItem, Deal
from app.infrastructure.repositories.cart_repository import CartRepository
from app.infrastructure.repositories.catalog_repository import CatalogRepository


@dataclass(frozen=True)
class CartLine:
    item: CartItem
    deal: Deal
    unit_price_cents: int
    line_total_cents: int


@dataclass(frozen=True)
class CartSummary:
    cart: Cart
    lines: tuple[CartLine, ...]
    subtotal_cents: int
    item_count: int


class CartService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._carts = CartRepository(session)
        self._catalogue = CatalogRepository(session)

    def get_or_create_cart(self, *, user_id: str | None, session_token: str | None) -> Cart:
        return self._carts.get_or_create(user_id=user_id, session_token=session_token)

    def add_item(
        self,
        *,
        user_id: str | None,
        session_token: str | None,
        deal_id: str,
        quantity: int,
    ) -> CartSummary:
        if quantity < 1 or quantity > 20:
            raise ValidationError("Quantity must be between 1 and 20")
        deal = self._catalogue.get_public_deal(deal_id)
        if not deal:
            raise NotFoundError("This deal is no longer available")
        if not DealAvailabilityPolicy.is_direct_purchase(deal.deal_type, deal.cash_price_cents):
            raise ValidationError("This offer requires an application rather than direct checkout")
        cart = self._carts.get_or_create(user_id=user_id, session_token=session_token)
        self._carts.add_item(cart, deal.id, quantity)
        return self.summary(cart)

    def update_item(
        self,
        *,
        user_id: str | None,
        session_token: str | None,
        deal_id: str,
        quantity: int,
    ) -> CartSummary:
        cart = self._carts.get_active(user_id=user_id, session_token=session_token)
        if not cart:
            raise NotFoundError("Cart not found")
        item = self._carts.get_item(cart.id, deal_id)
        if not item:
            raise NotFoundError("Cart item not found")
        if quantity > 20:
            raise ValidationError("Quantity cannot exceed 20")
        self._carts.update_item(item, quantity)
        return self.summary(cart)

    def summary_for(self, *, user_id: str | None, session_token: str | None) -> CartSummary | None:
        cart = self._carts.get_active(user_id=user_id, session_token=session_token)
        return self.summary(cart) if cart else None

    def summary(self, cart: Cart) -> CartSummary:
        loaded = self._carts.get_with_items(cart.id) or cart
        lines: list[CartLine] = []
        subtotal = 0
        count = 0
        for item in loaded.items:
            price = item.deal.cash_price_cents
            if price is None:
                continue
            line_total = price * item.quantity
            subtotal += line_total
            count += item.quantity
            lines.append(
                CartLine(
                    item=item,
                    deal=item.deal,
                    unit_price_cents=price,
                    line_total_cents=line_total,
                )
            )
        return CartSummary(
            cart=loaded,
            lines=tuple(lines),
            subtotal_cents=subtotal,
            item_count=count,
        )
