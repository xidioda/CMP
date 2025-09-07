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
from datetime import datetime

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
        """Fetch transactions from Wio Bank with enhanced error handling"""
        from ..integrations.invoices import wio_bank
        
        try:
            transactions = await wio_bank.fetch_transactions(days=days)
            logger.info(f"{self.name}: Successfully fetched {len(transactions)} bank transactions")
            
            # Process and categorize each transaction
            processed_transactions = []
            for txn in transactions:
                # Add automatic categorization
                category = await self.categorize_transaction(txn)
                txn["category"] = category
                processed_transactions.append(txn)
            
            return processed_transactions
            
        except Exception as e:
            logger.error(f"{self.name}: Error fetching bank transactions: {e}")
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
            
            # Prepare invoice data for Zoho Books
            invoice_data = {
                "customer_name": ocr_data.get("vendor", "Unknown Vendor"),
                "invoice_number": ocr_data.get("invoice_number", ""),
                "date": ocr_data.get("date", ""),
                "currency": ocr_data.get("currency", "AED"),
                "line_items": ocr_data.get("line_items", []),
                "total_amount": ocr_data.get("amount", 0)
            }
            
            # Create invoice in Zoho Books
            zoho_response = await zoho_books.create_invoice(invoice_data)
            
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
                "status": "processed",
                "confidence": ocr_data.get("confidence", 0)
            }
            
            self.processed_invoices.append(result)
            logger.info(f"{self.name}: Successfully processed invoice {ocr_data.get('invoice_number', 'Unknown')} (confidence: {ocr_data.get('confidence', 0):.2f})")
            return result
            
        except Exception as e:
            logger.error(f"{self.name}: Error processing invoice {file_path}: {e}")
            return {"status": "error", "error": str(e), "file_path": str(file_path)}
    
    async def generate_einvoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate UAE-compliant e-invoice"""
        einvoice = generate_uae_einvoice(invoice_data)
        logger.info(f"{self.name}: Generated e-invoice {einvoice.get('invoice_id')}")
        return einvoice
    
    async def reconcile_bank(self, account_id: str = "main") -> Dict[str, Any]:
        """Perform daily bank reconciliation with real data"""
        from ..integrations.invoices import wio_bank, zoho_books
        
        try:
            # Get bank transactions from Wio Bank
            bank_transactions = await wio_bank.fetch_transactions(days=1)
            
            # Get transactions from Zoho Books
            zoho_transactions = await zoho_books.get_transactions(account_id)
            
            # Get current balance from Wio Bank
            balance_info = await wio_bank.get_balance()
            
            # Perform reconciliation logic
            bank_total = sum(txn.get("amount", 0) for txn in bank_transactions)
            zoho_total = sum(txn.get("amount", 0) for txn in zoho_transactions)
            discrepancy = abs(bank_total - zoho_total)
            
            status = "reconciled" if discrepancy < 0.01 else "discrepancy_found"
            
            result = {
                "account_id": account_id,
                "status": status,
                "bank_transactions_count": len(bank_transactions),
                "zoho_transactions_count": len(zoho_transactions),
                "bank_total": bank_total,
                "zoho_total": zoho_total,
                "discrepancy": discrepancy,
                "balance": balance_info.get("balance", 0),
                "currency": balance_info.get("currency", "AED"),
                "reconciliation_date": datetime.now().isoformat()
            }
            
            logger.info(f"{self.name}: Bank reconciliation completed - Status: {status}, Discrepancy: {discrepancy}")
            return result
            
        except Exception as e:
            logger.error(f"{self.name}: Error during bank reconciliation: {e}")
            return {
                "account_id": account_id,
                "status": "error",
                "error": str(e),
                "discrepancy": 0,
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
