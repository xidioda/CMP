"""
AI Accountant Agent

Responsibilities:
- Fetch transactions from Wio Bank
- Categorize transactions in Zoho Books  
- OCR uploaded invoices and create bills
- Generate e-invoices
- Perform daily bank reconciliations
- Prepare draft VAT returns
"""

from typing import Dict, Any, List
from pathlib import Path

from ..logging_config import get_logger
from ..utils.ocr import ocr_processor
from ..integrations.invoices import zoho_books, generate_uae_einvoice

logger = get_logger("agents.accountant")


class AIAccountant:
    """AI Accountant - maintains perfect, real-time, compliant bookkeeping"""
    
    def __init__(self):
        self.name = "AI:Accountant"
        self.processed_invoices = []
        self.transaction_categories = {
            "office_supplies": ["office", "supplies", "stationery", "paper"],
            "travel": ["travel", "flight", "hotel", "taxi", "uber"],
            "meals": ["restaurant", "cafe", "lunch", "dinner", "food"],
            "utilities": ["electricity", "water", "internet", "phone"],
            "rent": ["rent", "lease", "property"],
            "professional_services": ["legal", "consultant", "advisory", "audit"],
        }
        logger.info(f"{self.name} initialized with enhanced capabilities")
    
    async def fetch_bank_transactions(self, days: int = 1) -> List[Dict[str, Any]]:
        """Fetch transactions from Wio Bank"""
        # TODO: Implement Wio Bank API integration
        logger.info(f"{self.name}: Fetching {days} days of bank transactions (stub)")
        return []
    
    async def categorize_transaction(self, transaction: Dict[str, Any]) -> str:
        """Categorize a transaction for Zoho Books using AI"""
        description = transaction.get("description", "").lower()
        
        # Simple rule-based categorization (would use ML in production)
        for category, keywords in self.transaction_categories.items():
            if any(keyword in description for keyword in keywords):
                logger.info(f"{self.name}: Categorized '{description}' as {category}")
                return category
        
        logger.info(f"{self.name}: Transaction '{description}' marked as uncategorized")
        return "uncategorized"
    
    async def process_uploaded_invoice(self, file_path: Path) -> Dict[str, Any]:
        """Process an uploaded invoice with OCR and create Zoho Books entry"""
        try:
            # Extract data using OCR
            ocr_data = await ocr_processor.extract_invoice_data(file_path)
            
            # Create invoice in Zoho Books (stub)
            zoho_response = await zoho_books.create_invoice({
                "vendor_name": ocr_data.get("vendor"),
                "invoice_number": ocr_data.get("invoice_number"),
                "amount": ocr_data.get("amount"),
                "currency": ocr_data.get("currency", "AED"),
                "line_items": ocr_data.get("line_items", []),
            })
            
            # Generate UAE e-invoice
            einvoice = generate_uae_einvoice({
                "supplier_name": "Your Company",
                "customer_name": ocr_data.get("vendor"),
                "subtotal": ocr_data.get("amount", 0),
                "vat_amount": ocr_data.get("amount", 0) * 0.05,  # 5% VAT
                "total": ocr_data.get("amount", 0) * 1.05,
                "line_items": ocr_data.get("line_items", []),
            })
            
            result = {
                "file_path": str(file_path),
                "ocr_data": ocr_data,
                "zoho_response": zoho_response,
                "einvoice": einvoice,
                "status": "processed"
            }
            
            self.processed_invoices.append(result)
            logger.info(f"{self.name}: Successfully processed invoice {ocr_data.get('invoice_number', 'Unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"{self.name}: Error processing invoice {file_path}: {e}")
            return {"status": "error", "error": str(e)}
    
    async def generate_einvoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate UAE-compliant e-invoice"""
        einvoice = generate_uae_einvoice(invoice_data)
        logger.info(f"{self.name}: Generated e-invoice {einvoice.get('invoice_id')}")
        return einvoice
    
    async def reconcile_bank(self, account_id: str = "main") -> Dict[str, Any]:
        """Perform daily bank reconciliation"""
        # TODO: Implement actual reconciliation logic
        logger.info(f"{self.name}: Bank reconciliation for account {account_id} (stub)")
        return {
            "account_id": account_id,
            "status": "reconciled",
            "discrepancies": 0,
            "balance": 0
        }
    
    async def prepare_vat_draft(self, period: str = "current") -> Dict[str, Any]:
        """Prepare draft VAT return"""
        # TODO: Calculate actual VAT from transactions
        logger.info(f"{self.name}: Preparing VAT draft for period {period} (stub)")
        return {
            "period": period,
            "total_sales": 0,
            "total_purchases": 0,
            "vat_payable": 0,
            "vat_recoverable": 0,
            "net_vat": 0,
            "status": "draft"
        }
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current status and metrics"""
        return {
            "name": self.name,
            "status": "active",
            "processed_invoices_count": len(self.processed_invoices),
            "last_activity": "Ready for work",
            "capabilities": [
                "Bank transaction processing",
                "Invoice OCR",
                "Transaction categorization", 
                "E-invoice generation",
                "VAT calculation"
            ]
        }


# Global instance
accountant = AIAccountant()
