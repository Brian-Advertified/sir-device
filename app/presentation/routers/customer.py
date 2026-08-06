from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.constants import ADMIN_ROLES
from app.application.services.customer_service import CustomerService
from app.core.dependencies import assert_csrf, get_required_user
from app.infrastructure.db.models import User
from app.infrastructure.db.session import get_db
from app.infrastructure.repositories.application_repository import ApplicationRepository
from app.infrastructure.repositories.catalog_repository import CatalogRepository
from app.infrastructure.repositories.commerce_repository import CommerceRepository
from app.presentation.rendering import templates
from app.presentation.template_context import base_context


router = APIRouter()


@router.get("/account", response_class=HTMLResponse)
def account_page(
    request: Request,
    session: Session = Depends(get_db),
    user: User = Depends(get_required_user),
):
    applications = ApplicationRepository(session).list_applications(user_id=user.id)
    quotes = ApplicationRepository(session).list_quotes(user_id=user.id)
    orders = CommerceRepository(session).list_orders(user_id=user.id)
    saved_products = CatalogRepository(session).list_saved_products(user.id)
    return templates.TemplateResponse(
        request,
        "account.html",
        base_context(
            request,
            title="My account",
            user=user,
            applications=applications,
            quotes=quotes,
            orders=orders,
            saved_products=saved_products,
        ),
    )


@router.get("/protected-files/{storage_key:path}")
def protected_file(
    storage_key: str,
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(get_required_user),
):
    applications = ApplicationRepository(session).list_applications(
        user_id=None if user.role in ADMIN_ROLES else user.id,
        limit=1000,
    )
    allowed_keys = {
        document.storage_key
        for application in applications
        for document in application.documents
    }
    if storage_key not in allowed_keys:
        raise HTTPException(status_code=404, detail="File not found")
    if settings.upload_backend != "local":
        from app.infrastructure.storage.factory import create_file_storage

        url = create_file_storage(settings).create_download_url(storage_key)
        return RedirectResponse(url, status_code=303)
    root = Path(settings.upload_directory).resolve()
    file_path = (root / storage_key).resolve()
    if root not in file_path.parents or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)


@router.post("/account/profile")
async def update_profile(
    request: Request,
    session: Session = Depends(get_db),
    user: User = Depends(get_required_user),
):
    await assert_csrf(request)
    form = await request.form()
    CustomerService(session).update_profile(
        user_id=user.id,
        full_name=str(form.get("full_name") or ""),
        phone=str(form.get("phone") or "") or None,
    )
    session.commit()
    return RedirectResponse("/account#profile", status_code=303)


@router.post("/saved-products/{product_id}")
async def save_product(
    request: Request,
    product_id: str,
    session: Session = Depends(get_db),
    user: User = Depends(get_required_user),
):
    await assert_csrf(request)
    CustomerService(session).save_product(user_id=user.id, product_id=product_id)
    session.commit()
    return RedirectResponse("/account#saved", status_code=303)


@router.post("/saved-products/{product_id}/remove")
async def remove_saved_product(
    request: Request,
    product_id: str,
    session: Session = Depends(get_db),
    user: User = Depends(get_required_user),
):
    await assert_csrf(request)
    CustomerService(session).remove_saved_product(user_id=user.id, product_id=product_id)
    session.commit()
    return RedirectResponse("/account#saved", status_code=303)


@router.get("/account/orders/{reference}/invoice")
def download_invoice(
    request: Request,
    reference: str,
    session: Session = Depends(get_db),
    user: User = Depends(get_required_user),
):
    order = CommerceRepository(session).get_order_by_reference(reference)
    if not order or order.user_id != user.id:
        raise HTTPException(status_code=404, detail="Invoice not found")
    rendered = templates.env.get_template("invoice.html").render(
        base_context(request, title=f"Invoice {order.reference}", order=order, user=user)
    )
    return Response(
        rendered,
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="{order.reference}-invoice.html"'},
    )
