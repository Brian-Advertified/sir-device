from fastapi import Request

from app.core.config import get_settings
from app.core.dependencies import get_principal
from app.core.money import format_money
from app.domain.enums import (
    ApplicationIntent,
    ApplicationStatus,
    CustomerType,
    DealType,
    DocumentType,
    OrderStatus,
    ProductCategory,
    QuoteStatus,
    StockStatus,
    UseContext,
    UserRole,
)
from app.presentation.content import (
    APPLICATION_REVIEW_NOTICE,
    DEMONSTRATION_NOTICE,
    DOCUMENT_LABELS,
    LABELS,
    NETWORK_APPROVAL_NOTICE,
    PRIMARY_NAVIGATION,
    ROLE_LABELS,
    SHOP_BY_NEED,
    STATUS_LABELS,
    TRUST_ITEMS,
)


def base_context(request: Request, **values) -> dict:
    settings = get_settings()
    principal = get_principal(request, settings)
    context = {
        "request": request,
        "app_name": settings.app_name,
        "principal": principal,
        "support_email": settings.support_email,
        "support_phone": settings.support_phone,
        "whatsapp_number": settings.whatsapp_number,
        "csrf_token": principal.csrf_token if principal else "",
        "navigation": PRIMARY_NAVIGATION,
        "shop_by_need": SHOP_BY_NEED,
        "trust_items": TRUST_ITEMS,
        "labels": LABELS,
        "status_labels": STATUS_LABELS,
        "document_labels": DOCUMENT_LABELS,
        "role_labels": ROLE_LABELS,
        "format_money": format_money,
        "demo_notice": DEMONSTRATION_NOTICE,
        "network_notice": NETWORK_APPROVAL_NOTICE,
        "application_notice": APPLICATION_REVIEW_NOTICE,
        "ProductCategory": ProductCategory,
        "DealType": DealType,
        "StockStatus": StockStatus,
        "UseContext": UseContext,
        "CustomerType": CustomerType,
        "ApplicationIntent": ApplicationIntent,
        "ApplicationStatus": ApplicationStatus,
        "OrderStatus": OrderStatus,
        "QuoteStatus": QuoteStatus,
        "DocumentType": DocumentType,
        "UserRole": UserRole,
    }
    context.update(values)
    return context
