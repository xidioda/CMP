"""
AI Agent Zoho Books Tools

Provides Zoho Books integration tools specifically designed for AI agents
to perform bookkeeping operations, manage company data, and automate financial tasks.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal
import json

from .zoho_books_api import zoho_books_api
from ..logging_config import get_logger
from ..db import session_scope
from ..models import append_ledger_entry

logger = get_logger("agent_zoho_tools")


class AgentZohoBooks:
    """
    Zoho Books tools for AI agents
    
    Provides high-level functions that AI agents can use to perform
    real bookkeeping operations and manage financial data in Zoho Books.
    """
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.actor = f"AI:{agent_name}"
        self.api = zoho_books_api
    
    # COMPANY PROFILE MANAGEMENT
    
    async def get_company_profile_from_zoho(self) -> Dict[str, Any]:
        """Get company profile from Zoho Books"""
        try:
            result = await self.api.get_organization_profile()
            
            if result["success"]:
                profile = result["organization"]
                
                # Extract key information
                company_info = {
                    "name": profile.get("name", ""),
                    "email": profile.get("email", ""),
                    "phone": profile.get("phone", ""),
                    "website": profile.get("website", ""),
                    "address": profile.get("address", {}),
                    "currency": profile.get("currency_code", "AED"),
                    "fiscal_year_start": profile.get("fiscal_year_start_month", 1),
                    "tax_id": profile.get("tax_id_no", ""),
                    "industry": profile.get("industry_type", ""),
                    "is_tax_registered": profile.get("is_registered_for_tax", False)
                }
                
                logger.info(f"{self.actor}: Retrieved company profile from Zoho Books")
                return {
                    "success": True,
                    "company_info": company_info,
                    "raw_profile": profile
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"{self.actor}: Error getting company profile from Zoho: {e}")
            return {"success": False, "error": str(e)}
    
    async def sync_company_profile_to_zoho(self, user_message: str = None) -> Dict[str, Any]:
        """Sync CMP company profile to Zoho Books"""
        try:
            result = await self.api.sync_company_profile_to_zoho()
            
            if result["success"]:
                # Log the action
                with session_scope() as session:
                    append_ledger_entry(
                        session,
                        actor=self.actor,
                        action="sync_company_profile_to_zoho",
                        data={
                            "user_message": user_message,
                            "zoho_data": result.get("zoho_data", {}),
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
                
                logger.info(f"{self.actor}: Synced company profile to Zoho Books")
            
            return result
            
        except Exception as e:
            logger.error(f"{self.actor}: Error syncing company profile to Zoho: {e}")
            return {"success": False, "error": str(e)}
    
    # CUSTOMER MANAGEMENT
    
    async def create_customer_in_zoho(
        self, 
        customer_name: str, 
        email: str = None, 
        phone: str = None, 
        address: Dict[str, str] = None,
        user_message: str = None
    ) -> Dict[str, Any]:
        """Create new customer in Zoho Books"""
        try:
            customer_data = {
                "contact_name": customer_name,
                "contact_type": "customer"
            }
            
            if email:
                customer_data["email"] = email
            if phone:
                customer_data["phone"] = phone
            if address:
                customer_data["billing_address"] = address
                customer_data["shipping_address"] = address
            
            result = await self.api.create_customer(customer_data)
            
            if result["success"]:
                # Log the action
                with session_scope() as session:
                    append_ledger_entry(
                        session,
                        actor=self.actor,
                        action="create_customer_in_zoho",
                        data={
                            "customer_name": customer_name,
                            "customer_id": result["customer"].get("contact_id"),
                            "user_message": user_message,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
                
                logger.info(f"{self.actor}: Created customer '{customer_name}' in Zoho Books")
            
            return result
            
        except Exception as e:
            logger.error(f"{self.actor}: Error creating customer in Zoho: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_customers_from_zoho(self) -> Dict[str, Any]:
        """Get list of customers from Zoho Books"""
        try:
            result = await self.api.get_customers()
            
            if result["success"]:
                customers = result["customers"]
                
                # Extract simplified customer list
                customer_list = []
                for customer in customers:
                    customer_list.append({
                        "id": customer.get("contact_id"),
                        "name": customer.get("contact_name"),
                        "email": customer.get("email"),
                        "phone": customer.get("phone"),
                        "outstanding_receivable": customer.get("outstanding_receivable_amount", 0),
                        "status": customer.get("status")
                    })
                
                logger.info(f"{self.actor}: Retrieved {len(customer_list)} customers from Zoho Books")
                return {
                    "success": True,
                    "customers": customer_list,
                    "total_count": len(customer_list)
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"{self.actor}: Error getting customers from Zoho: {e}")
            return {"success": False, "error": str(e)}

    # QUOTES MANAGEMENT
    
    async def create_quote_in_zoho(
        self,
        customer_id: str,
        line_items: List[Dict[str, Any]],
        quote_date: str = None,
        expiry_date: str = None,
        notes: str = None,
        user_message: str = None
    ) -> Dict[str, Any]:
        """Create new quote in Zoho Books"""
        try:
            quote_data = {
                "customer_id": customer_id,
                "line_items": line_items
            }
            
            if quote_date:
                quote_data["estimate_date"] = quote_date
            else:
                quote_data["estimate_date"] = datetime.now().strftime("%Y-%m-%d")
                
            if expiry_date:
                quote_data["expiry_date"] = expiry_date
            else:
                # Default expiry: 30 days from quote date
                expiry = datetime.now() + timedelta(days=30)
                quote_data["expiry_date"] = expiry.strftime("%Y-%m-%d")
                
            if notes:
                quote_data["notes"] = notes
            
            result = await self.api.create_quote(quote_data)
            
            if result["success"]:
                quote = result["quote"]
                
                # Log the action
                with session_scope() as session:
                    append_ledger_entry(
                        session,
                        actor=self.actor,
                        action="create_quote_in_zoho",
                        data={
                            "quote_id": quote.get("estimate_id"),
                            "customer_id": customer_id,
                            "amount": quote.get("total"),
                            "user_message": user_message,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
                
                logger.info(f"{self.actor}: Created quote of {quote.get('total', 0)} AED in Zoho Books")
                
                return {
                    "success": True,
                    "quote": {
                        "id": quote.get("estimate_id"),
                        "number": quote.get("estimate_number"),
                        "customer": quote.get("customer_name"),
                        "total": quote.get("total"),
                        "status": quote.get("status"),
                        "expiry_date": quote.get("expiry_date")
                    },
                    "message": f"Quote created successfully for {quote.get('total', 0)} AED"
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"{self.actor}: Error creating quote in Zoho: {e}")
            return {"success": False, "error": str(e)}

    async def convert_quote_to_invoice_in_zoho(self, quote_id: str, user_message: str = None) -> Dict[str, Any]:
        """Convert quote to invoice in Zoho Books"""
        try:
            result = await self.api.convert_quote_to_invoice(quote_id)
            
            if result["success"]:
                invoice = result["invoice"]
                
                # Log the action
                with session_scope() as session:
                    append_ledger_entry(
                        session,
                        actor=self.actor,
                        action="convert_quote_to_invoice",
                        data={
                            "quote_id": quote_id,
                            "invoice_id": invoice.get("invoice_id"),
                            "user_message": user_message,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
                
                logger.info(f"{self.actor}: Converted quote {quote_id} to invoice in Zoho Books")
                return result
            else:
                return result
                
        except Exception as e:
            logger.error(f"{self.actor}: Error converting quote to invoice: {e}")
            return {"success": False, "error": str(e)}

    async def get_quotes_from_zoho(self) -> Dict[str, Any]:
        """Get all quotes from Zoho Books"""
        try:
            result = await self.api.get_quotes()
            
            if result["success"]:
                quotes = result["quotes"]
                
                # Extract simplified quote list
                quote_list = []
                for quote in quotes:
                    quote_list.append({
                        "id": quote.get("estimate_id"),
                        "number": quote.get("estimate_number"),
                        "customer": quote.get("customer_name"),
                        "total": quote.get("total"),
                        "status": quote.get("status"),
                        "date": quote.get("estimate_date"),
                        "expiry_date": quote.get("expiry_date")
                    })
                
                logger.info(f"{self.actor}: Retrieved {len(quote_list)} quotes from Zoho Books")
                return {
                    "success": True,
                    "quotes": quote_list,
                    "total_count": len(quote_list)
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"{self.actor}: Error getting quotes from Zoho: {e}")
            return {"success": False, "error": str(e)}

    # PAYMENTS RECEIVED MANAGEMENT
    
    async def record_payment_received_in_zoho(
        self,
        customer_id: str,
        amount: float,
        payment_date: str = None,
        payment_mode: str = "bank_transfer",
        reference_number: str = None,
        notes: str = None,
        user_message: str = None
    ) -> Dict[str, Any]:
        """Record payment received from customer in Zoho Books"""
        try:
            payment_data = {
                "customer_id": customer_id,
                "amount": str(amount),
                "payment_mode": payment_mode
            }
            
            if payment_date:
                payment_data["date"] = payment_date
            else:
                payment_data["date"] = datetime.now().strftime("%Y-%m-%d")
                
            if reference_number:
                payment_data["reference_number"] = reference_number
                
            if notes:
                payment_data["notes"] = notes
            
            result = await self.api.record_payment_received(payment_data)
            
            if result["success"]:
                payment = result["payment"]
                
                # Log the action
                with session_scope() as session:
                    append_ledger_entry(
                        session,
                        actor=self.actor,
                        action="record_payment_received",
                        data={
                            "payment_id": payment.get("payment_id"),
                            "customer_id": customer_id,
                            "amount": amount,
                            "user_message": user_message,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
                
                logger.info(f"{self.actor}: Recorded payment of {amount} AED from customer in Zoho Books")
                
                return {
                    "success": True,
                    "payment": {
                        "id": payment.get("payment_id"),
                        "amount": payment.get("amount"),
                        "customer": payment.get("customer_name"),
                        "date": payment.get("date"),
                        "payment_mode": payment.get("payment_mode")
                    },
                    "message": f"Payment of {amount} AED recorded successfully"
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"{self.actor}: Error recording payment in Zoho: {e}")
            return {"success": False, "error": str(e)}

    # VENDOR MANAGEMENT
    
    async def create_vendor_in_zoho(
        self,
        vendor_name: str,
        email: str = None,
        phone: str = None,
        address: Dict[str, str] = None,
        user_message: str = None
    ) -> Dict[str, Any]:
        """Create new vendor in Zoho Books"""
        try:
            vendor_data = {
                "contact_name": vendor_name,
                "contact_type": "vendor"
            }
            
            if email:
                vendor_data["email"] = email
                
            if phone:
                vendor_data["phone"] = phone
                
            if address:
                vendor_data["billing_address"] = address
            
            result = await self.api.create_vendor(vendor_data)
            
            if result["success"]:
                vendor = result["vendor"]
                
                # Log the action
                with session_scope() as session:
                    append_ledger_entry(
                        session,
                        actor=self.actor,
                        action="create_vendor_in_zoho",
                        data={
                            "vendor_id": vendor.get("contact_id"),
                            "vendor_name": vendor_name,
                            "user_message": user_message,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
                
                logger.info(f"{self.actor}: Created vendor '{vendor_name}' in Zoho Books")
                
                return {
                    "success": True,
                    "vendor": {
                        "id": vendor.get("contact_id"),
                        "name": vendor.get("contact_name"),
                        "email": vendor.get("email"),
                        "phone": vendor.get("phone"),
                        "status": vendor.get("status")
                    },
                    "message": f"Vendor '{vendor_name}' created successfully"
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"{self.actor}: Error creating vendor in Zoho: {e}")
            return {"success": False, "error": str(e)}

    async def get_vendors_from_zoho(self) -> Dict[str, Any]:
        """Get all vendors from Zoho Books"""
        try:
            result = await self.api.get_vendors()
            
            if result["success"]:
                vendors = result["vendors"]
                
                # Extract simplified vendor list
                vendor_list = []
                for vendor in vendors:
                    vendor_list.append({
                        "id": vendor.get("contact_id"),
                        "name": vendor.get("contact_name"),
                        "email": vendor.get("email"),
                        "phone": vendor.get("phone"),
                        "outstanding_payable": vendor.get("outstanding_payable_amount", 0),
                        "status": vendor.get("status")
                    })
                
                logger.info(f"{self.actor}: Retrieved {len(vendor_list)} vendors from Zoho Books")
                return {
                    "success": True,
                    "vendors": vendor_list,
                    "total_count": len(vendor_list)
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"{self.actor}: Error getting vendors from Zoho: {e}")
            return {"success": False, "error": str(e)}

    async def create_bill_in_zoho(
        self,
        vendor_id: str,
        line_items: List[Dict[str, Any]],
        bill_date: str = None,
        due_date: str = None,
        bill_number: str = None,
        notes: str = None,
        user_message: str = None
    ) -> Dict[str, Any]:
        """Create new bill from vendor in Zoho Books"""
        try:
            bill_data = {
                "vendor_id": vendor_id,
                "line_items": line_items
            }
            
            if bill_date:
                bill_data["date"] = bill_date
            else:
                bill_data["date"] = datetime.now().strftime("%Y-%m-%d")
                
            if due_date:
                bill_data["due_date"] = due_date
            else:
                # Default due date: 30 days from bill date
                due_date_obj = datetime.now() + timedelta(days=30)
                bill_data["due_date"] = due_date_obj.strftime("%Y-%m-%d")
                
            if bill_number:
                bill_data["bill_number"] = bill_number
                
            if notes:
                bill_data["notes"] = notes
            
            result = await self.api.create_bill(bill_data)
            
            if result["success"]:
                bill = result["bill"]
                
                # Log the action
                with session_scope() as session:
                    append_ledger_entry(
                        session,
                        actor=self.actor,
                        action="create_bill_in_zoho",
                        data={
                            "bill_id": bill.get("bill_id"),
                            "vendor_id": vendor_id,
                            "amount": bill.get("total"),
                            "user_message": user_message,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
                
                logger.info(f"{self.actor}: Created bill of {bill.get('total', 0)} AED in Zoho Books")
                
                return {
                    "success": True,
                    "bill": {
                        "id": bill.get("bill_id"),
                        "number": bill.get("bill_number"),
                        "vendor": bill.get("vendor_name"),
                        "total": bill.get("total"),
                        "status": bill.get("status"),
                        "due_date": bill.get("due_date")
                    },
                    "message": f"Bill created successfully for {bill.get('total', 0)} AED"
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"{self.actor}: Error creating bill in Zoho: {e}")
            return {"success": False, "error": str(e)}

    async def record_payment_made_in_zoho(
        self,
        vendor_id: str,
        amount: float,
        payment_date: str = None,
        payment_mode: str = "bank_transfer",
        reference_number: str = None,
        notes: str = None,
        user_message: str = None
    ) -> Dict[str, Any]:
        """Record payment made to vendor in Zoho Books"""
        try:
            payment_data = {
                "vendor_id": vendor_id,
                "amount": str(amount),
                "payment_mode": payment_mode
            }
            
            if payment_date:
                payment_data["date"] = payment_date
            else:
                payment_data["date"] = datetime.now().strftime("%Y-%m-%d")
                
            if reference_number:
                payment_data["reference_number"] = reference_number
                
            if notes:
                payment_data["notes"] = notes
            
            result = await self.api.record_payment_made(payment_data)
            
            if result["success"]:
                payment = result["payment"]
                
                # Log the action
                with session_scope() as session:
                    append_ledger_entry(
                        session,
                        actor=self.actor,
                        action="record_payment_made",
                        data={
                            "payment_id": payment.get("payment_id"),
                            "vendor_id": vendor_id,
                            "amount": amount,
                            "user_message": user_message,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
                
                logger.info(f"{self.actor}: Recorded payment of {amount} AED to vendor in Zoho Books")
                
                return {
                    "success": True,
                    "payment": {
                        "id": payment.get("payment_id"),
                        "amount": payment.get("amount"),
                        "vendor": payment.get("vendor_name"),
                        "date": payment.get("date"),
                        "payment_mode": payment.get("payment_mode")
                    },
                    "message": f"Payment of {amount} AED recorded successfully"
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"{self.actor}: Error recording payment to vendor in Zoho: {e}")
            return {"success": False, "error": str(e)}

    # ITEMS & SERVICES MANAGEMENT
    
    async def create_service_item_in_zoho(
        self,
        item_name: str,
        description: str = None,
        rate: float = None,
        account_id: str = None,
        user_message: str = None
    ) -> Dict[str, Any]:
        """Create new service item in Zoho Books (for software development services)"""
        try:
            item_data = {
                "name": item_name,
                "item_type": "service"
            }
            
            if description:
                item_data["description"] = description
                
            if rate:
                item_data["rate"] = str(rate)
                
            if account_id:
                item_data["account_id"] = account_id
            else:
                # Use default income account for services
                item_data["account_id"] = "7244184000000000404"  # Sales account
            
            result = await self.api.create_item(item_data)
            
            if result["success"]:
                item = result["item"]
                
                # Log the action
                with session_scope() as session:
                    append_ledger_entry(
                        session,
                        actor=self.actor,
                        action="create_service_item",
                        data={
                            "item_id": item.get("item_id"),
                            "item_name": item_name,
                            "rate": rate,
                            "user_message": user_message,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
                
                logger.info(f"{self.actor}: Created service item '{item_name}' in Zoho Books")
                
                return {
                    "success": True,
                    "item": {
                        "id": item.get("item_id"),
                        "name": item.get("name"),
                        "description": item.get("description"),
                        "rate": item.get("rate"),
                        "item_type": item.get("item_type")
                    },
                    "message": f"Service item '{item_name}' created successfully"
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"{self.actor}: Error creating service item in Zoho: {e}")
            return {"success": False, "error": str(e)}

    async def get_items_from_zoho(self) -> Dict[str, Any]:
        """Get all items/services from Zoho Books"""
        try:
            result = await self.api.get_items()
            
            if result["success"]:
                items = result["items"]
                
                # Extract simplified item list
                item_list = []
                for item in items:
                    item_list.append({
                        "id": item.get("item_id"),
                        "name": item.get("name"),
                        "description": item.get("description"),
                        "rate": item.get("rate"),
                        "item_type": item.get("item_type"),
                        "status": item.get("status")
                    })
                
                logger.info(f"{self.actor}: Retrieved {len(item_list)} items from Zoho Books")
                return {
                    "success": True,
                    "items": item_list,
                    "total_count": len(item_list)
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"{self.actor}: Error getting items from Zoho: {e}")
            return {"success": False, "error": str(e)}

    async def create_software_development_packages(self) -> Dict[str, Any]:
        """Create standard software development service packages"""
        try:
            packages = [
                {
                    "name": "Web Application Development",
                    "description": "Full-stack web application development including frontend, backend, and database design",
                    "rate": 5000.0
                },
                {
                    "name": "Mobile App Development",
                    "description": "Native and cross-platform mobile application development for iOS and Android",
                    "rate": 7500.0
                },
                {
                    "name": "UI/UX Design Services",
                    "description": "Complete user interface and user experience design for web and mobile applications",
                    "rate": 3000.0
                },
                {
                    "name": "Software Consulting",
                    "description": "Technical consulting and architecture planning for software projects",
                    "rate": 1500.0
                },
                {
                    "name": "API Development & Integration",
                    "description": "Custom API development and third-party service integration",
                    "rate": 2500.0
                },
                {
                    "name": "Database Design & Optimization",
                    "description": "Database architecture design and performance optimization services",
                    "rate": 2000.0
                },
                {
                    "name": "DevOps & Deployment",
                    "description": "CI/CD pipeline setup, cloud deployment, and infrastructure management",
                    "rate": 3500.0
                },
                {
                    "name": "Software Maintenance & Support",
                    "description": "Ongoing maintenance, bug fixes, and technical support for existing software",
                    "rate": 1000.0
                }
            ]
            
            created_items = []
            for package in packages:
                result = await self.create_service_item_in_zoho(
                    item_name=package["name"],
                    description=package["description"],
                    rate=package["rate"],
                    user_message="Creating standard software development packages"
                )
                
                if result["success"]:
                    created_items.append(result["item"])
                else:
                    logger.warning(f"Failed to create package {package['name']}: {result.get('error', 'Unknown error')}")
            
            logger.info(f"{self.actor}: Created {len(created_items)} software development packages in Zoho Books")
            return {
                "success": True,
                "items_created": created_items,
                "total_created": len(created_items),
                "message": f"Created {len(created_items)} software development service packages"
            }
            
        except Exception as e:
            logger.error(f"{self.actor}: Error creating software development packages: {e}")
            return {"success": False, "error": str(e)}
    
    # INVOICE MANAGEMENT
    
    async def create_invoice_in_zoho(
        self,
        customer_id: str,
        line_items: List[Dict[str, Any]],
        invoice_date: str = None,
        due_date: str = None,
        notes: str = None,
        user_message: str = None
    ) -> Dict[str, Any]:
        """Create new invoice in Zoho Books"""
        try:
            invoice_data = {
                "customer_id": customer_id,
                "line_items": line_items
            }
            
            if invoice_date:
                invoice_data["date"] = invoice_date
            else:
                invoice_data["date"] = datetime.now().strftime("%Y-%m-%d")
            
            if due_date:
                invoice_data["due_date"] = due_date
            
            if notes:
                invoice_data["notes"] = notes
            
            result = await self.api.create_invoice(invoice_data)
            
            if result["success"]:
                invoice = result["invoice"]
                
                # Log the action
                with session_scope() as session:
                    append_ledger_entry(
                        session,
                        actor=self.actor,
                        action="create_invoice_in_zoho",
                        data={
                            "invoice_id": invoice.get("invoice_id"),
                            "invoice_number": invoice.get("invoice_number"),
                            "customer_id": customer_id,
                            "total": invoice.get("total"),
                            "user_message": user_message,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
                
                logger.info(f"{self.actor}: Created invoice {invoice.get('invoice_number')} in Zoho Books")
                
                return {
                    "success": True,
                    "invoice": {
                        "id": invoice.get("invoice_id"),
                        "number": invoice.get("invoice_number"),
                        "total": invoice.get("total"),
                        "status": invoice.get("status"),
                        "date": invoice.get("date"),
                        "due_date": invoice.get("due_date")
                    },
                    "message": f"Invoice {invoice.get('invoice_number')} created successfully"
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"{self.actor}: Error creating invoice in Zoho: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_invoice_in_zoho(self, invoice_id: str, user_message: str = None) -> Dict[str, Any]:
        """Send invoice to customer via Zoho Books"""
        try:
            result = await self.api.send_invoice(invoice_id)
            
            if result["success"]:
                # Log the action
                with session_scope() as session:
                    append_ledger_entry(
                        session,
                        actor=self.actor,
                        action="send_invoice_in_zoho",
                        data={
                            "invoice_id": invoice_id,
                            "user_message": user_message,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
                
                logger.info(f"{self.actor}: Sent invoice {invoice_id} via Zoho Books")
            
            return result
            
        except Exception as e:
            logger.error(f"{self.actor}: Error sending invoice in Zoho: {e}")
            return {"success": False, "error": str(e)}
    
    # EXPENSE MANAGEMENT
    
    async def create_expense_in_zoho(
        self,
        amount: float,
        description: str,
        account_id: str = None,
        vendor_id: str = None,
        expense_date: str = None,
        reference_number: str = None,
        user_message: str = None
    ) -> Dict[str, Any]:
        """Create new expense in Zoho Books"""
        try:
            # Use default expense account if none provided
            if not account_id:
                account_id = "7244184000000000400"  # Office Supplies account
            
            expense_data = {
                "amount": str(amount),  # Convert to string for Zoho API
                "description": description,
                "account_id": account_id
            }
            
            if expense_date:
                expense_data["date"] = expense_date
            else:
                expense_data["date"] = datetime.now().strftime("%Y-%m-%d")
            
            if vendor_id:
                expense_data["vendor_id"] = vendor_id
            
            if reference_number:
                expense_data["reference_number"] = reference_number
            
            result = await self.api.create_expense(expense_data)
            
            if result["success"]:
                expense = result["expense"]
                
                # Log the action
                with session_scope() as session:
                    append_ledger_entry(
                        session,
                        actor=self.actor,
                        action="create_expense_in_zoho",
                        data={
                            "expense_id": expense.get("expense_id"),
                            "amount": amount,
                            "description": description,
                            "account_id": account_id,
                            "user_message": user_message,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
                
                logger.info(f"{self.actor}: Created expense of {amount} AED in Zoho Books")
                
                return {
                    "success": True,
                    "expense": {
                        "id": expense.get("expense_id"),
                        "amount": expense.get("amount"),
                        "description": expense.get("description"),
                        "date": expense.get("date"),
                        "status": expense.get("status")
                    },
                    "message": f"Expense of {amount} AED created successfully"
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"{self.actor}: Error creating expense in Zoho: {e}")
            return {"success": False, "error": str(e)}
    
    async def record_expense_in_zoho(
        self,
        amount: float,
        description: str,
        account_id: str = None,
        vendor_id: str = None,
        expense_date: str = None,
        reference_number: str = None,
        user_message: str = None
    ) -> Dict[str, Any]:
        """Alias for create_expense_in_zoho - record an expense in Zoho Books"""
        return await self.create_expense_in_zoho(
            amount=amount,
            description=description,
            account_id=account_id,
            vendor_id=vendor_id,
            expense_date=expense_date,
            reference_number=reference_number,
            user_message=user_message
        )
    
    # JOURNAL ENTRIES
    
    async def create_journal_entry_in_zoho(
        self,
        journal_lines: List[Dict[str, Any]],
        entry_date: str = None,
        reference: str = None,
        notes: str = None,
        user_message: str = None
    ) -> Dict[str, Any]:
        """Create journal entry in Zoho Books"""
        try:
            journal_data = {
                "journal_date": entry_date or datetime.now().strftime("%Y-%m-%d"),
                "line_items": journal_lines
            }
            
            if reference:
                journal_data["reference_number"] = reference
            
            if notes:
                journal_data["notes"] = notes
            
            result = await self.api.create_journal_entry(journal_data)
            
            if result["success"]:
                journal = result["journal_entry"]
                
                # Log the action
                with session_scope() as session:
                    append_ledger_entry(
                        session,
                        actor=self.actor,
                        action="create_journal_entry_in_zoho",
                        data={
                            "journal_id": journal.get("journal_id"),
                            "reference": reference,
                            "lines_count": len(journal_lines),
                            "user_message": user_message,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
                
                logger.info(f"{self.actor}: Created journal entry in Zoho Books")
                
                return {
                    "success": True,
                    "journal_entry": {
                        "id": journal.get("journal_id"),
                        "reference": journal.get("reference_number"),
                        "date": journal.get("journal_date"),
                        "total": journal.get("total")
                    },
                    "message": "Journal entry created successfully"
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"{self.actor}: Error creating journal entry in Zoho: {e}")
            return {"success": False, "error": str(e)}
    
    # REPORTS AND ANALYTICS
    
    async def get_profit_loss_report(self, from_date: str, to_date: str) -> Dict[str, Any]:
        """Get Profit & Loss report from Zoho Books"""
        try:
            result = await self.api.get_profit_and_loss(from_date, to_date)
            
            if result["success"]:
                report = result["report"]
                logger.info(f"{self.actor}: Retrieved P&L report for {from_date} to {to_date}")
                
                return {
                    "success": True,
                    "report_data": report,
                    "period": f"{from_date} to {to_date}",
                    "message": f"P&L report generated for {from_date} to {to_date}"
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"{self.actor}: Error getting P&L report from Zoho: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_balance_sheet_report(self, as_of_date: str) -> Dict[str, Any]:
        """Get Balance Sheet report from Zoho Books"""
        try:
            result = await self.api.get_balance_sheet(as_of_date)
            
            if result["success"]:
                report = result["report"]
                logger.info(f"{self.actor}: Retrieved Balance Sheet as of {as_of_date}")
                
                return {
                    "success": True,
                    "report_data": report,
                    "as_of_date": as_of_date,
                    "message": f"Balance Sheet generated as of {as_of_date}"
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"{self.actor}: Error getting Balance Sheet from Zoho: {e}")
            return {"success": False, "error": str(e)}
    
    # ACCOUNT MANAGEMENT
    
    async def get_chart_of_accounts(self) -> Dict[str, Any]:
        """Get chart of accounts from Zoho Books"""
        try:
            result = await self.api.get_chart_of_accounts()
            
            if result["success"]:
                accounts = result["accounts"]
                
                # Extract simplified account list
                account_list = []
                for account in accounts:
                    account_list.append({
                        "id": account.get("account_id"),
                        "name": account.get("account_name"),
                        "type": account.get("account_type"),
                        "balance": account.get("balance", 0),
                        "is_active": account.get("is_active", True)
                    })
                
                logger.info(f"{self.actor}: Retrieved {len(account_list)} accounts from Zoho Books")
                return {
                    "success": True,
                    "accounts": account_list,
                    "total_count": len(account_list)
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"{self.actor}: Error getting chart of accounts from Zoho: {e}")
            return {"success": False, "error": str(e)}
    
    # UTILITY METHODS
    
    async def get_organization_info(self) -> Dict[str, Any]:
        """Get organization information from Zoho Books"""
        try:
            result = await self.get_company_profile_from_zoho()
            
            if result["success"]:
                company_info = result["company_info"]
                
                return {
                    "success": True,
                    "organization": company_info,
                    "message": "Organization information retrieved from Zoho Books"
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"{self.actor}: Error getting organization info from Zoho: {e}")
            return {"success": False, "error": str(e)}

    # PROJECT MANAGEMENT
    
    async def get_projects_from_zoho(self) -> Dict[str, Any]:
        """Get list of projects from Zoho Books"""
        try:
            from .zoho_books_api import zoho_books_api
            
            result = await zoho_books_api.get_projects()
            
            if result.get("message") == "success":
                projects = result.get("projects", [])
                
                # Format projects for agent consumption
                formatted_projects = []
                for project in projects:
                    formatted_project = {
                        "id": project.get("project_id"),
                        "name": project.get("project_name"),
                        "status": project.get("status", "unknown"),
                        "customer_id": project.get("customer_id"),
                        "customer_name": project.get("customer_name"),
                        "description": project.get("description", ""),
                        "billing_type": project.get("billing_type", ""),
                        "budget": project.get("budget", 0),
                        "created_time": project.get("created_time", ""),
                        "budget_threshold": project.get("budget_threshold", 0)
                    }
                    formatted_projects.append(formatted_project)
                
                # Log success
                await self._log_ledger_entry(
                    "get_projects_from_zoho",
                    f"Retrieved {len(formatted_projects)} projects from Zoho Books",
                    0.0,
                    "AED",
                    {"projects_count": len(formatted_projects)}
                )
                
                logger.info(f"{self.actor}: Retrieved {len(formatted_projects)} projects from Zoho Books")
                
                return {
                    "success": True,
                    "projects": formatted_projects,
                    "total_count": len(formatted_projects),
                    "message": f"Retrieved {len(formatted_projects)} projects from Zoho Books"
                }
                
            else:
                return {
                    "success": False,
                    "error": result.get("message", "Unknown error"),
                    "projects": []
                }
                
        except Exception as e:
            logger.error(f"{self.actor}: Error getting projects from Zoho: {e}")
            return {"success": False, "error": str(e), "projects": []}
    
    async def create_project_in_zoho(
        self,
        project_name: str,
        customer_id: str,
        billing_type: str = "based_on_project_hours",
        description: str = None,
        budget: float = None,
        user_message: str = None
    ) -> Dict[str, Any]:
        """Create new project in Zoho Books"""
        try:
            from .zoho_books_api import zoho_books_api
            
            project_data = {
                "project_name": project_name,
                "customer_id": customer_id,
                "billing_type": billing_type
            }
            
            if description:
                project_data["description"] = description
                
            if budget:
                project_data["budget"] = budget
            
            result = await zoho_books_api.create_project(project_data)
            
            if result.get("message") == "success":
                project = result.get("project", {})
                
                # Log success
                await self._log_ledger_entry(
                    "create_project_in_zoho",
                    f"Created project '{project_name}' in Zoho Books",
                    budget or 0.0,
                    "AED",
                    {
                        "project_id": project.get("project_id"),
                        "project_name": project_name,
                        "customer_id": customer_id,
                        "billing_type": billing_type,
                        "user_message": user_message
                    }
                )
                
                logger.info(f"{self.actor}: Created project '{project_name}' in Zoho Books")
                
                return {
                    "success": True,
                    "project": {
                        "id": project.get("project_id"),
                        "name": project.get("project_name"),
                        "status": project.get("status"),
                        "customer_id": project.get("customer_id"),
                        "billing_type": project.get("billing_type"),
                        "budget": project.get("budget", 0)
                    },
                    "message": f"Project '{project_name}' created successfully"
                }
                
            else:
                return {
                    "success": False,
                    "error": result.get("message", "Unknown error")
                }
                
        except Exception as e:
            logger.error(f"{self.actor}: Error creating project in Zoho: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_time_entries_from_zoho(self, project_id: str = None) -> Dict[str, Any]:
        """Get time entries from Zoho Books"""
        try:
            from .zoho_books_api import zoho_books_api
            
            result = await zoho_books_api.get_time_entries(project_id=project_id)
            
            if result.get("message") == "success":
                time_entries = result.get("time_entries", [])
                
                # Format time entries for agent consumption
                formatted_entries = []
                for entry in time_entries:
                    formatted_entry = {
                        "id": entry.get("time_entry_id"),
                        "project_id": entry.get("project_id"),
                        "project_name": entry.get("project_name"),
                        "user_name": entry.get("user_name"),
                        "log_date": entry.get("log_date"),
                        "log_time": entry.get("log_time"),
                        "billed_hours": entry.get("billed_hours", 0),
                        "notes": entry.get("notes", ""),
                        "is_billable": entry.get("is_billable", False)
                    }
                    formatted_entries.append(formatted_entry)
                
                # Log success
                await self._log_ledger_entry(
                    "get_time_entries_from_zoho",
                    f"Retrieved {len(formatted_entries)} time entries from Zoho Books",
                    0.0,
                    "AED",
                    {"time_entries_count": len(formatted_entries), "project_id": project_id}
                )
                
                logger.info(f"{self.actor}: Retrieved {len(formatted_entries)} time entries from Zoho Books")
                
                return {
                    "success": True,
                    "time_entries": formatted_entries,
                    "total_count": len(formatted_entries),
                    "message": f"Retrieved {len(formatted_entries)} time entries from Zoho Books"
                }
                
            else:
                return {
                    "success": False,
                    "error": result.get("message", "Unknown error"),
                    "time_entries": []
                }
                
        except Exception as e:
            logger.error(f"{self.actor}: Error getting time entries from Zoho: {e}")
            return {"success": False, "error": str(e), "time_entries": []}
    
    # CONVENIENCE METHODS FOR BACKWARD COMPATIBILITY
    
    async def get_customers(self) -> Dict[str, Any]:
        """Get customers (compatibility method)"""
        return await self.get_customers_from_zoho()
    
    async def get_items(self) -> Dict[str, Any]:
        """Get items (compatibility method)"""
        return await self.get_items_from_zoho()
    
    async def create_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new item in Zoho Books"""
        try:
            result = await self.api.create_item(item_data)
            
            if result.get("message") == "The item has been created.":
                item = result.get("item", {})
                
                # Log success
                await self._log_ledger_entry(
                    "create_item",
                    f"Created item: {item_data.get('name', 'Unknown')}",
                    0.0,
                    "AED",
                    {"item_id": item.get("item_id"), "item_name": item_data.get("name")}
                )
                
                logger.info(f"{self.actor}: Created item {item_data.get('name', 'Unknown')} in Zoho Books")
                
                return {
                    "success": True,
                    "item": item,
                    "message": "Item created successfully"
                }
            else:
                return {
                    "success": False,
                    "error": result.get("message", "Unknown error"),
                    "item": None
                }
                
        except Exception as e:
            logger.error(f"{self.actor}: Error creating item: {e}")
            return {"success": False, "error": str(e), "item": None}