from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.application.services.application_service import ApplicationService
from app.application.services.notification_service import NotificationService
from app.application.services.audit_service import AuditService
from app.application.services.quote_service import QuoteService
from app.core.config import get_settings
from app.core.constants import (
    APPLICATION_MANAGEMENT_ROLES,
    ORDER_MANAGEMENT_ROLES,
)
from app.core.dependencies import assert_csrf, require_roles
from app.core.errors import ApplicationError
from app.domain.enums import (
    ApplicationStatus,
    AuditAction,
    AuditEntityType,
    NotificationTemplate,
    OrderStatus,
    QuoteStatus,
)
from app.infrastructure.db.models import User
from app.infrastructure.db.session import get_db
from app.infrastructure.repositories.application_repository import ApplicationRepository
from app.infrastructure.repositories.commerce_repository import CommerceRepository
from app.infrastructure.repositories.operations_repository import OperationsRepository
from app.infrastructure.storage.factory import create_file_storage
from app.presentation.rendering import templates
from app.presentation.template_context import base_context


router = APIRouter(prefix="/admin")


@router.get("/applications", response_class=HTMLResponse)
def applications_admin(
    request: Request,
    session: Session = Depends(get_db),
    user: User = Depends(require_roles(APPLICATION_MANAGEMENT_ROLES)),
):
    return templates.TemplateResponse(
        request,
        "admin/applications.html",
        base_context(
            request,
            title="Applications",
            admin_user=user,
            applications=ApplicationRepository(session).list_applications(),
        ),
    )


@router.post("/applications/{application_id}/status")
async def change_application_status(
    request: Request,
    application_id: str,
    session: Session = Depends(get_db),
    user: User = Depends(require_roles(APPLICATION_MANAGEMENT_ROLES)),
):
    await assert_csrf(request)
    form = await request.form()
    try:
        settings = get_settings()
        application = ApplicationService(
            session,
            create_file_storage(settings),
            settings.max_upload_bytes,
        ).change_status(
            application_id=application_id,
            status=ApplicationStatus(str(form.get("status") or "")),
        )
        AuditService(session).record(
            actor_user_id=user.id,
            action=AuditAction.APPLICATION_STATUS_CHANGED.value,
            entity_type=AuditEntityType.CONTRACT_APPLICATION.value,
            entity_id=application.id,
            details={"status": application.status.value},
        )
        session.commit()
    except (ApplicationError, ValueError):
        session.rollback()
    return RedirectResponse("/admin/applications", status_code=303)


@router.get("/quotes", response_class=HTMLResponse)
def quotes_admin(
    request: Request,
    session: Session = Depends(get_db),
    user: User = Depends(require_roles(APPLICATION_MANAGEMENT_ROLES)),
):
    return templates.TemplateResponse(
        request,
        "admin/quotes.html",
        base_context(
            request,
            title="Business quote requests",
            admin_user=user,
            quotes=ApplicationRepository(session).list_quotes(),
        ),
    )


@router.post("/quotes/{quote_id}/status")
async def change_quote_status(
    request: Request,
    quote_id: str,
    session: Session = Depends(get_db),
    user: User = Depends(require_roles(APPLICATION_MANAGEMENT_ROLES)),
):
    await assert_csrf(request)
    form = await request.form()
    try:
        quote = QuoteService(session).change_status(
            quote_id, QuoteStatus(str(form.get("status") or ""))
        )
        AuditService(session).record(
            actor_user_id=user.id,
            action=AuditAction.QUOTE_STATUS_CHANGED.value,
            entity_type=AuditEntityType.BUSINESS_QUOTE.value,
            entity_id=quote.id,
            details={"status": quote.status.value},
        )
        session.commit()
    except (ApplicationError, ValueError):
        session.rollback()
    return RedirectResponse("/admin/quotes", status_code=303)


@router.get("/orders", response_class=HTMLResponse)
def orders_admin(
    request: Request,
    session: Session = Depends(get_db),
    user: User = Depends(require_roles(ORDER_MANAGEMENT_ROLES)),
):
    return templates.TemplateResponse(
        request,
        "admin/orders.html",
        base_context(
            request,
            title="Orders and payments",
            admin_user=user,
            orders=CommerceRepository(session).list_orders(),
        ),
    )


@router.post("/orders/{order_id}/status")
async def change_order_status(
    request: Request,
    order_id: str,
    session: Session = Depends(get_db),
    user: User = Depends(require_roles(ORDER_MANAGEMENT_ROLES)),
):
    await assert_csrf(request)
    form = await request.form()
    order = CommerceRepository(session).get_order(order_id)
    try:
        if not order:
            raise ValueError("Order not found")
        order.status = OrderStatus(str(form.get("status") or ""))
        NotificationService(session).enqueue_email(
            recipient=order.email,
            template_key=NotificationTemplate.ORDER_STATUS_CHANGED.value,
            payload={"reference": order.reference, "status": order.status.value},
        )
        AuditService(session).record(
            actor_user_id=user.id,
            action=AuditAction.ORDER_STATUS_CHANGED.value,
            entity_type=AuditEntityType.ORDER.value,
            entity_id=order.id,
            details={"status": order.status.value},
        )
        session.commit()
    except ValueError:
        session.rollback()
    return RedirectResponse("/admin/orders", status_code=303)


@router.get("/support", response_class=HTMLResponse)
def support_admin(
    request: Request,
    session: Session = Depends(get_db),
    user: User = Depends(require_roles(APPLICATION_MANAGEMENT_ROLES)),
):
    return templates.TemplateResponse(
        request,
        "admin/support.html",
        base_context(
            request,
            title="Support enquiries",
            admin_user=user,
            tickets=OperationsRepository(session).list_support_tickets(),
        ),
    )
