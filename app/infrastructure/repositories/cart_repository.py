from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.domain.enums import CartStatus
from app.infrastructure.db.models import Cart, CartItem, Deal


class CartRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_active(self, *, user_id: str | None, session_token: str | None) -> Cart | None:
        statement = select(Cart).where(Cart.status == CartStatus.ACTIVE)
        if user_id:
            statement = statement.where(Cart.user_id == user_id)
        elif session_token:
            statement = statement.where(Cart.session_token == session_token)
        else:
            return None
        return self._session.scalar(statement)

    def get_or_create(self, *, user_id: str | None, session_token: str | None) -> Cart:
        cart = self.get_active(user_id=user_id, session_token=session_token)
        if cart:
            return cart
        cart = Cart(user_id=user_id, session_token=None if user_id else session_token)
        self._session.add(cart)
        self._session.flush()
        return cart

    def get_with_items(self, cart_id: str) -> Cart | None:
        statement = (
            select(Cart)
            .options(
                joinedload(Cart.items).joinedload(CartItem.deal).joinedload(Deal.product),
                joinedload(Cart.items).joinedload(CartItem.deal).joinedload(Deal.network),
            )
            .where(Cart.id == cart_id)
        )
        return self._session.scalars(statement).unique().one_or_none()

    def get_item(self, cart_id: str, deal_id: str) -> CartItem | None:
        statement = select(CartItem).where(
            CartItem.cart_id == cart_id, CartItem.deal_id == deal_id
        )
        return self._session.scalar(statement)

    def add_item(self, cart: Cart, deal_id: str, quantity: int) -> CartItem:
        item = self.get_item(cart.id, deal_id)
        if item:
            item.quantity += quantity
        else:
            item = CartItem(cart_id=cart.id, deal_id=deal_id, quantity=quantity)
            self._session.add(item)
        self._session.flush()
        return item

    def update_item(self, item: CartItem, quantity: int) -> None:
        if quantity <= 0:
            self._session.delete(item)
        else:
            item.quantity = quantity
        self._session.flush()

    def mark_converted(self, cart: Cart) -> None:
        cart.status = CartStatus.CONVERTED
        self._session.flush()
