from __future__ import annotations

from dataclasses import dataclass
from typing import Any

@dataclass
class AccountantConfig:
    enable_ocr: bool = True


class AccountantAgent:
    """AI Accountant: bookkeeping, OCR, e-invoices (stub).

    Methods return dicts for now; later wire to Zoho, Wio, and OCR.
    """

    def __init__(self, config: AccountantConfig | None = None) -> None:
        self.config = config or AccountantConfig()

    async def fetch_bank_transactions(self) -> list[dict[str, Any]]:
        # TODO: integrate Wio Bank connector
        return []

    async def categorize_transactions(self, transactions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        # TODO: integrate Zoho Books API
        return transactions

    async def ocr_invoice(self, image_path: str) -> dict[str, Any]:
        # TODO: integrate pytesseract
        return {"text": None, "path": image_path}

    async def generate_einvoice(self, invoice_data: dict[str, Any]) -> dict[str, Any]:
        # TODO: UAE e-invoice mapping
        return {"einvoice": invoice_data}
