from fastapi import APIRouter, Depends, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.application.services.admin_service import AdminService
from app.application.services.audit_service import AuditService
from app.application.services.import_service import CsvDealImporter
from app.core.constants import CATALOGUE_MANAGEMENT_ROLES
from app.core.dependencies import assert_csrf, require_roles
from app.core.errors import ApplicationError
from app.domain.enums import AuditAction, AuditEntityType
from app.infrastructure.db.models import User
from app.infrastructure.db.session import get_db
from app.infrastructure.repositories.catalog_repository import CatalogRepository
from app.presentation.rendering import templates
from app.presentation.template_context import base_context


router = APIRouter(prefix="/admin")


def _catalog_context(request: Request, session: Session, **values) -> dict:
    repository = CatalogRepository(session)
    return base_context(
        request,
        networks=repository.list_networks(active_only=False),
        products=repository.list_admin_products(),
        deals=repository.list_admin_deals(),
        banners=repository.list_banners(),
        **values,
    )


@router.get("/catalog", response_class=HTMLResponse)
def catalog_admin(
    request: Request,
    session: Session = Depends(get_db),
    user: User = Depends(require_roles(CATALOGUE_MANAGEMENT_ROLES)),
):
    return templates.TemplateResponse(
        request,
        "admin/catalog.html",
        _catalog_context(request, session, title="Catalogue management", admin_user=user),
    )


@router.post("/networks")
async def save_network(
    request: Request,
    session: Session = Depends(get_db),
    user: User = Depends(require_roles(CATALOGUE_MANAGEMENT_ROLES)),
):
    await assert_csrf(request)
    form = await request.form()
    try:
        entity = AdminService(session).save_network(
            {str(key): str(value) for key, value in form.items()},
            str(form.get("id") or "") or None,
        )
        AuditService(session).record(
            actor_user_id=user.id,
            action=AuditAction.NETWORK_SAVED.value,
            entity_type=AuditEntityType.NETWORK.value,
            entity_id=entity.id,
        )
        session.commit()
        return RedirectResponse("/admin/catalog#networks", status_code=303)
    except (ApplicationError, ValueError) as exc:
        session.rollback()
        return templates.TemplateResponse(
            request,
            "admin/catalog.html",
            _catalog_context(
                request,
                session,
                title="Catalogue management",
                admin_user=user,
                error=str(exc),
            ),
            status_code=400,
        )


@router.post("/products")
async def save_product(
    request: Request,
    session: Session = Depends(get_db),
    user: User = Depends(require_roles(CATALOGUE_MANAGEMENT_ROLES)),
):
    await assert_csrf(request)
    form = await request.form()
    try:
        entity = AdminService(session).save_product(
            {str(key): str(value) for key, value in form.items()},
            str(form.get("id") or "") or None,
        )
        AuditService(session).record(
            actor_user_id=user.id,
            action=AuditAction.PRODUCT_SAVED.value,
            entity_type=AuditEntityType.PRODUCT.value,
            entity_id=entity.id,
        )
        session.commit()
        return RedirectResponse("/admin/catalog#products", status_code=303)
    except (ApplicationError, ValueError) as exc:
        session.rollback()
        return templates.TemplateResponse(
            request,
            "admin/catalog.html",
            _catalog_context(
                request,
                session,
                title="Catalogue management",
                admin_user=user,
                error=str(exc),
            ),
            status_code=400,
        )


@router.post("/deals")
async def save_deal(
    request: Request,
    session: Session = Depends(get_db),
    user: User = Depends(require_roles(CATALOGUE_MANAGEMENT_ROLES)),
):
    await assert_csrf(request)
    form = await request.form()
    try:
        entity = AdminService(session).save_deal(
            {str(key): str(value) for key, value in form.items()},
            str(form.get("id") or "") or None,
        )
        AuditService(session).record(
            actor_user_id=user.id,
            action=AuditAction.DEAL_SAVED.value,
            entity_type=AuditEntityType.DEAL.value,
            entity_id=entity.id,
        )
        session.commit()
        return RedirectResponse("/admin/catalog#deals", status_code=303)
    except (ApplicationError, ValueError, KeyError) as exc:
        session.rollback()
        return templates.TemplateResponse(
            request,
            "admin/catalog.html",
            _catalog_context(
                request,
                session,
                title="Catalogue management",
                admin_user=user,
                error=str(exc),
            ),
            status_code=400,
        )


@router.post("/banners")
async def save_banner(
    request: Request,
    session: Session = Depends(get_db),
    user: User = Depends(require_roles(CATALOGUE_MANAGEMENT_ROLES)),
):
    await assert_csrf(request)
    form = await request.form()
    try:
        entity = AdminService(session).save_banner(
            {str(key): str(value) for key, value in form.items()},
            str(form.get("id") or "") or None,
        )
        AuditService(session).record(
            actor_user_id=user.id,
            action=AuditAction.BANNER_SAVED.value,
            entity_type=AuditEntityType.PROMOTION_BANNER.value,
            entity_id=entity.id,
        )
        session.commit()
        return RedirectResponse("/admin/catalog#banners", status_code=303)
    except (ApplicationError, ValueError) as exc:
        session.rollback()
        return templates.TemplateResponse(
            request,
            "admin/catalog.html",
            _catalog_context(
                request,
                session,
                title="Catalogue management",
                admin_user=user,
                error=str(exc),
            ),
            status_code=400,
        )


@router.post("/imports/deals", response_class=HTMLResponse)
async def import_deals(
    request: Request,
    session: Session = Depends(get_db),
    user: User = Depends(require_roles(CATALOGUE_MANAGEMENT_ROLES)),
):
    await assert_csrf(request)
    form = await request.form()
    upload = form.get("file")
    try:
        if not hasattr(upload, "read"):
            raise ValueError("Choose a CSV file")
        contents = await upload.read()
        importer = CsvDealImporter(session)
        filename = str(getattr(upload, "filename", "") or "").lower()
        if filename.endswith(".xlsx"):
            result = importer.import_xlsx_bytes(contents)
        else:
            result = importer.import_text(contents.decode("utf-8-sig"))
        if result.issues:
            session.rollback()
        else:
            AuditService(session).record(
                actor_user_id=user.id,
                action=AuditAction.DEALS_IMPORTED.value,
                entity_type=AuditEntityType.DEAL_IMPORT.value,
                entity_id=None,
                details={"rows": result.rows_processed},
            )
            session.commit()
        return templates.TemplateResponse(
            request,
            "admin/import_result.html",
            base_context(
                request,
                title="Deal import result",
                admin_user=user,
                result=result,
            ),
            status_code=400 if result.issues else 200,
        )
    except (ApplicationError, UnicodeDecodeError, ValueError) as exc:
        session.rollback()
        return templates.TemplateResponse(
            request,
            "admin/import_result.html",
            base_context(
                request,
                title="Deal import result",
                admin_user=user,
                result=None,
                error=str(exc),
            ),
            status_code=400,
        )
