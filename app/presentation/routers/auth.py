from urllib.parse import urlparse

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.application.services.auth_service import AuthService
from app.core.config import Settings, get_settings
from app.core.dependencies import assert_csrf
from app.core.errors import ApplicationError
from app.core.security import issue_session_token
from app.infrastructure.db.session import get_db
from app.presentation.rendering import templates
from app.presentation.template_context import base_context


router = APIRouter()


def _safe_next(value: str | None) -> str:
    if not value:
        return "/account"
    parsed = urlparse(value)
    return value if not parsed.netloc and value.startswith("/") else "/account"


def _set_auth_cookies(
    response: RedirectResponse,
    *,
    token: str,
    csrf_token: str,
    settings: Settings,
) -> None:
    response.set_cookie(
        settings.session_cookie_name,
        token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=settings.session_ttl_minutes * 60,
    )
    response.set_cookie(
        settings.csrf_cookie_name,
        csrf_token,
        httponly=False,
        secure=settings.is_production,
        samesite="lax",
        max_age=settings.session_ttl_minutes * 60,
    )


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, next: str | None = None):
    return templates.TemplateResponse(
        request,
        "auth.html",
        base_context(request, title="Sign in", mode="login", next_url=_safe_next(next)),
    )


@router.post("/login")
async def login(
    request: Request,
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    form = await request.form()
    try:
        user = AuthService(session).authenticate(
            str(form.get("email") or ""), str(form.get("password") or "")
        )
        token, csrf_token = issue_session_token(user.id, user.role, settings)
        response = RedirectResponse(_safe_next(str(form.get("next") or "")), status_code=303)
        _set_auth_cookies(response, token=token, csrf_token=csrf_token, settings=settings)
        return response
    except ApplicationError as exc:
        return templates.TemplateResponse(
            request,
            "auth.html",
            base_context(
                request,
                title="Sign in",
                mode="login",
                error=str(exc),
                next_url=_safe_next(str(form.get("next") or "")),
            ),
            status_code=400,
        )


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(
        request,
        "auth.html",
        base_context(request, title="Create account", mode="register", next_url="/account"),
    )


@router.post("/register")
async def register(
    request: Request,
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    form = await request.form()
    try:
        user = AuthService(session).register_customer(
            email=str(form.get("email") or ""),
            password=str(form.get("password") or ""),
            full_name=str(form.get("full_name") or ""),
            phone=str(form.get("phone") or "") or None,
        )
        session.commit()
        token, csrf_token = issue_session_token(user.id, user.role, settings)
        response = RedirectResponse("/account", status_code=303)
        _set_auth_cookies(response, token=token, csrf_token=csrf_token, settings=settings)
        return response
    except ApplicationError as exc:
        session.rollback()
        return templates.TemplateResponse(
            request,
            "auth.html",
            base_context(
                request,
                title="Create account",
                mode="register",
                error=str(exc),
                next_url="/account",
            ),
            status_code=400,
        )


@router.post("/logout")
async def logout(request: Request, settings: Settings = Depends(get_settings)):
    await assert_csrf(request, settings)
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie(settings.session_cookie_name)
    response.delete_cookie(settings.csrf_cookie_name)
    return response
