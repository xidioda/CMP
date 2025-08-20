from __future__ import annotations

import datetime as dt
import json
import hashlib
from typing import Any, Optional

from sqlalchemy import Integer, String, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


# Use SQLAlchemy's generic JSON type which maps to the appropriate backend type
JSONType = JSON  # type: ignore


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
