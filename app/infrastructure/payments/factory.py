from app.core.config import Settings
from app.core.errors import ConfigurationError
from app.domain.enums import PaymentProvider
from app.domain.ports import PaymentGateway
from app.infrastructure.payments.payfast import PayFastPaymentGateway


def create_payment_gateway(settings: Settings) -> PaymentGateway:
    provider = settings.payment_provider.strip().lower()
    if provider == PaymentProvider.PAYFAST.value:
        return PayFastPaymentGateway(settings)
    raise ConfigurationError(f"Unsupported payment provider: {provider}")
