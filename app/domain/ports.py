from dataclasses import dataclass
from typing import BinaryIO, Protocol


@dataclass(frozen=True)
class StoredFile:
    key: str
    size_bytes: int
    content_type: str


class FileStorage(Protocol):
    def save(
        self,
        *,
        source: BinaryIO,
        original_name: str,
        content_type: str,
        namespace: str,
        max_bytes: int,
    ) -> StoredFile: ...

    def create_download_url(self, key: str, expires_seconds: int = 300) -> str: ...


@dataclass(frozen=True)
class PaymentRedirect:
    action_url: str
    fields: dict[str, str]


class PaymentGateway(Protocol):
    name: str

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
    ) -> PaymentRedirect: ...

    def validate_notification(
        self,
        *,
        payload: dict[str, str],
        source_ip: str | None,
        expected_amount_cents: int,
    ) -> bool: ...


class EmailSender(Protocol):
    def send(self, *, recipient: str, subject: str, body: str) -> None: ...
