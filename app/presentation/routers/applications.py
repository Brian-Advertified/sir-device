from fastapi import APIRouter, Depends, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.application.services.application_service import ApplicationService
from app.application.services.quote_service import QuoteService
from app.core.config import Settings, get_settings
from app.core.dependencies import assert_csrf, get_optional_user
from app.core.errors import ApplicationError
from app.domain.enums import CustomerType, DocumentType
from app.infrastructure.db.models import User
from app.infrastructure.db.session import get_db
from app.infrastructure.repositories.application_repository import ApplicationRepository
from app.infrastructure.storage.factory import create_file_storage
from app.presentation.rendering import templates
from app.presentation.template_context import base_context


router = APIRouter()


@router.get("/contract-application", response_class=HTMLResponse)
def application_page(request: Request, deal_id: str | None = None, intent: str | None = None):
    return templates.TemplateResponse(
        request,
        "application.html",
        base_context(
            request,
            title="Contract application",
            deal_id=deal_id,
            intent=intent,
            error=None,
        ),
    )


@router.post("/contract-application", response_class=HTMLResponse)
async def submit_application(
    request: Request,
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User | None = Depends(get_optional_user),
):
    await assert_csrf(request, settings)
    form = await request.form()
    try:
        customer_type = CustomerType(str(form.get("customer_type") or ""))
        excluded = {"csrf_token", "customer_type", "email", "phone", "selected_deal_id"}
        details = {str(key): str(value) for key, value in form.items() if key not in excluded}
        service = ApplicationService(
            session,
            create_file_storage(settings),
            settings.max_upload_bytes,
        )
        application = service.create(
            user_id=user.id if user else None,
            selected_deal_id=str(form.get("selected_deal_id") or "") or None,
            customer_type=customer_type,
            email=str(form.get("email") or ""),
            phone=str(form.get("phone") or ""),
            details=details,
        )
        session.commit()
        return RedirectResponse(f"/upload-documents/{application.reference}", status_code=303)
    except (ApplicationError, ValueError) as exc:
        session.rollback()
        return templates.TemplateResponse(
            request,
            "application.html",
            base_context(
                request,
                title="Contract application",
                deal_id=str(form.get("selected_deal_id") or "") or None,
                intent=str(form.get("intent") or "") or None,
                error=str(exc),
            ),
            status_code=400,
        )


@router.get("/upload-documents/{reference}", response_class=HTMLResponse)
def upload_page(request: Request, reference: str, session: Session = Depends(get_db)):
    application = ApplicationRepository(session).get_application_by_reference(reference)
    if not application:
        return templates.TemplateResponse(
            request,
            "not_found.html",
            base_context(request, title="Application not found"),
            status_code=404,
        )
    return templates.TemplateResponse(
        request,
        "upload.html",
        base_context(request, title="Upload documents", application=application, error=None),
    )


@router.post("/upload-documents/{reference}", response_class=HTMLResponse)
async def upload_document(
    request: Request,
    reference: str,
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    await assert_csrf(request, settings)
    form = await request.form()
    file_value = form.get("file")
    try:
        if not hasattr(file_value, "file"):
            raise ValueError("Select a file to upload")
        document_type = DocumentType(str(form.get("document_type") or ""))
        ApplicationService(
            session,
            create_file_storage(settings),
            settings.max_upload_bytes,
        ).upload_document(
            reference=reference,
            document_type=document_type,
            source=file_value.file,
            original_name=file_value.filename or "upload",
            content_type=file_value.content_type or "application/octet-stream",
        )
        session.commit()
        return RedirectResponse(f"/upload-documents/{reference}", status_code=303)
    except (ApplicationError, ValueError) as exc:
        session.rollback()
        application = ApplicationRepository(session).get_application_by_reference(reference)
        return templates.TemplateResponse(
            request,
            "upload.html",
            base_context(
                request,
                title="Upload documents",
                application=application,
                error=str(exc),
            ),
            status_code=400,
        )


@router.get("/business-quote", response_class=HTMLResponse)
def quote_page(request: Request):
    return templates.TemplateResponse(
        request,
        "quote.html",
        base_context(request, title="Get a business quote", quote=None, error=None),
    )


@router.post("/business-quote", response_class=HTMLResponse)
async def submit_quote(
    request: Request,
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User | None = Depends(get_optional_user),
):
    await assert_csrf(request, settings)
    form = await request.form()
    excluded = {"csrf_token", "company_name", "contact_name", "email", "phone"}
    details = {str(key): str(value) for key, value in form.items() if key not in excluded}
    try:
        quote = QuoteService(session, settings.sales_team_email).create(
            user_id=user.id if user else None,
            company_name=str(form.get("company_name") or ""),
            contact_name=str(form.get("contact_name") or ""),
            email=str(form.get("email") or ""),
            phone=str(form.get("phone") or ""),
            details=details,
        )
        session.commit()
        return templates.TemplateResponse(
            request,
            "quote.html",
            base_context(request, title="Get a business quote", quote=quote, error=None),
        )
    except ApplicationError as exc:
        session.rollback()
        return templates.TemplateResponse(
            request,
            "quote.html",
            base_context(request, title="Get a business quote", quote=None, error=str(exc)),
            status_code=400,
        )
