from __future__ import annotations

from dataclasses import dataclass
from typing import Any

@dataclass
class UAEInvoice:
    supplier_name: str
    supplier_trn: str
    customer_name: str
    customer_trn: str | None
    items: list[dict[str, Any]]  # [{ description, qty, unit_price, vat_rate }]
    currency: str = "AED"


def generate_uae_einvoice(data: dict[str, Any]) -> dict[str, Any]:
    """Stub UAE e-invoice generator. Returns a normalized dictionary structure.

    TODO: implement full FTA compliance and XML/UBL export.
    """
    return {
        "supplier": {
            "name": data.get("supplier_name"),
            "trn": data.get("supplier_trn"),
        },
        "customer": {
            "name": data.get("customer_name"),
            "trn": data.get("customer_trn"),
        },
        "items": data.get("items", []),
        "currency": data.get("currency", "AED"),
        "meta": {
            "format": "uae-einvoice-stub",
            "version": "0.1",
        },
    }
