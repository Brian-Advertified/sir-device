from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.infrastructure.db.models import Order, Payment


class CommerceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_order(self, order: Order) -> Order:
        self._session.add(order)
        self._session.flush()
        return order

    def add_payment(self, payment: Payment) -> Payment:
        self._session.add(payment)
        self._session.flush()
        return payment

    def get_order(self, order_id: str) -> Order | None:
        statement = (
            select(Order)
            .options(joinedload(Order.items), joinedload(Order.payments))
            .where(Order.id == order_id)
        )
        return self._session.scalars(statement).unique().one_or_none()

    def get_order_by_reference(self, reference: str) -> Order | None:
        statement = (
            select(Order)
            .options(joinedload(Order.items), joinedload(Order.payments))
            .where(Order.reference == reference)
        )
        return self._session.scalars(statement).unique().one_or_none()

    def list_orders(self, *, user_id: str | None = None, limit: int = 300) -> list[Order]:
        statement = select(Order).options(joinedload(Order.items))
        if user_id:
            statement = statement.where(Order.user_id == user_id)
        statement = statement.order_by(Order.created_at.desc()).limit(limit)
        return list(self._session.scalars(statement).unique())

    def get_payment_by_provider_reference(self, reference: str) -> Payment | None:
        statement = select(Payment).where(Payment.provider_reference == reference)
        return self._session.scalar(statement)
