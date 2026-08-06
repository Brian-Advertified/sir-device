from collections import OrderedDict
from hashlib import md5
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.core.config import Settings
from app.core.errors import ConfigurationError
from app.domain.enums import PaymentProvider
from app.domain.ports import PaymentRedirect


class PayFastPaymentGateway:
    name = PaymentProvider.PAYFAST.value

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def _require_configuration(self) -> None:
        required = {
            "PAYFAST_MERCHANT_ID": self._settings.payfast_merchant_id,
            "PAYFAST_MERCHANT_KEY": self._settings.payfast_merchant_key,
            "PAYFAST_PROCESS_URL": self._settings.payfast_process_url,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ConfigurationError(f"Payment gateway is not configured: {', '.join(missing)}")

    def _signature(self, fields: dict[str, str]) -> str:
        ordered = OrderedDict(
            (key, str(value).strip())
            for key, value in fields.items()
            if value is not None and str(value).strip() and key != "signature"
        )
        query = urlencode(list(ordered.items()))
        if self._settings.payfast_passphrase:
            query = f"{query}&passphrase={urlencode({'value': self._settings.payfast_passphrase})[6:]}"
        return md5(query.encode("utf-8"), usedforsecurity=False).hexdigest()

    def create_redirect(
        self,
        *,
        order_reference: str,
        amount_cents: int,
        item_name: str,
        customer_email: str,
        customer_first_name: str,
        customer_last_name: str,
        return_url: str,
        cancel_url: str,
        notify_url: str,
    ) -> PaymentRedirect:
        self._require_configuration()
        fields = OrderedDict(
            merchant_id=self._settings.payfast_merchant_id or "",
            merchant_key=self._settings.payfast_merchant_key or "",
            return_url=return_url,
            cancel_url=cancel_url,
            notify_url=notify_url,
            name_first=customer_first_name,
            name_last=customer_last_name,
            email_address=customer_email,
            m_payment_id=order_reference,
            amount=f"{amount_cents / 100:.2f}",
            item_name=item_name[:100],
        )
        fields["signature"] = self._signature(fields)
        return PaymentRedirect(
            action_url=self._settings.payfast_process_url or "",
            fields=dict(fields),
        )

    def validate_notification(
        self,
        *,
        payload: dict[str, str],
        source_ip: str | None,
        expected_amount_cents: int,
    ) -> bool:
        self._require_configuration()
        if self._settings.payfast_allowed_ips:
            if not source_ip or source_ip not in self._settings.payfast_allowed_ips:
                return False
        received_signature = payload.get("signature", "")
        if not received_signature or self._signature(payload) != received_signature:
            return False
        try:
            received_cents = round(float(payload.get("amount_gross", "0")) * 100)
        except ValueError:
            return False
        if received_cents != expected_amount_cents:
            return False
        if not self._settings.payfast_validate_url:
            return True
        encoded = urlencode(payload).encode("utf-8")
        request = Request(self._settings.payfast_validate_url, data=encoded, method="POST")
        with urlopen(request, timeout=10) as response:  # nosec B310 - configured provider URL
            return response.read().decode("utf-8").strip().upper() == "VALID"
