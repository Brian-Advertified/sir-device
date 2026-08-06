import pytest
from app.core.config import get_settings
from app.core.security import (
    decode_session_token,
    hash_password,
    issue_session_token,
    verify_password,
)
from app.domain.enums import UserRole


def test_password_hash_is_salted_and_verifiable():
    first = hash_password("A-strong-password-123")
    second = hash_password("A-strong-password-123")
    assert first != second
    assert verify_password("A-strong-password-123", first)
    assert not verify_password("wrong-password", first)


def test_session_token_round_trip():
    settings = get_settings()
    token, csrf = issue_session_token("user-id", UserRole.CUSTOMER, settings)
    principal = decode_session_token(token, settings)
    assert principal is not None
    assert principal.user_id == "user-id"
    assert principal.role == UserRole.CUSTOMER
    assert principal.csrf_token == csrf


def test_production_configuration_fails_closed():
    from dataclasses import replace

    from app.core.config import get_settings, validate_settings
    from app.core.errors import ConfigurationError

    insecure = replace(get_settings(), app_env="production")
    with pytest.raises(ConfigurationError):
        validate_settings(insecure)
