from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import SessionPrincipal, decode_session_token
from app.domain.enums import UserRole
from app.infrastructure.db.models import User
from app.infrastructure.db.session import get_db
from app.infrastructure.repositories.identity_repository import IdentityRepository


def get_principal(request: Request, settings: Settings | None = None) -> SessionPrincipal | None:
    resolved_settings = settings or get_settings()
    token = request.cookies.get(resolved_settings.session_cookie_name)
    return decode_session_token(token, resolved_settings) if token else None


def get_optional_user(
    request: Request,
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User | None:
    principal = get_principal(request, settings)
    if not principal:
        return None
    user = IdentityRepository(session).get_by_id(principal.user_id)
    return user if user and user.is_active else None


def get_required_user(user: User | None = Depends(get_optional_user)) -> User:
    if not user:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="Authentication required",
            headers={"Location": "/login"},
        )
    return user


def require_roles(allowed_roles: frozenset[UserRole]) -> Callable:
    def dependency(user: User = Depends(get_required_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        return user

    return dependency


async def assert_csrf(request: Request, settings: Settings | None = None) -> None:
    resolved_settings = settings or get_settings()
    principal = get_principal(request, resolved_settings)
    if not principal:
        return
    cookie_token = request.cookies.get(resolved_settings.csrf_cookie_name)
    submitted = request.headers.get("X-CSRF-Token")
    if not submitted:
        form = await request.form()
        submitted = str(form.get("csrf_token") or "")
    if not submitted or submitted != principal.csrf_token or cookie_token != principal.csrf_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token")
