from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.constants import ADMIN_ROLES
from app.core.dependencies import require_roles
from app.infrastructure.db.models import User
from app.infrastructure.db.session import get_db
from app.infrastructure.repositories.application_repository import ApplicationRepository
from app.infrastructure.repositories.commerce_repository import CommerceRepository
from app.infrastructure.repositories.operations_repository import OperationsRepository
from app.presentation.rendering import templates
from app.presentation.template_context import base_context


router = APIRouter(prefix="/admin")


@router.get("", response_class=HTMLResponse)
def dashboard(
    request: Request,
    session: Session = Depends(get_db),
    user: User = Depends(require_roles(ADMIN_ROLES)),
):
    return templates.TemplateResponse(
        request,
        "admin/dashboard.html",
        base_context(
            request,
            title="Administration dashboard",
            admin_user=user,
            counts=OperationsRepository(session).dashboard_counts(),
            applications=ApplicationRepository(session).list_applications(limit=8),
            orders=CommerceRepository(session).list_orders(limit=8),
        ),
    )
