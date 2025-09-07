"""
UAE E-Invoice Generation and Banking Integrations

Handles UAE FTA-compliant e-invoices and real banking integrations for UAE market.
Updated to use actual UAE banking APIs and file import methods.
"""

from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime
from pathlib import Path
import httpx

from ..logging_config import get_logger
from ..config import settings

logger = get_logger("integrations.invoices")


def generate_uae_einvoice(invoice_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate UAE FTA-compliant e-invoice
    
    Args:
        invoice_data: Invoice details including amount, vendor, items, etc.
    
    Returns:
        Dictionary containing the e-invoice in UAE-compliant format
    """
    
    # TODO: Implement actual UAE e-invoice format per FTA specifications
    # This is a placeholder structure
    
    einvoice = {
        "invoice_id": invoice_data.get("invoice_id", f"INV-{uuid.uuid4().hex[:8].upper()}"),
        "issue_date": datetime.now().isoformat(),
        "invoice_type": "388",  # Standard commercial invoice
        "currency": "AED",
        "supplier": {
            "name": invoice_data.get("supplier_name", ""),
            "vat_number": invoice_data.get("supplier_vat", ""),
            "address": invoice_data.get("supplier_address", "")
        },
        "customer": {
            "name": invoice_data.get("customer_name", ""),
            "vat_number": invoice_data.get("customer_vat", ""),
            "address": invoice_data.get("customer_address", "")
        },
        "line_items": invoice_data.get("line_items", []),
        "totals": {
            "subtotal": invoice_data.get("subtotal", 0),
            "vat_amount": invoice_data.get("vat_amount", 0),
            "total": invoice_data.get("total", 0)
        },
        "vat_breakdown": invoice_data.get("vat_breakdown", []),
        # UAE-specific fields
        "invoice_hash": "",  # TODO: Generate cryptographic hash
        "qr_code": "",       # TODO: Generate QR code for verification
        "digital_signature": ""  # TODO: Digital signature if required
    }
    
    logger.info(f"Generated UAE e-invoice: {einvoice['invoice_id']}")
    return einvoice


def validate_uae_einvoice(einvoice: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate UAE e-invoice against FTA requirements
    
    Args:
        einvoice: E-invoice to validate
    
    Returns:
        Validation result with any errors or warnings
    """
    
    # TODO: Implement actual UAE e-invoice validation rules
    errors = []
    warnings = []
    
    # Basic validation checks (placeholder)
    required_fields = ["invoice_id", "issue_date", "supplier", "customer", "totals"]
    for field in required_fields:
        if field not in einvoice:
            errors.append(f"Missing required field: {field}")
    
    logger.info(f"Validated e-invoice {einvoice.get('invoice_id', 'UNKNOWN')}: {len(errors)} errors, {len(warnings)} warnings")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


class ZohoBooksConnector:
    """Production Zoho Books API client with OAuth 2.0 authentication"""
    
    def __init__(self, client_id: str = "", client_secret: str = "", access_token: str = "", 
                 refresh_token: str = "", organization_id: str = "", base_url: str = ""):
        self.client_id = client_id or settings.zoho_client_id or ""
        self.client_secret = client_secret or settings.zoho_client_secret or ""
        self.access_token = access_token or settings.zoho_access_token or ""
        self.refresh_token = refresh_token or settings.zoho_refresh_token or ""
        self.organization_id = organization_id or settings.zoho_organization_id or ""
        self.base_url = base_url or settings.zoho_base_url
        
        # Check if we have credentials for production use
        self.is_configured = bool(self.client_id and self.client_secret and self.organization_id)
        
        if self.is_configured:
            logger.info("Zoho Books connector initialized for production use")
        else:
            logger.warning("Zoho Books connector running in stub mode - missing credentials")
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get Zoho OAuth headers"""
        if not self.access_token:
            return {}
        return {
            "Authorization": f"Zoho-oauthtoken {self.access_token}",
            "Content-Type": "application/json"
        }
    
    async def refresh_access_token(self) -> bool:
        """Refresh expired access token using refresh token"""
        if not self.refresh_token or not self.client_id or not self.client_secret:
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://accounts.zoho.com/oauth/v2/token",
                    data={
                        "refresh_token": self.refresh_token,
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "grant_type": "refresh_token"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.access_token = data.get("access_token", "")
                    logger.info("Zoho access token refreshed successfully")
                    return True
                else:
                    logger.error(f"Failed to refresh Zoho token: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"Error refreshing Zoho token: {e}")
            return False
    
    async def _make_zoho_request(self, method: str, endpoint: str, data: Optional[Dict] = None,
                                params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to Zoho Books API"""
        if not self.is_configured:
            logger.warning(f"Zoho Books API call ({method} {endpoint}) - running in stub mode")
            return {"message": "stub_response", "code": 0}
        
        # Ensure organization_id is in params
        if params is None:
            params = {}
        params["organization_id"] = self.organization_id
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self.get_auth_headers()
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=headers
                )
                
                if response.status_code == 401:  # Token expired
                    logger.info("Access token expired, attempting refresh")
                    if await self.refresh_access_token():
                        # Retry with new token
                        headers = self.get_auth_headers()
                        response = await client.request(
                            method=method,
                            url=url,
                            json=data,
                            params=params,
                            headers=headers
                        )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Zoho API error: {response.status_code} - {response.text}")
                    return {"error": f"API call failed: {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Zoho Books API request failed: {e}")
            return {"error": str(e)}
    
    async def create_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create invoice in Zoho Books"""
        if not self.is_configured:
            logger.info("Creating invoice in Zoho Books (stub mode)")
            return {"invoice_id": "ZB-STUB-001", "status": "created", "mode": "stub"}
        
        # Transform our invoice data to Zoho Books format
        zoho_invoice = {
            "customer_name": invoice_data.get("customer_name", ""),
            "invoice_number": invoice_data.get("invoice_number", ""),
            "date": invoice_data.get("date", ""),
            "due_date": invoice_data.get("due_date", ""),
            "currency_code": invoice_data.get("currency", "AED"),
            "line_items": []
        }
        
        # Convert line items
        for item in invoice_data.get("line_items", []):
            zoho_item = {
                "name": item.get("description", ""),
                "description": item.get("description", ""),
                "rate": item.get("unit_price", 0),
                "quantity": item.get("quantity", 1),
                "tax_id": ""  # Would map to appropriate tax ID
            }
            zoho_invoice["line_items"].append(zoho_item)
        
        result = await self._make_zoho_request("POST", "invoices", data=zoho_invoice)
        logger.info(f"Created invoice in Zoho Books: {result.get('invoice', {}).get('invoice_id', 'Unknown')}")
        return result
    
    async def get_transactions(self, account_id: str, from_date: str = "", to_date: str = "") -> List[Dict[str, Any]]:
        """Fetch transactions from Zoho Books"""
        if not self.is_configured:
            logger.info(f"Fetching transactions for account {account_id} (stub mode)")
            return []
        
        params = {}
        if from_date:
            params["from_date"] = from_date
        if to_date:
            params["to_date"] = to_date
        
        result = await self._make_zoho_request("GET", f"banktransactions", params=params)
        transactions = result.get("banktransactions", [])
        logger.info(f"Fetched {len(transactions)} transactions from Zoho Books")
        return transactions
    
    async def get_organizations(self) -> List[Dict[str, Any]]:
        """Get list of organizations (useful for getting organization_id)"""
        if not self.is_configured:
            return [{"organization_id": "stub_org", "name": "Stub Organization"}]
        
        result = await self._make_zoho_request("GET", "organizations")
        return result.get("organizations", [])
    
    async def create_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a contact/customer in Zoho Books"""
        if not self.is_configured:
            logger.info("Creating contact in Zoho Books (stub mode)")
            return {"contact_id": "ZB-CONTACT-STUB-001", "status": "created", "mode": "stub"}
        
        zoho_contact = {
            "contact_name": contact_data.get("name", ""),
            "company_name": contact_data.get("company", ""),
            "email": contact_data.get("email", ""),
            "phone": contact_data.get("phone", ""),
            "contact_type": contact_data.get("type", "customer")
        }
        
        result = await self._make_zoho_request("POST", "contacts", data=zoho_contact)
        logger.info(f"Created contact in Zoho Books: {result.get('contact', {}).get('contact_id', 'Unknown')}")
        return result


class EmiratesNBDConnector:
    """Production Emirates NBD API Souq client for UAE banking integration"""
    
    def __init__(self, api_key: str = "", client_id: str = "", account_number: str = "", base_url: str = ""):
        self.api_key = api_key or settings.emirates_nbd_api_key or ""
        self.client_id = client_id or settings.emirates_nbd_client_id or ""
        self.account_number = account_number or settings.emirates_nbd_account_number or ""
        self.base_url = base_url or settings.emirates_nbd_base_url
        
        # Check if we have credentials for production use
        self.is_configured = bool(self.api_key and self.client_id and self.account_number)
        
        if self.is_configured:
            logger.info("Emirates NBD API Souq connector initialized for production use")
        else:
            logger.warning("Emirates NBD connector running in stub mode - missing credentials")
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get Emirates NBD API authentication headers"""
        if not self.api_key:
            return {}
        
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Client-Id": self.client_id,
            "Content-Type": "application/json"
        }
    
    async def _make_emirates_nbd_request(self, method: str, endpoint: str, data: Optional[Dict] = None,
                               params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to Emirates NBD API Souq"""
        if not self.is_configured:
            logger.warning(f"Emirates NBD API call ({method} {endpoint}) - running in stub mode")
            return {"message": "stub_response", "status": "success"}
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self.get_auth_headers()
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=headers
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Emirates NBD API error: {response.status_code} - {response.text}")
                    return {"error": f"API call failed: {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Emirates NBD API request failed: {e}")
            return {"error": str(e)}
    
    async def fetch_transactions(self, account_number: str = "", days: int = 1) -> List[Dict[str, Any]]:
        """Fetch recent transactions from Emirates NBD"""
        account = account_number or self.account_number
        
        if not self.is_configured:
            logger.info(f"Fetching {days} days of transactions for Emirates NBD account {account} (stub mode)")
            # Return realistic UAE banking stub data
            return [
                {
                    "transaction_id": "ENBD-TXN-001",
                    "date": datetime.now().isoformat(),
                    "description": "POS Transaction - Carrefour Mall",
                    "amount": -245.50,
                    "currency": "AED",
                    "balance": 15750.25,
                    "type": "debit",
                    "category": "retail",
                    "reference": "POS240815001"
                },
                {
                    "transaction_id": "ENBD-TXN-002", 
                    "date": datetime.now().isoformat(),
                    "description": "Salary Transfer - ABC Company",
                    "amount": 12000.00,
                    "currency": "AED",
                    "balance": 15995.75,
                    "type": "credit",
                    "category": "salary",
                    "reference": "SAL240815002"
                }
            ]
        
        # Calculate date range
        from datetime import timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        params = {
            "account_number": account,
            "from_date": start_date.strftime("%Y-%m-%d"),
            "to_date": end_date.strftime("%Y-%m-%d"),
            "limit": 100
        }
        
        result = await self._make_emirates_nbd_request("GET", "accounts/transactions", params=params)
        transactions = result.get("transactions", [])
        logger.info(f"Fetched {len(transactions)} transactions from Emirates NBD")
        return transactions
    
    async def get_balance(self, account_number: str = "") -> Dict[str, Any]:
        """Get current account balance from Emirates NBD"""
        account = account_number or self.account_number
        
        if not self.is_configured:
            logger.info(f"Getting balance for Emirates NBD account {account} (stub mode)")
            return {
                "account_number": account,
                "balance": 15750.25,
                "currency": "AED",
                "available_balance": 15000.00,
                "timestamp": datetime.now().isoformat(),
                "mode": "stub",
                "bank": "Emirates NBD"
            }
        
        params = {"account_number": account}
        result = await self._make_emirates_nbd_request("GET", "accounts/balance", params=params)
        logger.info(f"Retrieved balance for Emirates NBD account {account}")
        return result
    
    async def get_account_details(self, account_number: str = "") -> Dict[str, Any]:
        """Get detailed account information from Emirates NBD"""
        account = account_number or self.account_number
        
        if not self.is_configured:
            logger.info(f"Getting Emirates NBD account details for {account} (stub mode)")
            return {
                "account_number": account,
                "account_name": "Business Current Account",
                "account_type": "current",
                "currency": "AED",
                "status": "active",
                "bank": "Emirates NBD",
                "branch": "Business Banking - Dubai Mall",
                "mode": "stub"
            }
        
        params = {"account_number": account}
        result = await self._make_emirates_nbd_request("GET", "accounts/details", params=params)
        logger.info(f"Retrieved Emirates NBD account details for {account}")
        return result


class BankFileImporter:
    """Bank statement file importer for banks that don't have APIs"""
    
    def __init__(self):
        self.supported_formats = [".csv", ".xlsx", ".qif", ".ofx"]
        logger.info("Bank file importer initialized - supports CSV, Excel, QIF, OFX formats")
    
    async def import_statement(self, file_path: Path, bank_name: str = "Unknown") -> List[Dict[str, Any]]:
        """Import transactions from bank statement file"""
        
        if not file_path.exists():
            logger.error(f"Bank statement file not found: {file_path}")
            return []
        
        file_ext = file_path.suffix.lower()
        
        if file_ext not in self.supported_formats:
            logger.error(f"Unsupported file format: {file_ext}")
            return []
        
        try:
            if file_ext == ".csv":
                return await self._import_csv(file_path, bank_name)
            elif file_ext in [".xlsx", ".xls"]:
                return await self._import_excel(file_path, bank_name)
            else:
                logger.warning(f"Format {file_ext} support coming soon")
                return []
                
        except Exception as e:
            logger.error(f"Failed to import bank statement: {e}")
            return []
    
    async def _import_csv(self, file_path: Path, bank_name: str) -> List[Dict[str, Any]]:
        """Import CSV bank statement (common format for UAE banks)"""
        import csv
        
        transactions = []
        
        # Common CSV column mappings for UAE banks
        column_mappings = {
            "date": ["date", "transaction_date", "value_date", "posting_date"],
            "description": ["description", "narrative", "details", "particulars"],
            "amount": ["amount", "transaction_amount", "debit", "credit"],
            "balance": ["balance", "running_balance", "available_balance"],
            "reference": ["reference", "ref", "transaction_ref", "cheque_no"]
        }
        
        with open(file_path, 'r', encoding='utf-8') as file:
            # Try to detect CSV dialect
            sample = file.read(1024)
            file.seek(0)
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
            
            reader = csv.DictReader(file, delimiter=delimiter)
            
            for row_num, row in enumerate(reader, 1):
                if row_num > 1000:  # Limit to 1000 transactions for safety
                    break
                
                try:
                    # Map columns to standard format
                    transaction = {
                        "transaction_id": f"{bank_name}-CSV-{row_num:04d}",
                        "date": self._extract_field(row, column_mappings["date"]),
                        "description": self._extract_field(row, column_mappings["description"]),
                        "amount": self._parse_amount(self._extract_field(row, column_mappings["amount"])),
                        "balance": self._parse_amount(self._extract_field(row, column_mappings["balance"])),
                        "reference": self._extract_field(row, column_mappings["reference"]),
                        "currency": "AED",
                        "type": "debit" if str(self._extract_field(row, column_mappings["amount"])).startswith("-") else "credit",
                        "bank": bank_name,
                        "source": "csv_import"
                    }
                    
                    if transaction["date"] and transaction["amount"] is not None:
                        transactions.append(transaction)
                        
                except Exception as e:
                    logger.warning(f"Skipped row {row_num} due to parsing error: {e}")
                    continue
        
        logger.info(f"Imported {len(transactions)} transactions from {bank_name} CSV file")
        return transactions
    
    async def _import_excel(self, file_path: Path, bank_name: str) -> List[Dict[str, Any]]:
        """Import Excel bank statement"""
        # Would implement Excel parsing here
        logger.info(f"Excel import for {bank_name} - feature coming soon")
        return []
    
    def _extract_field(self, row: Dict, possible_columns: List[str]) -> str:
        """Extract field value from row using possible column names"""
        for col in possible_columns:
            for key, value in row.items():
                if col.lower() in key.lower():
                    return str(value).strip() if value else ""
        return ""
    
    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """Parse amount string to float"""
        if not amount_str:
            return None
        
        try:
            # Remove common currency symbols and commas
            cleaned = amount_str.replace("AED", "").replace(",", "").replace(" ", "").strip()
            return float(cleaned)
        except ValueError:
            return None


# Global connector instances - Updated for realistic UAE banking
zoho_books = ZohoBooksConnector()
emirates_nbd = EmiratesNBDConnector()
bank_file_importer = BankFileImporter()

# Legacy alias for compatibility (now points to Emirates NBD)
wio_bank = emirates_nbd  # For backward compatibility with existing code
