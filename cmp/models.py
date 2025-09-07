from __future__ import annotations

import datetime as dt
import json
import hashlib
from typing import Any, Optional
from enum import Enum as PyEnum

from sqlalchemy import Integer, String, DateTime, JSON, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


# Use SQLAlchemy's generic JSON type which maps to the appropriate backend type
JSONType = JSON  # type: ignore


class UserRole(PyEnum):
    """User roles for access control"""
    ADMIN = "admin"           # Full system access, user management
    ORCHESTRATOR = "orchestrator"  # Agent control, invoice processing, financial operations
    VIEWER = "viewer"         # Read-only access to dashboards and reports


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
