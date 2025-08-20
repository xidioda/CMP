from __future__ import annotations

from cmp.db import init_db, SessionLocal
from cmp.models import append_ledger_entry, LedgerEntry


def setup_module(module):
    init_db()


def test_ledger_hash_chain():
    s = SessionLocal()
    try:
        e1 = append_ledger_entry(s, actor="AI:Accountant", action="t1", data={"v": 1})
        e2 = append_ledger_entry(s, actor="AI:Accountant", action="t2", data={"v": 2})
        s.commit()

        # Ensure chaining
        assert e2.prev_hash == e1.hash

        # Recompute and verify
        from cmp.models import compute_ledger_hash
        expected = compute_ledger_hash(e1.hash, e2.timestamp, e2.actor, e2.action, e2.data)
        assert e2.hash == expected

    finally:
        s.close()
