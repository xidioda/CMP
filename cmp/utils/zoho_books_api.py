"""
Zoho Books API Integration Module

Comprehensive integration with Zoho Books API for AI agents to perform
real bookkeeping operations, manage company data, and automate financial tasks.
"""

import os
import aiohttp
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date
import json
from decimal import Decimal

from ..config import settings
from ..logging_config import get_logger
from ..db import session_scope
from ..models import Company

logger = get_logger("zoho_books_api")


class ZohoBooksAPI:
    """
    Comprehensive Zoho Books API integration for AI agents
    
    Provides full access to Zoho Books functionality including:
    - Company profile management
    - Chart of accounts
    - Customer/vendor management
    - Transaction management
    - Invoice creation and management
    - Reports and analytics
    - Bank reconciliation
    """
    
    def __init__(self):
        self.base_url = "https://www.zohoapis.com/books/v3"
        self.organization_id = settings.zoho_organization_id
        self.access_token = settings.zoho_access_token
        self.refresh_token = settings.zoho_refresh_token
        self.client_id = settings.zoho_client_id
        self.client_secret = settings.zoho_client_secret
        self.session = None
        
        # Rate limiting to prevent API limit exceeded errors
        self.api_calls_made = 0
        self.rate_limit_reset_time = datetime.now()
        self.max_calls_per_hour = 900  # Conservative limit (Zoho allows 1000)
        self.rate_limit_window = 3600  # 1 hour in seconds
        self.last_api_call = None
        self.min_delay_between_calls = 0.1  # 100ms minimum delay
    
    async def _check_rate_limit(self):
        """Check and enforce rate limiting"""
        current_time = datetime.now()
        
        # Reset counter if an hour has passed
        if (current_time - self.rate_limit_reset_time).seconds >= self.rate_limit_window:
            self.api_calls_made = 0
            self.rate_limit_reset_time = current_time
        
        # Check if we've exceeded the rate limit
        if self.api_calls_made >= self.max_calls_per_hour:
            wait_time = self.rate_limit_window - (current_time - self.rate_limit_reset_time).seconds
            logger.warning(f"Rate limit reached. Waiting {wait_time} seconds before next API call")
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                self.api_calls_made = 0
                self.rate_limit_reset_time = datetime.now()
        
        # Ensure minimum delay between calls
        if self.last_api_call:
            time_since_last_call = (current_time - self.last_api_call).total_seconds()
            if time_since_last_call < self.min_delay_between_calls:
                await asyncio.sleep(self.min_delay_between_calls - time_since_last_call)
        
        self.api_calls_made += 1
        self.last_api_call = datetime.now()
    
    async def _ensure_session(self):
        """Ensure aiohttp session is available"""
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def _refresh_access_token(self) -> bool:
        """
        Refresh the access token using the refresh token
        
        Returns:
            True if token was successfully refreshed, False otherwise
        """
        if not self.refresh_token or not self.client_id or not self.client_secret:
            logger.error("Missing refresh token or client credentials for token refresh")
            return False
            
        await self._ensure_session()
        
        try:
            refresh_url = "https://accounts.zoho.com/oauth/v2/token"
            
            data = {
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token
            }
            
            async with self.session.post(refresh_url, data=data) as response:
                result = await response.json()
                
                if response.status == 200 and "access_token" in result:
                    self.access_token = result["access_token"]
                    logger.info("Successfully refreshed Zoho Books access token")
                    
                    # Update settings (though this won't persist across restarts)
                    settings.zoho_access_token = self.access_token
                    
                    return True
                else:
                    logger.error(f"Token refresh failed: {result}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error refreshing access token: {e}")
            return False
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Dict = None, 
        params: Dict = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Make authenticated request to Zoho Books API with automatic token refresh
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            data: Request body data
            params: Query parameters
            retry_count: Number of retry attempts (for token refresh)
            
        Returns:
            API response as dictionary
        """
        await self._ensure_session()
        
        # Check rate limit before making API call
        await self._check_rate_limit()
        
        if not self.access_token or self.access_token == "your_zoho_access_token":
            raise Exception("Zoho Books access token not configured")
        
        if not self.organization_id or self.organization_id == "your_zoho_organization_id":
            raise Exception("Zoho Books organization ID not configured")
        
        url = f"{self.base_url}{endpoint}"
        
        headers = {
            "Authorization": f"Zoho-oauthtoken {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Add organization ID to params
        if not params:
            params = {}
        params["organization_id"] = self.organization_id
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=data if data else None,
                params=params
            ) as response:
                result = await response.json()
                
                # Check for authentication errors (401 or specific error codes)
                if response.status == 401 or (response.status >= 400 and "invalid" in str(result.get("message", "")).lower() and "token" in str(result.get("message", "")).lower()):
                    if retry_count == 0:  # Only retry once
                        logger.warning("Access token expired, attempting to refresh...")
                        if await self._refresh_access_token():
                            logger.info("Token refreshed, retrying request...")
                            return await self._make_request(method, endpoint, data, params, retry_count + 1)
                        else:
                            raise Exception("Failed to refresh access token")
                    else:
                        raise Exception("Access token refresh failed, unable to authenticate")
                
                if response.status >= 400:
                    error_msg = result.get("message", f"HTTP {response.status}")
                    raise Exception(f"Zoho Books API error: {error_msg}")
                
                return result
                
        except Exception as e:
            logger.error(f"Zoho Books API request failed: {e}")
            raise
    
    # COMPANY PROFILE MANAGEMENT
    
    async def get_organization_profile(self) -> Dict[str, Any]:
        """Get current organization profile from Zoho Books"""
        try:
            result = await self._make_request("GET", f"/organizations/{self.organization_id}")
            return {
                "success": True,
                "organization": result.get("organization", {})
            }
        except Exception as e:
            logger.error(f"Error getting organization profile: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_organization_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update organization profile in Zoho Books"""
        try:
            result = await self._make_request(
                "PUT", 
                f"/organizations/{self.organization_id}",
                data=profile_data
            )
            return {
                "success": True,
                "organization": result.get("organization", {}),
                "message": "Organization profile updated successfully"
            }
        except Exception as e:
            logger.error(f"Error updating organization profile: {e}")
            return {"success": False, "error": str(e)}
    
    # CHART OF ACCOUNTS
    
    async def get_chart_of_accounts(self) -> Dict[str, Any]:
        """Get chart of accounts"""
        try:
            result = await self._make_request("GET", "/chartofaccounts")
            return {
                "success": True,
                "accounts": result.get("chartofaccounts", [])
            }
        except Exception as e:
            logger.error(f"Error getting chart of accounts: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_account(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new account in chart of accounts"""
        try:
            result = await self._make_request("POST", "/chartofaccounts", data=account_data)
            return {
                "success": True,
                "account": result.get("chartofaccount", {}),
                "message": "Account created successfully"
            }
        except Exception as e:
            logger.error(f"Error creating account: {e}")
            return {"success": False, "error": str(e)}
    
    # CUSTOMERS & SALES MANAGEMENT
    
    async def get_customers(self, page: int = 1, per_page: int = 200) -> Dict[str, Any]:
        """Get list of customers"""
        try:
            params = {
                "page": page,
                "per_page": per_page
            }
            result = await self._make_request("GET", "/contacts", params=params)
            return {
                "success": True,
                "customers": result.get("contacts", [])
            }
        except Exception as e:
            logger.error(f"Error getting customers: {e}")
            return {"success": False, "error": str(e)}

    async def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new customer"""
        try:
            result = await self._make_request("POST", "/contacts", data=customer_data)
            return {
                "success": True,
                "customer": result.get("contact", {}),
                "message": "Customer created successfully"
            }
        except Exception as e:
            logger.error(f"Error creating customer: {e}")
            return {"success": False, "error": str(e)}

    async def get_quotes(self, page: int = 1, per_page: int = 200) -> Dict[str, Any]:
        """Get list of quotes"""
        try:
            params = {
                "page": page,
                "per_page": per_page
            }
            result = await self._make_request("GET", "/estimates", params=params)
            return {
                "success": True,
                "quotes": result.get("estimates", [])
            }
        except Exception as e:
            logger.error(f"Error getting quotes: {e}")
            return {"success": False, "error": str(e)}

    async def create_quote(self, quote_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new quote/estimate"""
        try:
            result = await self._make_request("POST", "/estimates", data=quote_data)
            return {
                "success": True,
                "quote": result.get("estimate", {}),
                "message": "Quote created successfully"
            }
        except Exception as e:
            logger.error(f"Error creating quote: {e}")
            return {"success": False, "error": str(e)}

    async def convert_quote_to_invoice(self, quote_id: str) -> Dict[str, Any]:
        """Convert quote to invoice"""
        try:
            result = await self._make_request("POST", f"/estimates/{quote_id}/convertto/invoice")
            return {
                "success": True,
                "invoice": result.get("invoice", {}),
                "message": "Quote converted to invoice successfully"
            }
        except Exception as e:
            logger.error(f"Error converting quote to invoice: {e}")
            return {"success": False, "error": str(e)}

    async def get_recurring_invoices(self) -> Dict[str, Any]:
        """Get list of recurring invoices"""
        try:
            result = await self._make_request("GET", "/recurringinvoices")
            return {
                "success": True,
                "recurring_invoices": result.get("recurringinvoices", [])
            }
        except Exception as e:
            logger.error(f"Error getting recurring invoices: {e}")
            return {"success": False, "error": str(e)}

    async def create_recurring_invoice(self, recurring_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new recurring invoice"""
        try:
            result = await self._make_request("POST", "/recurringinvoices", data=recurring_data)
            return {
                "success": True,
                "recurring_invoice": result.get("recurringinvoice", {}),
                "message": "Recurring invoice created successfully"
            }
        except Exception as e:
            logger.error(f"Error creating recurring invoice: {e}")
            return {"success": False, "error": str(e)}

    async def get_payments_received(self, page: int = 1, per_page: int = 200) -> Dict[str, Any]:
        """Get list of payments received"""
        try:
            params = {
                "page": page,
                "per_page": per_page
            }
            result = await self._make_request("GET", "/customerpayments", params=params)
            return {
                "success": True,
                "payments": result.get("customerpayments", [])
            }
        except Exception as e:
            logger.error(f"Error getting payments received: {e}")
            return {"success": False, "error": str(e)}

    async def record_payment_received(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record a payment received from customer"""
        try:
            result = await self._make_request("POST", "/customerpayments", data=payment_data)
            return {
                "success": True,
                "payment": result.get("customerpayment", {}),
                "message": "Payment recorded successfully"
            }
        except Exception as e:
            logger.error(f"Error recording payment: {e}")
            return {"success": False, "error": str(e)}

    async def get_credit_notes(self, page: int = 1, per_page: int = 200) -> Dict[str, Any]:
        """Get list of credit notes"""
        try:
            params = {
                "page": page,
                "per_page": per_page
            }
            result = await self._make_request("GET", "/creditnotes", params=params)
            return {
                "success": True,
                "credit_notes": result.get("creditnotes", [])
            }
        except Exception as e:
            logger.error(f"Error getting credit notes: {e}")
            return {"success": False, "error": str(e)}

    async def create_credit_note(self, credit_note_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new credit note"""
        try:
            result = await self._make_request("POST", "/creditnotes", data=credit_note_data)
            return {
                "success": True,
                "credit_note": result.get("creditnote", {}),
                "message": "Credit note created successfully"
            }
        except Exception as e:
            logger.error(f"Error creating credit note: {e}")
            return {"success": False, "error": str(e)}

    # VENDOR & PURCHASE MANAGEMENT
    
    async def get_vendors(self, page: int = 1, per_page: int = 200) -> Dict[str, Any]:
        """Get list of vendors"""
        try:
            params = {
                "page": page,
                "per_page": per_page,
                "contact_type": "vendor"
            }
            result = await self._make_request("GET", "/contacts", params=params)
            return {
                "success": True,
                "vendors": result.get("contacts", [])
            }
        except Exception as e:
            logger.error(f"Error getting vendors: {e}")
            return {"success": False, "error": str(e)}

    async def create_vendor(self, vendor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new vendor"""
        try:
            # Ensure contact type is set to vendor
            vendor_data["contact_type"] = "vendor"
            result = await self._make_request("POST", "/contacts", data=vendor_data)
            return {
                "success": True,
                "vendor": result.get("contact", {}),
                "message": "Vendor created successfully"
            }
        except Exception as e:
            logger.error(f"Error creating vendor: {e}")
            return {"success": False, "error": str(e)}

    async def get_bills(self, page: int = 1, per_page: int = 200) -> Dict[str, Any]:
        """Get list of bills"""
        try:
            params = {
                "page": page,
                "per_page": per_page
            }
            result = await self._make_request("GET", "/bills", params=params)
            return {
                "success": True,
                "bills": result.get("bills", [])
            }
        except Exception as e:
            logger.error(f"Error getting bills: {e}")
            return {"success": False, "error": str(e)}

    async def create_bill(self, bill_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new bill"""
        try:
            result = await self._make_request("POST", "/bills", data=bill_data)
            return {
                "success": True,
                "bill": result.get("bill", {}),
                "message": "Bill created successfully"
            }
        except Exception as e:
            logger.error(f"Error creating bill: {e}")
            return {"success": False, "error": str(e)}

    async def get_payments_made(self, page: int = 1, per_page: int = 200) -> Dict[str, Any]:
        """Get list of payments made to vendors"""
        try:
            params = {
                "page": page,
                "per_page": per_page
            }
            result = await self._make_request("GET", "/vendorpayments", params=params)
            return {
                "success": True,
                "payments": result.get("vendorpayments", [])
            }
        except Exception as e:
            logger.error(f"Error getting payments made: {e}")
            return {"success": False, "error": str(e)}

    async def record_payment_made(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record a payment made to vendor"""
        try:
            result = await self._make_request("POST", "/vendorpayments", data=payment_data)
            return {
                "success": True,
                "payment": result.get("vendorpayment", {}),
                "message": "Payment recorded successfully"
            }
        except Exception as e:
            logger.error(f"Error recording payment: {e}")
            return {"success": False, "error": str(e)}

    # ITEMS & SERVICES MANAGEMENT
    
    async def get_items(self, page: int = 1, per_page: int = 200) -> Dict[str, Any]:
        """Get list of items/services"""
        try:
            params = {
                "page": page,
                "per_page": per_page
            }
            result = await self._make_request("GET", "/items", params=params)
            return {
                "success": True,
                "items": result.get("items", [])
            }
        except Exception as e:
            logger.error(f"Error getting items: {e}")
            return {"success": False, "error": str(e)}

    async def create_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new item/service"""
        try:
            result = await self._make_request("POST", "/items", data=item_data)
            return {
                "success": True,
                "item": result.get("item", {}),
                "message": "Item created successfully"
            }
        except Exception as e:
            logger.error(f"Error creating item: {e}")
            return {"success": False, "error": str(e)}

    async def update_item(self, item_id: str, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing item/service"""
        try:
            result = await self._make_request("PUT", f"/items/{item_id}", data=item_data)
            return {
                "success": True,
                "item": result.get("item", {}),
                "message": "Item updated successfully"
            }
        except Exception as e:
            logger.error(f"Error updating item: {e}")
            return {"success": False, "error": str(e)}

    # PROJECTS & TIME TRACKING
    
    async def get_projects(self, page: int = 1, per_page: int = 200) -> Dict[str, Any]:
        """Get list of projects"""
        try:
            params = {
                "page": page,
                "per_page": per_page
            }
            result = await self._make_request("GET", "/projects", params=params)
            return {
                "success": True,
                "projects": result.get("projects", [])
            }
        except Exception as e:
            logger.error(f"Error getting projects: {e}")
            return {"success": False, "error": str(e)}

    async def create_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new project"""
        try:
            result = await self._make_request("POST", "/projects", data=project_data)
            return {
                "success": True,
                "project": result.get("project", {}),
                "message": "Project created successfully"
            }
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            return {"success": False, "error": str(e)}

    async def get_time_entries(self, project_id: str = None, page: int = 1, per_page: int = 200) -> Dict[str, Any]:
        """Get time entries/timesheets"""
        try:
            params = {
                "page": page,
                "per_page": per_page
            }
            if project_id:
                params["project_id"] = project_id
                
            result = await self._make_request("GET", "/projects/timeentries", params=params)
            return {
                "success": True,
                "time_entries": result.get("time_entries", [])
            }
        except Exception as e:
            logger.error(f"Error getting time entries: {e}")
            return {"success": False, "error": str(e)}

    async def create_time_entry(self, time_entry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new time entry"""
        try:
            result = await self._make_request("POST", "/projects/timeentries", data=time_entry_data)
            return {
                "success": True,
                "time_entry": result.get("time_entry", {}),
                "message": "Time entry created successfully"
            }
        except Exception as e:
            logger.error(f"Error creating time entry: {e}")
            return {"success": False, "error": str(e)}
    
    # INVOICE MANAGEMENT
    
    async def get_invoices(self, status: str = None, page: int = 1, per_page: int = 200) -> Dict[str, Any]:
        """Get list of invoices"""
        try:
            params = {"page": page, "per_page": per_page}
            if status:
                params["status"] = status
            
            result = await self._make_request("GET", "/invoices", params=params)
            return {
                "success": True,
                "invoices": result.get("invoices", []),
                "page_context": result.get("page_context", {})
            }
        except Exception as e:
            logger.error(f"Error getting invoices: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new invoice"""
        try:
            result = await self._make_request("POST", "/invoices", data=invoice_data)
            return {
                "success": True,
                "invoice": result.get("invoice", {}),
                "message": "Invoice created successfully"
            }
        except Exception as e:
            logger.error(f"Error creating invoice: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_invoice(self, invoice_id: str, send_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send invoice to customer"""
        try:
            if not send_data:
                send_data = {}
            
            result = await self._make_request(
                "POST", 
                f"/invoices/{invoice_id}/status/sent",
                data=send_data
            )
            return {
                "success": True,
                "message": "Invoice sent successfully"
            }
        except Exception as e:
            logger.error(f"Error sending invoice: {e}")
            return {"success": False, "error": str(e)}
    
    # EXPENSE MANAGEMENT
    
    async def get_expenses(self, page: int = 1, per_page: int = 200) -> Dict[str, Any]:
        """Get list of expenses"""
        try:
            params = {"page": page, "per_page": per_page}
            result = await self._make_request("GET", "/expenses", params=params)
            return {
                "success": True,
                "expenses": result.get("expenses", []),
                "page_context": result.get("page_context", {})
            }
        except Exception as e:
            logger.error(f"Error getting expenses: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_expense(self, expense_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new expense"""
        try:
            result = await self._make_request("POST", "/expenses", data=expense_data)
            return {
                "success": True,
                "expense": result.get("expense", {}),
                "message": "Expense created successfully"
            }
        except Exception as e:
            logger.error(f"Error creating expense: {e}")
            return {"success": False, "error": str(e)}
    
    # JOURNAL ENTRIES
    
    async def create_journal_entry(self, journal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new journal entry"""
        try:
            result = await self._make_request("POST", "/journalentries", data=journal_data)
            return {
                "success": True,
                "journal_entry": result.get("journalentry", {}),
                "message": "Journal entry created successfully"
            }
        except Exception as e:
            logger.error(f"Error creating journal entry: {e}")
            return {"success": False, "error": str(e)}
    
    # BANK ACCOUNTS & TRANSACTIONS
    
    async def get_bank_accounts(self) -> Dict[str, Any]:
        """Get list of bank accounts"""
        try:
            result = await self._make_request("GET", "/bankaccounts")
            return {
                "success": True,
                "bank_accounts": result.get("bankaccounts", [])
            }
        except Exception as e:
            logger.error(f"Error getting bank accounts: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_bank_transaction(self, account_id: str, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create bank transaction"""
        try:
            result = await self._make_request(
                "POST", 
                f"/bankaccounts/{account_id}/transactions",
                data=transaction_data
            )
            return {
                "success": True,
                "transaction": result.get("banktransaction", {}),
                "message": "Bank transaction created successfully"
            }
        except Exception as e:
            logger.error(f"Error creating bank transaction: {e}")
            return {"success": False, "error": str(e)}
    
    # REPORTS
    
    async def get_profit_and_loss(self, from_date: str, to_date: str) -> Dict[str, Any]:
        """Get Profit & Loss report"""
        try:
            params = {
                "from_date": from_date,
                "to_date": to_date
            }
            result = await self._make_request("GET", "/reports/profitandloss", params=params)
            return {
                "success": True,
                "report": result
            }
        except Exception as e:
            logger.error(f"Error getting P&L report: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_balance_sheet(self, as_of_date: str) -> Dict[str, Any]:
        """Get Balance Sheet report"""
        try:
            params = {"date": as_of_date}
            result = await self._make_request("GET", "/reports/balancesheet", params=params)
            return {
                "success": True,
                "report": result
            }
        except Exception as e:
            logger.error(f"Error getting balance sheet: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_trial_balance(self, from_date: str, to_date: str) -> Dict[str, Any]:
        """Get Trial Balance report"""
        try:
            params = {
                "from_date": from_date,
                "to_date": to_date
            }
            result = await self._make_request("GET", "/reports/trialbalance", params=params)
            return {
                "success": True,
                "report": result
            }
        except Exception as e:
            logger.error(f"Error getting trial balance: {e}")
            return {"success": False, "error": str(e)}
    
    # TAX MANAGEMENT
    
    async def get_taxes(self) -> Dict[str, Any]:
        """Get list of taxes"""
        try:
            result = await self._make_request("GET", "/settings/taxes")
            return {
                "success": True,
                "taxes": result.get("taxes", [])
            }
        except Exception as e:
            logger.error(f"Error getting taxes: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_tax(self, tax_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new tax"""
        try:
            result = await self._make_request("POST", "/settings/taxes", data=tax_data)
            return {
                "success": True,
                "tax": result.get("tax", {}),
                "message": "Tax created successfully"
            }
        except Exception as e:
            logger.error(f"Error creating tax: {e}")
            return {"success": False, "error": str(e)}
    
    # UTILITY METHODS
    
    async def sync_company_profile_to_zoho(self) -> Dict[str, Any]:
        """Sync CMP company profile to Zoho Books"""
        try:
            # Get current CMP company data
            with session_scope() as session:
                company = session.query(Company).first()
                if not company:
                    return {"success": False, "error": "No company data found in CMP"}
            
            # Prepare Zoho organization profile data
            zoho_data = {
                "name": company.legal_name or company.trade_name,
                "address": {
                    "attention": "",  # Contact person not available in Company model
                    "address": company.address_line1 or "",
                    "street2": company.address_line2 or "",
                    "city": company.city or "",
                    "state": company.emirate or "",
                    "zip": company.po_box or "",
                    "country": company.country or "United Arab Emirates"
                },
                "phone": company.phone or "",
                "email": company.email or "",
                "website": company.website or "",
                "industry_type": "Financial Services",
                "currency_code": company.currency or "AED"
                # Removed fiscal_year_start_month due to API format issues
            }
            
            # Add tax information if available
            if company.vat_registered and company.vat_registration_number:
                zoho_data["tax_id_no"] = company.vat_registration_number
                zoho_data["is_registered_for_tax"] = True
            
            # Update Zoho Books organization profile
            result = await self.update_organization_profile(zoho_data)
            
            if result["success"]:
                logger.info("Successfully synced company profile to Zoho Books")
                return {
                    "success": True,
                    "message": "Company profile synced to Zoho Books successfully",
                    "zoho_data": zoho_data
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error syncing company profile to Zoho: {e}")
            return {"success": False, "error": str(e)}
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None


# Global instance for AI agents to use
zoho_books_api = ZohoBooksAPI()