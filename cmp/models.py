from __future__ import annotations

import datetime as dt
import json
import hashlib
from typing import Any, Optional
from enum import Enum as PyEnum

from sqlalchemy import Integer, String, DateTime, JSON, Boolean, Enum, Text, Date
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


# Use SQLAlchemy's generic JSON type which maps to the appropriate backend type
JSONType = JSON  # type: ignore


class UserRole(PyEnum):
    """User roles for access control"""
    ADMIN = "admin"           # Full system access, user management
    ORCHESTRATOR = "orchestrator"  # Agent control, invoice processing, financial operations
    VIEWER = "viewer"         # Read-only access to dashboards and reports


class BusinessActivity(PyEnum):
    """UAE business activities for trade license"""
    TRADING = "trading"
    CONSULTANCY = "consultancy"
    TECHNOLOGY = "technology"
    FINANCIAL_SERVICES = "financial_services"
    REAL_ESTATE = "real_estate"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    HOSPITALITY = "hospitality"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    OTHER = "other"


class DocumentType(PyEnum):
    """Types of business documents"""
    TRADE_LICENSE = "trade_license"
    ESTABLISHMENT_CARD = "establishment_card"
    VAT_CERTIFICATE = "vat_certificate"
    TAX_CERTIFICATE = "tax_certificate"
    MEMORANDUM = "memorandum"
    ARTICLES_OF_ASSOCIATION = "articles_of_association"
    PASSPORT_COPY = "passport_copy"
    VISA_COPY = "visa_copy"
    POWER_OF_ATTORNEY = "power_of_attorney"
    BANK_CERTIFICATE = "bank_certificate"
    OTHER = "other"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.VIEWER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc), nullable=False)
    last_login: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - debug
        return f"<User id={self.id} email={self.email} role={self.role.value}>"

    def has_permission(self, required_role: UserRole) -> bool:
        """Check if user has required permission level"""
        role_hierarchy = {
            UserRole.VIEWER: 1,
            UserRole.ORCHESTRATOR: 2,
            UserRole.ADMIN: 3
        }
        return role_hierarchy[self.role] >= role_hierarchy[required_role]


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Basic Information
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    trade_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    business_type: Mapped[str] = mapped_column(String(100), nullable=False, default="Private Company")
    
    # Contact Information
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Address Information
    address_line1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False, default="Dubai")
    emirate: Mapped[str] = mapped_column(String(100), nullable=False, default="Dubai")
    country: Mapped[str] = mapped_column(String(100), nullable=False, default="United Arab Emirates")
    po_box: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Registration Information
    trade_license_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    trade_license_authority: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    trade_license_issue_date: Mapped[Optional[dt.date]] = mapped_column(Date, nullable=True)
    trade_license_expiry_date: Mapped[Optional[dt.date]] = mapped_column(Date, nullable=True)
    
    # VAT Information
    vat_registered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    vat_registration_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # TRN
    vat_registration_date: Mapped[Optional[dt.date]] = mapped_column(Date, nullable=True)
    vat_effective_date: Mapped[Optional[dt.date]] = mapped_column(Date, nullable=True)
    
    # Corporate Tax Information
    corporate_tax_registered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    corporate_tax_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    corporate_tax_registration_date: Mapped[Optional[dt.date]] = mapped_column(Date, nullable=True)
    
    # Business Activities
    primary_activity: Mapped[Optional[BusinessActivity]] = mapped_column(Enum(BusinessActivity), nullable=True)
    business_activities: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONType, nullable=True)  # List of activities with codes
    
    # Financial Information
    established_date: Mapped[Optional[dt.date]] = mapped_column(Date, nullable=True)
    fiscal_year_end: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, default="31-Dec")  # Format: DD-MMM
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="AED")
    
    # Additional Information
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # System Fields
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc), nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc), onupdate=lambda: dt.datetime.now(dt.timezone.utc), nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Track who made changes

    def __repr__(self) -> str:  # pragma: no cover - debug
        return f"<Company id={self.id} legal_name={self.legal_name} vat_registered={self.vat_registered}>"

    @property
    def display_name(self) -> str:
        """Return the preferred display name (trade name if available, otherwise legal name)"""
        return self.trade_name or self.legal_name

    @property
    def is_vat_liable(self) -> bool:
        """Check if company is approaching or above VAT threshold"""
        # This can be enhanced with actual revenue calculations
        return self.vat_registered

    @property
    def registration_summary(self) -> dict[str, Any]:
        """Get a summary of all registrations"""
        return {
            "trade_license": {
                "number": self.trade_license_number,
                "authority": self.trade_license_authority,
                "expiry": self.trade_license_expiry_date
            },
            "vat": {
                "registered": self.vat_registered,
                "trn": self.vat_registration_number,
                "registration_date": self.vat_registration_date
            },
            "corporate_tax": {
                "registered": self.corporate_tax_registered,
                "number": self.corporate_tax_number,
                "registration_date": self.corporate_tax_registration_date
            }
        }


class BusinessDocument(Base):
    __tablename__ = "business_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, nullable=False, default=1)  # FK to companies table
    
    # Document Information
    document_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # File Information
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    original_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # in bytes
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Document Metadata
    document_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    issue_date: Mapped[Optional[dt.date]] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[Optional[dt.date]] = mapped_column(Date, nullable=True)
    issuing_authority: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Security & Validation
    file_hash: Mapped[str] = mapped_column(String(256), nullable=False)  # SHA-256 hash for integrity
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verification_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # System Fields
    uploaded_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc), nullable=False)
    uploaded_by: Mapped[str] = mapped_column(String(255), nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc), onupdate=lambda: dt.datetime.now(dt.timezone.utc), nullable=False)

    def __repr__(self) -> str:  # pragma: no cover - debug
        return f"<BusinessDocument id={self.id} type={self.document_type.value} title={self.title}>"

    @property
    def is_expired(self) -> bool:
        """Check if document has expired"""
        if not self.expiry_date:
            return False
        return self.expiry_date < dt.date.today()

    @property
    def expires_soon(self) -> bool:
        """Check if document expires within 30 days"""
        if not self.expiry_date:
            return False
        return self.expiry_date <= dt.date.today() + dt.timedelta(days=30)

    @property
    def file_size_mb(self) -> float:
        """Get file size in MB"""
        return round(self.file_size / (1024 * 1024), 2)


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc), nullable=False)
    actor: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "AI:Accountant" or "Human:john@acme.com"
    action: Mapped[str] = mapped_column(String(200), nullable=False)
    data: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONType, nullable=True)

    prev_hash: Mapped[str] = mapped_column(String(128), nullable=False, default="GENESIS")
    hash: Mapped[str] = mapped_column(String(128), nullable=False)

    def __repr__(self) -> str:  # pragma: no cover - debug
        return f"<LedgerEntry id={self.id} actor={self.actor} action={self.action}>"


def canonicalize_payload(payload: Optional[dict[str, Any]]) -> str:
    if payload is None:
        return "null"
    # Stable order
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def compute_ledger_hash(prev_hash: str, timestamp: dt.datetime, actor: str, action: str, payload: Optional[dict[str, Any]]) -> str:
    canonical = canonicalize_payload(payload)
    raw = f"{prev_hash}|{timestamp.isoformat()}|{actor}|{action}|{canonical}".encode()
    return hashlib.sha256(raw).hexdigest()


def append_ledger_entry(session, *, actor: str, action: str, data: Optional[dict[str, Any]] = None) -> LedgerEntry:
    # Get previous hash
    from sqlalchemy import select

    last_hash = "GENESIS"
    last = session.execute(select(LedgerEntry).order_by(LedgerEntry.id.desc()).limit(1)).scalar_one_or_none()
    if last is not None:
        last_hash = last.hash

    now = dt.datetime.now(dt.timezone.utc)
    entry = LedgerEntry(
        timestamp=now,
        actor=actor,
        action=action,
        data=data,
        prev_hash=last_hash,
        hash=compute_ledger_hash(last_hash, now, actor, action, data),
    )
    session.add(entry)
    session.flush()  # assign id
    return entry


# ======================================================================================
# Zoho Books Data Models - Local Storage for API Data Caching
# ======================================================================================

class ZohoCustomer(Base):
    """Local storage for Zoho Books customers to reduce API calls"""
    __tablename__ = "zoho_customers"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    zoho_customer_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    
    # Customer Information
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Address Information
    billing_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    shipping_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Financial Information
    currency_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    opening_balance: Mapped[Optional[float]] = mapped_column(nullable=True)
    credit_limit: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # Status and Metadata
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    created_time: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_modified_time: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Sync Information
    last_synced: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc), nullable=False)
    sync_status: Mapped[str] = mapped_column(String(20), nullable=False, default="synced")  # synced, pending, error


class ZohoProject(Base):
    """Local storage for Zoho Books projects to reduce API calls"""
    __tablename__ = "zoho_projects"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    zoho_project_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    
    # Project Information
    project_name: Mapped[str] = mapped_column(String(255), nullable=False)
    project_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Customer Information
    customer_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    customer_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Financial Information
    budget_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    budget_amount: Mapped[Optional[float]] = mapped_column(nullable=True)
    budget_hours: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # Status and Timeline
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    start_date: Mapped[Optional[dt.date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[dt.date]] = mapped_column(Date, nullable=True)
    
    # Billing Information
    billing_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    rate: Mapped[Optional[float]] = mapped_column(nullable=True)
    currency_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    
    # Metadata
    created_time: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_modified_time: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Sync Information
    last_synced: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc), nullable=False)
    sync_status: Mapped[str] = mapped_column(String(20), nullable=False, default="synced")


class ZohoItem(Base):
    """Local storage for Zoho Books items/services to reduce API calls"""
    __tablename__ = "zoho_items"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    zoho_item_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    
    # Item Information
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Item Type and Category
    item_type: Mapped[str] = mapped_column(String(50), nullable=False, default="sales")  # sales, inventory, service
    product_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    category_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Pricing Information
    rate: Mapped[Optional[float]] = mapped_column(nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    currency_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    
    # Tax Information
    is_taxable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    tax_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tax_percentage: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # Inventory Information (if applicable)
    is_returnable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    available_stock: Mapped[Optional[float]] = mapped_column(nullable=True)
    stock_on_hand: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # Status and Metadata
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    created_time: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_modified_time: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Sync Information
    last_synced: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc), nullable=False)
    sync_status: Mapped[str] = mapped_column(String(20), nullable=False, default="synced")


class ZohoSyncStatus(Base):
    """Track synchronization status and frequency for different Zoho data types"""
    __tablename__ = "zoho_sync_status"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    data_type: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)  # customers, projects, items
    
    # Sync Timing
    last_sync_time: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_successful_sync: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_sync_time: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Sync Results
    sync_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")  # pending, running, success, error
    records_synced: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sync_errors: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Configuration
    sync_interval_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)  # Sync every hour by default
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Metadata
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc), nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc), nullable=False)
