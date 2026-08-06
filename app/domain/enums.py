from enum import StrEnum


class UserRole(StrEnum):
    ADMINISTRATOR = "administrator"
    SALES_AGENT = "sales_agent"
    APPLICATION_PROCESSOR = "application_processor"
    PRODUCT_MANAGER = "product_manager"
    CUSTOMER_SUPPORT = "customer_support"
    FINANCE_USER = "finance_user"
    CUSTOMER = "customer"


class ProductCategory(StrEnum):
    SMARTPHONE = "smartphone"
    TABLET = "tablet"
    LAPTOP = "laptop"
    ROUTER = "router"
    MOBILE_PLAN = "mobile_plan"
    SIM_ONLY = "sim_only"
    FIBRE = "fibre"
    LTE = "lte"
    FIVE_G = "5g"
    ACCESSORY = "accessory"


class UseContext(StrEnum):
    PERSONAL = "personal"
    BUSINESS = "business"
    BOTH = "both"


class DealType(StrEnum):
    CASH_PURCHASE = "cash_purchase"
    DEVICE_CONTRACT = "device_contract"
    SIM_ONLY = "sim_only"
    INTERNET = "internet"
    ACCESSORY = "accessory"
    DEPOSIT = "deposit"


class StockStatus(StrEnum):
    IN_STOCK = "in_stock"
    LIMITED = "limited"
    PREORDER = "preorder"
    OUT_OF_STOCK = "out_of_stock"
    SUBJECT_TO_CONFIRMATION = "subject_to_confirmation"


class CartStatus(StrEnum):
    ACTIVE = "active"
    CONVERTED = "converted"
    ABANDONED = "abandoned"


class OrderStatus(StrEnum):
    DRAFT = "draft"
    AWAITING_PAYMENT = "awaiting_payment"
    PROCESSING = "processing"
    DISPATCHED = "dispatched"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class ApplicationStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    DOCUMENTS_REQUIRED = "documents_required"
    UNDER_REVIEW = "under_review"
    SUBMITTED_TO_NETWORK = "submitted_to_network"
    APPROVED = "approved"
    DECLINED = "declined"
    AWAITING_PAYMENT = "awaiting_payment"
    PROCESSING = "processing"
    DISPATCHED = "dispatched"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CustomerType(StrEnum):
    PERSONAL = "personal"
    BUSINESS = "business"


class ApplicationIntent(StrEnum):
    NEW_CONTRACT = "new_contract"
    UPGRADE = "upgrade"
    NUMBER_PORT = "number_port"


class DocumentType(StrEnum):
    IDENTITY = "identity"
    PROOF_OF_ADDRESS = "proof_of_address"
    PROOF_OF_INCOME = "proof_of_income"
    BANK_STATEMENT = "bank_statement"
    COMPANY_REGISTRATION = "company_registration"
    DIRECTOR_IDENTIFICATION = "director_identification"
    PURCHASE_ORDER = "purchase_order"
    OTHER = "other"


class DocumentStatus(StrEnum):
    RECEIVED = "received"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class QuoteStatus(StrEnum):
    SUBMITTED = "submitted"
    IN_PROGRESS = "in_progress"
    QUOTED = "quoted"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class NotificationStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class NotificationChannel(StrEnum):
    EMAIL = "email"
    SMS = "sms"


class SupportStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


class StorageBackend(StrEnum):
    LOCAL = "local"
    S3 = "s3"


class PaymentProvider(StrEnum):
    PAYFAST = "payfast"


class NotificationTemplate(StrEnum):
    ORDER_CREATED = "order_created"
    APPLICATION_SUBMITTED = "application_submitted"
    APPLICATION_STATUS_CHANGED = "application_status_changed"
    BUSINESS_QUOTE_SUBMITTED = "business_quote_submitted"
    BUSINESS_QUOTE_STATUS_CHANGED = "business_quote_status_changed"
    ORDER_STATUS_CHANGED = "order_status_changed"
    SALES_QUOTE_RECEIVED = "sales_quote_received"


class AuditAction(StrEnum):
    NETWORK_SAVED = "catalogue.network.saved"
    PRODUCT_SAVED = "catalogue.product.saved"
    DEAL_SAVED = "catalogue.deal.saved"
    BANNER_SAVED = "catalogue.banner.saved"
    DEALS_IMPORTED = "catalogue.deals.imported"
    APPLICATION_STATUS_CHANGED = "application.status.changed"
    QUOTE_STATUS_CHANGED = "quote.status.changed"
    ORDER_STATUS_CHANGED = "order.status.changed"
    STAFF_CREATED = "identity.staff.created"


class AuditEntityType(StrEnum):
    NETWORK = "network"
    PRODUCT = "product"
    DEAL = "deal"
    PROMOTION_BANNER = "promotion_banner"
    DEAL_IMPORT = "deal_import"
    CONTRACT_APPLICATION = "contract_application"
    BUSINESS_QUOTE = "business_quote"
    ORDER = "order"
    USER = "user"
