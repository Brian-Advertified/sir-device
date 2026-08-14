from dataclasses import dataclass

from app.domain.enums import (
    ApplicationStatus,
    DealType,
    DocumentType,
    OrderStatus,
    ProductCategory,
    QuoteStatus,
    StockStatus,
    UseContext,
    UserRole,
)


@dataclass(frozen=True)
class NavigationItem:
    label: str
    href: str


PRIMARY_NAVIGATION = (
    NavigationItem("Mobile Plans", "/mobile-plans"),
    NavigationItem("Internet", "/internet"),
    NavigationItem("Promotions", "/promotions"),
    NavigationItem("Business", "/business-deals"),
    NavigationItem("Support", "/support"),
)

SHOP_BY_NEED = (
    ("Get a new phone plan", "/mobile-plans", "phone"),
    ("Upgrade my device", "/contract-application?intent=upgrade", "upgrade"),
    ("SIM-only plans", "/mobile-plans?deal_type=sim_only", "sim"),
    ("Get business internet", "/business-deals?deal_type=internet", "wifi"),
    ("Connect my team", "/business-quote", "team"),
    ("Get LTE or 5G internet", "/internet", "wifi"),
    ("View promotions", "/promotions", "promotion"),
)

TRUST_ITEMS = (
    ("Independent marketplace", "Sir Device remains your primary point of contact."),
    ("Verified deal controls", "Published deals carry verification and expiry dates."),
    ("Secure applications", "Documents are stored privately and access is controlled."),
    ("Business focused", "Quotes support teams, branches and bulk device needs."),
)

DEMONSTRATION_NOTICE = "T&Cs apply. E&OE."
NETWORK_APPROVAL_NOTICE = "Pricing and availability are subject to confirmation and network approval."
APPLICATION_REVIEW_NOTICE = (
    "Your application will be reviewed and submitted for the required network and credit checks."
)

LABELS = {
    ProductCategory.SMARTPHONE: "Smartphones",
    ProductCategory.TABLET: "Tablets",
    ProductCategory.LAPTOP: "Laptops",
    ProductCategory.ROUTER: "Internet",
    ProductCategory.MOBILE_PLAN: "Mobile plans",
    ProductCategory.SIM_ONLY: "SIM-only plans",
    ProductCategory.FIBRE: "Fibre",
    ProductCategory.LTE: "LTE internet",
    ProductCategory.FIVE_G: "5G internet",
    ProductCategory.ACCESSORY: "Accessories",
    DealType.CASH_PURCHASE: "Cash purchase",
    DealType.DEVICE_CONTRACT: "Device contract",
    DealType.SIM_ONLY: "SIM-only",
    DealType.INTERNET: "Internet",
    DealType.ACCESSORY: "Accessory",
    DealType.DEPOSIT: "Deposit",
    UseContext.PERSONAL: "Personal",
    UseContext.BUSINESS: "Business",
    UseContext.BOTH: "Personal and business",
    StockStatus.IN_STOCK: "In stock",
    StockStatus.LIMITED: "Limited stock",
    StockStatus.PREORDER: "Pre-order",
    StockStatus.OUT_OF_STOCK: "Out of stock",
    StockStatus.SUBJECT_TO_CONFIRMATION: "Subject to confirmation",
}

STATUS_LABELS = {
    **{status: status.value.replace("_", " ").title() for status in ApplicationStatus},
    **{status: status.value.replace("_", " ").title() for status in OrderStatus},
    **{status: status.value.replace("_", " ").title() for status in QuoteStatus},
}

DOCUMENT_LABELS = {
    item: item.value.replace("_", " ").title() for item in DocumentType
}

ROLE_LABELS = {item: item.value.replace("_", " ").title() for item in UserRole}
