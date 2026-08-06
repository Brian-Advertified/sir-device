from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.application.services.cart_service import CartService
from app.application.services.notification_service import NotificationService
from app.core.config import Settings
from app.core.constants import REFERENCE_PREFIX_ORDER
from app.core.errors import ConfigurationError, ValidationError
from app.core.ids import new_reference
from app.domain.enums import NotificationTemplate, OrderStatus, PaymentStatus
from app.domain.ports import PaymentGateway, PaymentRedirect
from app.infrastructure.db.models import Order, OrderItem, Payment
from app.infrastructure.repositories.cart_repository import CartRepository
from app.infrastructure.repositories.commerce_repository import CommerceRepository


@dataclass(frozen=True)
class CheckoutResult:
    order: Order
    payment_redirect: PaymentRedirect | None
    payment_configuration_error: str | None


class CheckoutService:
    def __init__(
        self,
        session: Session,
        settings: Settings,
        payment_gateway: PaymentGateway,
    ) -> None:
        self._session = session
        self._settings = settings
        self._gateway = payment_gateway
        self._carts = CartRepository(session)
        self._commerce = CommerceRepository(session)
        self._cart_service = CartService(session)
        self._notifications = NotificationService(session)

    def create_order(
        self,
        *,
        user_id: str | None,
        session_token: str | None,
        customer: dict[str, str],
        delivery: dict[str, str],
    ) -> CheckoutResult:
        summary = self._cart_service.summary_for(user_id=user_id, session_token=session_token)
        if not summary or not summary.lines:
            raise ValidationError("Your cart is empty")
        required_customer = ("full_name", "email", "phone")
        required_delivery = ("line1", "city", "province", "postal_code")
        if any(not customer.get(field, "").strip() for field in required_customer):
            raise ValidationError("Complete all required customer fields")
        if any(not delivery.get(field, "").strip() for field in required_delivery):
            raise ValidationError("Complete all required delivery fields")

        reference = new_reference(REFERENCE_PREFIX_ORDER)
        order = Order(
            reference=reference,
            user_id=user_id,
            email=customer["email"].strip().lower(),
            phone=customer["phone"].strip(),
            status=OrderStatus.AWAITING_PAYMENT,
            payment_status=PaymentStatus.PENDING,
            subtotal_cents=summary.subtotal_cents,
            delivery_cents=0,
            total_cents=summary.subtotal_cents,
            customer_snapshot={key: value.strip() for key, value in customer.items()},
            delivery_snapshot={key: value.strip() for key, value in delivery.items()},
        )
        for line in summary.lines:
            order.items.append(
                OrderItem(
                    deal_id=line.deal.id,
                    quantity=line.item.quantity,
                    unit_price_cents=line.unit_price_cents,
                    snapshot={
                        "product_name": line.deal.product.name,
                        "sku": line.deal.product.sku,
                        "network": line.deal.network.display_name if line.deal.network else None,
                        "deal_type": line.deal.deal_type.value,
                    },
                )
            )
        self._commerce.add_order(order)
        payment = Payment(
            order_id=order.id,
            provider=self._gateway.name,
            provider_reference=reference,
            amount_cents=order.total_cents,
            status=PaymentStatus.PENDING,
            payload={},
        )
        self._commerce.add_payment(payment)
        self._carts.mark_converted(summary.cart)
        self._notifications.enqueue_email(
            recipient=order.email,
            template_key=NotificationTemplate.ORDER_CREATED.value,
            payload={"reference": reference, "total_cents": order.total_cents},
        )

        names = customer["full_name"].strip().split(maxsplit=1)
        first_name = names[0]
        last_name = names[1] if len(names) > 1 else "Customer"
        try:
            redirect = self._gateway.create_redirect(
                order_reference=reference,
                amount_cents=order.total_cents,
                item_name=f"Sir Device order {reference}",
                customer_email=order.email,
                customer_first_name=first_name,
                customer_last_name=last_name,
                return_url=f"{self._settings.app_base_url}/checkout/success/{reference}",
                cancel_url=f"{self._settings.app_base_url}/checkout/cancel/{reference}",
                notify_url=f"{self._settings.app_base_url}/api/v1/payments/payfast/notify",
            )
            return CheckoutResult(order=order, payment_redirect=redirect, payment_configuration_error=None)
        except ConfigurationError as exc:
            return CheckoutResult(
                order=order,
                payment_redirect=None,
                payment_configuration_error=str(exc),
            )

    def process_payment_notification(
        self,
        *,
        payload: dict[str, str],
        source_ip: str | None,
    ) -> bool:
        reference = payload.get("m_payment_id", "")
        order = self._commerce.get_order_by_reference(reference)
        if not order or not order.payments:
            return False
        if not self._gateway.validate_notification(
            payload=payload,
            source_ip=source_ip,
            expected_amount_cents=order.total_cents,
        ):
            return False
        payment = order.payments[-1]
        payment.payload = payload
        provider_status = payload.get("payment_status", "").upper()
        if provider_status == "COMPLETE":
            payment.status = PaymentStatus.PAID
            order.payment_status = PaymentStatus.PAID
            order.status = OrderStatus.PROCESSING
        else:
            payment.status = PaymentStatus.FAILED
            order.payment_status = PaymentStatus.FAILED
        return True
