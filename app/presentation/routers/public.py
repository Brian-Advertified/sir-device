from math import ceil
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.application.services.catalog_service import CatalogueFilters, CatalogService
from app.application.services.status_service import StatusService
from app.application.services.support_service import SupportService
from app.core.dependencies import assert_csrf, get_optional_user
from app.core.errors import ApplicationError
from app.domain.enums import DealType, ProductCategory, UseContext
from app.infrastructure.db.models import User
from app.infrastructure.db.session import get_db
from app.infrastructure.repositories.catalog_repository import CatalogRepository
from app.presentation.rendering import templates
from app.presentation.template_context import base_context


router = APIRouter()
CATALOGUE_PAGE_SIZE = 12


def _enum_or_none(enum_type, value: str | None):
    if not value:
        return None
    try:
        return enum_type(value)
    except ValueError:
        return None


def _page_numbers(current: int, total: int) -> list[int]:
    return sorted({1, total, current - 1, current, current + 1})


@router.get("/", response_class=HTMLResponse)
def home(request: Request, session: Session = Depends(get_db)):
    service = CatalogService(session)
    banners = CatalogRepository(session).list_banners(public_only=True)
    return templates.TemplateResponse(
        request,
        "home.html",
        base_context(
            request,
            title="Devices, plans and internet",
            featured_deals=service.featured_deals(use_context=UseContext.PERSONAL),
            banners=banners,
        ),
    )


def _catalogue_response(
    request: Request,
    session: Session,
    *,
    title: str,
    intro: str,
    fixed_category: ProductCategory | None = None,
    fixed_categories: tuple[ProductCategory, ...] = (),
    fixed_deal_type: DealType | None = None,
    fixed_deal_types: tuple[DealType, ...] = (),
    fixed_use_context: UseContext | None = None,
    featured_only: bool = False,
):
    params = request.query_params
    category = fixed_category or _enum_or_none(ProductCategory, params.get("category"))
    deal_type = fixed_deal_type or _enum_or_none(DealType, params.get("deal_type"))
    try:
        page = max(1, int(params.get("page", "1")))
    except ValueError:
        page = 1
    filters = CatalogueFilters(
        category=category,
        categories=() if category else fixed_categories,
        deal_type=deal_type,
        deal_types=() if deal_type else fixed_deal_types,
        network_code=params.get("network") or None,
        brand=params.get("brand") or None,
        use_context=fixed_use_context or _enum_or_none(UseContext, params.get("use_context")),
        min_monthly=params.get("min_monthly") or None,
        max_monthly=params.get("max_monthly") or None,
        contract_term=params.get("contract_term") or None,
        sort=params.get("sort") or "popular",
        search=params.get("q") or None,
        featured_only=featured_only,
    )
    service = CatalogService(session)
    total_count = service.count(filters)
    page_count = max(1, ceil(total_count / CATALOGUE_PAGE_SIZE))
    page = min(page, page_count)
    query = urlencode([(key, value) for key, value in params.multi_items() if key != "page"])
    return templates.TemplateResponse(
        request,
        "catalogue.html",
        base_context(
            request,
            title=title,
            intro=intro,
            deals=service.search(filters, limit=CATALOGUE_PAGE_SIZE, offset=(page - 1) * CATALOGUE_PAGE_SIZE),
            options=service.filter_options(use_context=filters.use_context),
            selected=filters,
            pagination={"page": page, "page_count": page_count, "pages": _page_numbers(page, page_count), "total_count": total_count, "query": query},
        ),
    )


@router.get("/devices", response_class=HTMLResponse)
def devices(request: Request, session: Session = Depends(get_db)):
    return _catalogue_response(
        request,
        session,
        title="Devices",
        intro="Browse verified smartphones, tablets, laptops and accessories.",
        fixed_use_context=UseContext.PERSONAL,
        fixed_categories=(
            ProductCategory.SMARTPHONE,
            ProductCategory.TABLET,
            ProductCategory.LAPTOP,
            ProductCategory.ACCESSORY,
        ),
    )


@router.get("/mobile-plans", response_class=HTMLResponse)
def mobile_plans(request: Request, session: Session = Depends(get_db)):
    return _catalogue_response(
        request,
        session,
        title="Mobile plans",
        intro="Compare device contracts and SIM-only offers against your requirements.",
        fixed_use_context=UseContext.PERSONAL,
        fixed_deal_types=(DealType.DEVICE_CONTRACT, DealType.SIM_ONLY),
    )


@router.get("/internet", response_class=HTMLResponse)
def internet(request: Request, session: Session = Depends(get_db)):
    return _catalogue_response(
        request,
        session,
        title="Internet",
        intro="Explore LTE, 5G and fibre internet for personal use.",
        fixed_deal_type=DealType.INTERNET,
        fixed_use_context=UseContext.PERSONAL,
    )


@router.get("/promotions", response_class=HTMLResponse)
def promotions(request: Request, session: Session = Depends(get_db)):
    return _catalogue_response(
        request,
        session,
        title="Current promotions",
        intro="Only published, unexpired promotions are shown.",
        fixed_use_context=UseContext.PERSONAL,
        featured_only=True,
    )


@router.get("/business-solutions", response_class=HTMLResponse)
def business_solutions(request: Request):
    return templates.TemplateResponse(
        request,
        "business.html",
        base_context(request, title="Business solutions"),
    )


@router.get("/business-deals", response_class=HTMLResponse)
def business_deals(request: Request, session: Session = Depends(get_db)):
    return _catalogue_response(
        request,
        session,
        title="MTN business deals",
        intro="Compare business mobile contracts, staff devices and connectivity from the MTN EBU catalogue.",
        fixed_use_context=UseContext.BUSINESS,
    )


@router.get("/deals/{deal_id}", response_class=HTMLResponse)
def deal_details(request: Request, deal_id: str, session: Session = Depends(get_db)):
    service = CatalogService(session)
    deal = service.get_public_deal(deal_id)
    if not deal:
        return templates.TemplateResponse(
            request,
            "not_found.html",
            base_context(request, title="Deal unavailable"),
            status_code=404,
        )
    return templates.TemplateResponse(
        request,
        "product.html",
        base_context(
            request,
            title=deal.product.name,
            deal=deal,
            offer_groups=service.grouped_offers(deal),
        ),
    )


@router.get("/compare", response_class=HTMLResponse)
def compare(
    request: Request,
    ids: str = Query(default=""),
    session: Session = Depends(get_db),
):
    deal_ids = [item for item in ids.split(",") if item][:3]
    service = CatalogService(session)
    deals = service.compare(deal_ids)
    candidates = [] if deals else service.search(
        CatalogueFilters(
            deal_types=(DealType.DEVICE_CONTRACT, DealType.SIM_ONLY),
            use_context=UseContext.PERSONAL,
            sort="price_asc",
        ),
        limit=12,
    )
    return templates.TemplateResponse(
        request,
        "compare.html",
        base_context(request, title="Compare packages", deals=deals, candidates=candidates),
    )


@router.get("/support", response_class=HTMLResponse)
def support_page(request: Request):
    return templates.TemplateResponse(
        request,
        "support.html",
        base_context(request, title="Contact and support", submitted=False),
    )


@router.post("/support", response_class=HTMLResponse)
async def submit_support(
    request: Request,
    session: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    await assert_csrf(request)
    form = await request.form()
    try:
        ticket = SupportService(session).create_ticket(
            user_id=user.id if user else None,
            name=str(form.get("name") or ""),
            email=str(form.get("email") or ""),
            phone=str(form.get("phone") or "") or None,
            subject=str(form.get("subject") or ""),
            message=str(form.get("message") or ""),
        )
        session.commit()
        return templates.TemplateResponse(
            request,
            "support.html",
            base_context(
                request,
                title="Contact and support",
                submitted=True,
                reference=ticket.reference,
            ),
        )
    except ApplicationError as exc:
        session.rollback()
        return templates.TemplateResponse(
            request,
            "support.html",
            base_context(request, title="Contact and support", submitted=False, error=str(exc)),
            status_code=400,
        )


@router.get("/application-status", response_class=HTMLResponse)
def application_status_page(request: Request):
    return templates.TemplateResponse(
        request,
        "status.html",
        base_context(request, title="Track your request", record=None, searched=False),
    )


@router.post("/application-status", response_class=HTMLResponse)
async def application_status_lookup(request: Request, session: Session = Depends(get_db)):
    await assert_csrf(request)
    form = await request.form()
    record = StatusService(session).find(
        reference=str(form.get("reference") or ""),
        email=str(form.get("email") or ""),
    )
    return templates.TemplateResponse(
        request,
        "status.html",
        base_context(
            request,
            title="Track your request",
            record=record,
            searched=True,
        ),
    )
