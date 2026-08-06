from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.application.services.cart_service import CartService
from app.application.services.checkout_service import CheckoutService
from app.core.config import Settings, get_settings
from app.core.dependencies import assert_csrf, get_optional_user
from app.core.errors import ApplicationError
from app.core.security import new_cart_token
from app.infrastructure.db.models import User
from app.infrastructure.db.session import get_db
from app.infrastructure.payments.factory import create_payment_gateway
from app.infrastructure.repositories.commerce_repository import CommerceRepository
from app.presentation.rendering import templates
from app.presentation.template_context import base_context


router = APIRouter()


def _identity(request: Request, user: User | None, settings: Settings) -> tuple[str | None, str | None]:
    return (
        user.id if user else None,
        None if user else request.cookies.get(settings.cart_cookie_name),
    )


def _ensure_cart_token(request: Request, user: User | None, settings: Settings) -> str | None:
    if user:
        return None
    return request.cookies.get(settings.cart_cookie_name) or new_cart_token()


@router.get("/cart", response_class=HTMLResponse)
def cart_page(
    request: Request,
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User | None = Depends(get_optional_user),
):
    user_id, session_token = _identity(request, user, settings)
    summary = CartService(session).summary_for(user_id=user_id, session_token=session_token)
    return templates.TemplateResponse(
        request,
        "cart.html",
        base_context(request, title="Your cart", summary=summary),
    )


@router.post("/api/v1/cart/items")
async def add_cart_item(
    request: Request,
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User | None = Depends(get_optional_user),
):
    await assert_csrf(request, settings)
    payload = await request.json()
    session_token = _ensure_cart_token(request, user, settings)
    try:
        summary = CartService(session).add_item(
            user_id=user.id if user else None,
            session_token=session_token,
            deal_id=str(payload.get("deal_id") or ""),
            quantity=int(payload.get("quantity") or 1),
        )
        session.commit()
        response = JSONResponse({"item_count": summary.item_count, "cart_url": "/cart"})
        if session_token and not user:
            response.set_cookie(
                settings.cart_cookie_name,
                session_token,
                httponly=True,
                secure=settings.is_production,
                samesite="lax",
                max_age=30 * 24 * 60 * 60,
            )
        return response
    except (ApplicationError, ValueError) as exc:
        session.rollback()
        return JSONResponse({"error": str(exc)}, status_code=400)


@router.post("/cart/items/{deal_id}")
async def update_cart_item(
    request: Request,
    deal_id: str,
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User | None = Depends(get_optional_user),
):
    await assert_csrf(request, settings)
    form = await request.form()
    user_id, session_token = _identity(request, user, settings)
    try:
        CartService(session).update_item(
            user_id=user_id,
            session_token=session_token,
            deal_id=deal_id,
            quantity=int(form.get("quantity") or 0),
        )
        session.commit()
    except (ApplicationError, ValueError):
        session.rollback()
    return RedirectResponse("/cart", status_code=303)


@router.get("/checkout", response_class=HTMLResponse)
def checkout_page(
    request: Request,
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User | None = Depends(get_optional_user),
):
    user_id, session_token = _identity(request, user, settings)
    summary = CartService(session).summary_for(user_id=user_id, session_token=session_token)
    if not summary or not summary.lines:
        return RedirectResponse("/cart", status_code=303)
    return templates.TemplateResponse(
        request,
        "checkout.html",
        base_context(request, title="Checkout", summary=summary, user=user, error=None),
    )


@router.post("/checkout", response_class=HTMLResponse)
async def checkout_submit(
    request: Request,
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User | None = Depends(get_optional_user),
):
    await assert_csrf(request, settings)
    form = await request.form()
    user_id, session_token = _identity(request, user, settings)
    customer = {
        "full_name": str(form.get("full_name") or ""),
        "email": str(form.get("email") or ""),
        "phone": str(form.get("phone") or ""),
    }
    delivery = {
        "line1": str(form.get("line1") or ""),
        "line2": str(form.get("line2") or ""),
        "city": str(form.get("city") or ""),
        "province": str(form.get("province") or ""),
        "postal_code": str(form.get("postal_code") or ""),
    }
    try:
        service = CheckoutService(session, settings, create_payment_gateway(settings))
        result = service.create_order(
            user_id=user_id,
            session_token=session_token,
            customer=customer,
            delivery=delivery,
        )
        session.commit()
        return templates.TemplateResponse(
            request,
            "payment_redirect.html",
            base_context(
                request,
                title="Payment",
                result=result,
            ),
        )
    except ApplicationError as exc:
        session.rollback()
        summary = CartService(session).summary_for(user_id=user_id, session_token=session_token)
        return templates.TemplateResponse(
            request,
            "checkout.html",
            base_context(
                request,
                title="Checkout",
                summary=summary,
                user=user,
                error=str(exc),
            ),
            status_code=400,
        )


@router.get("/checkout/success/{reference}", response_class=HTMLResponse)
def checkout_success(request: Request, reference: str, session: Session = Depends(get_db)):
    order = CommerceRepository(session).get_order_by_reference(reference)
    return templates.TemplateResponse(
        request,
        "order_result.html",
        base_context(request, title="Order received", order=order, cancelled=False),
    )


@router.get("/checkout/cancel/{reference}", response_class=HTMLResponse)
def checkout_cancel(request: Request, reference: str, session: Session = Depends(get_db)):
    order = CommerceRepository(session).get_order_by_reference(reference)
    return templates.TemplateResponse(
        request,
        "order_result.html",
        base_context(request, title="Payment cancelled", order=order, cancelled=True),
    )


@router.post("/api/v1/payments/payfast/notify")
async def payfast_notify(
    request: Request,
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    form = await request.form()
    payload = {str(key): str(value) for key, value in form.items()}
    service = CheckoutService(session, settings, create_payment_gateway(settings))
    valid = service.process_payment_notification(
        payload=payload,
        source_ip=request.client.host if request.client else None,
    )
    if valid:
        session.commit()
        return JSONResponse({"status": "accepted"})
    session.rollback()
    return JSONResponse({"status": "rejected"}, status_code=400)
