from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.application.services.auth_service import AuthService
from app.application.services.audit_service import AuditService
from app.core.constants import USER_MANAGEMENT_ROLES
from app.core.dependencies import assert_csrf, require_roles
from app.core.errors import ApplicationError
from app.domain.enums import AuditAction, AuditEntityType, UserRole
from app.infrastructure.db.models import User
from app.infrastructure.db.session import get_db
from app.infrastructure.repositories.identity_repository import IdentityRepository
from app.presentation.rendering import templates
from app.presentation.template_context import base_context


router = APIRouter(prefix="/admin")


@router.get("/users", response_class=HTMLResponse)
def users_admin(
    request: Request,
    session: Session = Depends(get_db),
    user: User = Depends(require_roles(USER_MANAGEMENT_ROLES)),
):
    return templates.TemplateResponse(
        request,
        "admin/users.html",
        base_context(
            request,
            title="Users and permissions",
            admin_user=user,
            users=IdentityRepository(session).list_users(),
            error=None,
        ),
    )


@router.post("/users", response_class=HTMLResponse)
async def create_staff_user(
    request: Request,
    session: Session = Depends(get_db),
    user: User = Depends(require_roles(USER_MANAGEMENT_ROLES)),
):
    await assert_csrf(request)
    form = await request.form()
    try:
        staff = AuthService(session).create_staff_user(
            email=str(form.get("email") or ""),
            password=str(form.get("password") or ""),
            full_name=str(form.get("full_name") or ""),
            phone=str(form.get("phone") or "") or None,
            role=UserRole(str(form.get("role") or "")),
        )
        AuditService(session).record(
            actor_user_id=user.id,
            action=AuditAction.STAFF_CREATED.value,
            entity_type=AuditEntityType.USER.value,
            entity_id=staff.id,
            details={"role": staff.role.value},
        )
        session.commit()
        return RedirectResponse("/admin/users", status_code=303)
    except (ApplicationError, ValueError) as exc:
        session.rollback()
        return templates.TemplateResponse(
            request,
            "admin/users.html",
            base_context(
                request,
                title="Users and permissions",
                admin_user=user,
                users=IdentityRepository(session).list_users(),
                error=str(exc),
            ),
            status_code=400,
        )
