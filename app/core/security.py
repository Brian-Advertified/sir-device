from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import os
from secrets import token_urlsafe

import jwt

from app.core.config import Settings
from app.domain.enums import UserRole


_JWT_ALGORITHM = "HS256"
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SALT_BYTES = 16


@dataclass(frozen=True)
class SessionPrincipal:
    user_id: str
    role: UserRole
    csrf_token: str


def hash_password(password: str) -> str:
    if len(password) < 10:
        raise ValueError("Password must be at least 10 characters")
    salt = os.urandom(_SALT_BYTES)
    derived = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P
    )
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${salt.hex()}${derived.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, n, r, p, salt_hex, expected_hex = encoded.split("$")
        if algorithm != "scrypt":
            return False
        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=bytes.fromhex(salt_hex),
            n=int(n),
            r=int(r),
            p=int(p),
        )
        return hmac.compare_digest(actual.hex(), expected_hex)
    except (ValueError, TypeError):
        return False


def issue_session_token(user_id: str, role: UserRole, settings: Settings) -> tuple[str, str]:
    csrf_token = token_urlsafe(24)
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "role": role.value,
        "csrf": csrf_token,
        "iat": now,
        "exp": now + timedelta(minutes=settings.session_ttl_minutes),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=_JWT_ALGORITHM)
    return token, csrf_token


def decode_session_token(token: str, settings: Settings) -> SessionPrincipal | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[_JWT_ALGORITHM])
        return SessionPrincipal(
            user_id=str(payload["sub"]),
            role=UserRole(str(payload["role"])),
            csrf_token=str(payload["csrf"]),
        )
    except (jwt.PyJWTError, KeyError, ValueError):
        return None


def new_cart_token() -> str:
    return token_urlsafe(24)
