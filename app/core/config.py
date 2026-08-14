from dataclasses import dataclass
from functools import lru_cache
import os

from app.core.errors import ConfigurationError


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_int(value: str | None, default: int) -> int:
    return int(value) if value else default


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_env: str
    app_base_url: str
    secret_key: str
    database_url: str
    auto_create_schema: bool
    session_cookie_name: str
    cart_cookie_name: str
    csrf_cookie_name: str
    session_ttl_minutes: int
    upload_backend: str
    upload_directory: str
    max_upload_bytes: int
    aws_region: str
    s3_bucket: str | None
    s3_public_base_url: str | None
    smtp_host: str | None
    smtp_port: int
    smtp_username: str | None
    smtp_password: str | None
    smtp_from_email: str
    smtp_use_tls: bool
    support_email: str
    support_phone: str | None
    whatsapp_number: str | None
    sales_team_email: str | None
    payment_provider: str
    payfast_merchant_id: str | None
    payfast_merchant_key: str | None
    payfast_passphrase: str | None
    payfast_process_url: str | None
    payfast_validate_url: str | None
    payfast_allowed_ips: tuple[str, ...]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    allowed_ips = tuple(
        item.strip()
        for item in os.getenv("PAYFAST_ALLOWED_IPS", "").split(",")
        if item.strip()
    )
    return Settings(
        app_name=os.getenv("APP_NAME", "Sir Device"),
        app_env=os.getenv("APP_ENV", "development"),
        app_base_url=os.getenv("APP_BASE_URL", "http://localhost:8000").rstrip("/"),
        secret_key=os.getenv("SECRET_KEY", "development-only-change-this-secret-key"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./sir_device.db"),
        auto_create_schema=_as_bool(os.getenv("AUTO_CREATE_SCHEMA"), True),
        session_cookie_name=os.getenv("SESSION_COOKIE_NAME", "sir_device_session"),
        cart_cookie_name=os.getenv("CART_COOKIE_NAME", "sir_device_cart"),
        csrf_cookie_name=os.getenv("CSRF_COOKIE_NAME", "sir_device_csrf"),
        session_ttl_minutes=_as_int(os.getenv("SESSION_TTL_MINUTES"), 720),
        upload_backend=os.getenv("UPLOAD_BACKEND", "local"),
        upload_directory=os.getenv("UPLOAD_DIRECTORY", "./var/uploads"),
        max_upload_bytes=_as_int(os.getenv("MAX_UPLOAD_BYTES"), 10 * 1024 * 1024),
        aws_region=os.getenv("AWS_REGION", "af-south-1"),
        s3_bucket=os.getenv("S3_BUCKET") or None,
        s3_public_base_url=os.getenv("S3_PUBLIC_BASE_URL") or None,
        smtp_host=os.getenv("SMTP_HOST") or None,
        smtp_port=_as_int(os.getenv("SMTP_PORT"), 587),
        smtp_username=os.getenv("SMTP_USERNAME") or None,
        smtp_password=os.getenv("SMTP_PASSWORD") or None,
        smtp_from_email=os.getenv("SMTP_FROM_EMAIL", "noreply@example.com"),
        smtp_use_tls=_as_bool(os.getenv("SMTP_USE_TLS"), True),
        support_email=os.getenv("SUPPORT_EMAIL", "deals@sirdevice.com"),
        support_phone=os.getenv("SUPPORT_PHONE") or None,
        whatsapp_number=os.getenv("WHATSAPP_NUMBER") or None,
        sales_team_email=os.getenv("SALES_TEAM_EMAIL") or None,
        payment_provider=os.getenv("PAYMENT_PROVIDER", "payfast"),
        payfast_merchant_id=os.getenv("PAYFAST_MERCHANT_ID") or None,
        payfast_merchant_key=os.getenv("PAYFAST_MERCHANT_KEY") or None,
        payfast_passphrase=os.getenv("PAYFAST_PASSPHRASE") or None,
        payfast_process_url=os.getenv("PAYFAST_PROCESS_URL") or None,
        payfast_validate_url=os.getenv("PAYFAST_VALIDATE_URL") or None,
        payfast_allowed_ips=allowed_ips,
    )


_DEVELOPMENT_SECRET = "development-only-change-this-secret-key"
_MINIMUM_PRODUCTION_SECRET_LENGTH = 32


def validate_settings(settings: Settings) -> None:
    if not settings.is_production:
        return
    if (
        settings.secret_key == _DEVELOPMENT_SECRET
        or len(settings.secret_key) < _MINIMUM_PRODUCTION_SECRET_LENGTH
    ):
        raise ConfigurationError("Production SECRET_KEY must be a strong unique value")
    if settings.auto_create_schema:
        raise ConfigurationError("Production must use Alembic with AUTO_CREATE_SCHEMA=false")
    if settings.database_url.startswith("sqlite"):
        raise ConfigurationError("Production DATABASE_URL must use PostgreSQL")
    if not settings.app_base_url.startswith("https://"):
        raise ConfigurationError("Production APP_BASE_URL must use HTTPS")
