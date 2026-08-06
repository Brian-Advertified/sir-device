from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings, validate_settings
from app.core.errors import ApplicationError
from app.infrastructure.db.session import SessionLocal, create_schema
from app.infrastructure.repositories.catalog_repository import CatalogRepository
from app.presentation.rendering import templates
from app.presentation.routers import (
    admin_catalog,
    admin_dashboard,
    admin_users,
    admin_workflows,
    api,
    applications,
    auth,
    commerce,
    customer,
    public,
)
from app.presentation.template_context import base_context


settings = get_settings()
validate_settings(settings)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.auto_create_schema:
        create_schema()
    with SessionLocal() as session:
        CatalogRepository(session).expire_past_deals()
        session.commit()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs" if not settings.is_production else None,
    redoc_url=None,
)

static_directory = Path(__file__).parent / "presentation" / "static"
app.mount("/static", StaticFiles(directory=str(static_directory)), name="static")

app.include_router(public.router)
app.include_router(auth.router)
app.include_router(commerce.router)
app.include_router(applications.router)
app.include_router(customer.router)
app.include_router(api.router)
app.include_router(admin_dashboard.router)
app.include_router(admin_catalog.router)
app.include_router(admin_workflows.router)
app.include_router(admin_users.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(ApplicationError)
async def application_error_handler(request: Request, exc: ApplicationError):
    if request.url.path.startswith("/api/"):
        return JSONResponse({"error": str(exc)}, status_code=400)
    return templates.TemplateResponse(
        request,
        "error.html",
        base_context(request, title="Something needs attention", error=str(exc)),
        status_code=400,
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, _):
    return templates.TemplateResponse(
        request,
        "not_found.html",
        base_context(request, title="Page not found"),
        status_code=404,
    )
