"""
AI Service Integration for CMP Agent Responses

Provides real AI-powered responses using OpenAI GPT models for intelligent
financial agent conversations and task processing.
"""

import os
import re
import json
from typing import Dict, List, Optional, Any
import openai
from openai import OpenAI
import asyncio
from datetime import datetime, timedelta, timedelta
from ..config import settings
from ..logging_config import get_logger
from ..db import session_scope
from ..models import LedgerEntry, Company
from .agent_db_tools import AgentDatabaseTools
from .agent_zoho_tools import AgentZohoBooks

logger = get_logger("ai_service")


class AIAgentService:
    """
    Real AI service for generating intelligent agent responses using OpenAI GPT models.
    Includes database modification capabilities for updating company information.
    """
    
    def __init__(self):
        self.client = None
        self.model = "gpt-3.5-turbo"  # Default model
        self.db_tools = {}  # Store per-agent database tools
        self.zoho_tools = {}  # Store per-agent Zoho Books tools
        self._initialize_client()
    
    def _get_db_tools(self, agent_type: str) -> AgentDatabaseTools:
        """Get or create database tools for a specific agent"""
        if agent_type not in self.db_tools:
            self.db_tools[agent_type] = AgentDatabaseTools(agent_type)
        return self.db_tools[agent_type]
    
    def _get_zoho_tools(self, agent_type: str) -> AgentZohoBooks:
        """Get or create Zoho Books tools for a specific agent"""
        if agent_type not in self.zoho_tools:
            self.zoho_tools[agent_type] = AgentZohoBooks(agent_type)
        return self.zoho_tools[agent_type]
    
    def _initialize_client(self):
        """Initialize OpenAI client if API key is available"""
        api_key = settings.openai_api_key
        
        if not api_key or api_key == "your_openai_api_key":
            logger.warning("OpenAI API key not configured. Using fallback responses.")
            return
        
        try:
            self.client = OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
    
    async def generate_agent_response(
        self, 
        agent_type: str, 
        message: str, 
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate an intelligent response for a specific agent type
        
        Args:
            agent_type: Type of agent (accountant, cfo, controller, director)
            message: User's message/question
            context: Additional context like agent status, KPIs, etc.
            
        Returns:
            Dict containing response message, type, and suggestions
        """
        
        if not self.client:
            return self._get_fallback_response(agent_type, message)
        
        try:
            # Get comprehensive company and financial context
            company_context = await self._get_company_context()
            
            # Create agent-specific system prompt with real company data
            system_prompt = self._get_system_prompt(agent_type, context, company_context)
            
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=400,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Structure the response
            return {
                "message": ai_response,
                "type": "ai_response",
                "suggestions": self._generate_suggestions(agent_type, message),
                "powered_by": "OpenAI GPT"
            }
            
        except Exception as e:
            logger.error(f"AI response generation failed: {e}")
            return self._get_fallback_response(agent_type, message)
    
    async def process_message_with_db_updates(
        self, 
        agent_type: str, 
        message: str, 
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Process a message that might contain database update requests and Zoho Books operations
        
        Args:
            agent_type: Type of agent processing the message
            message: User's message that might contain update instructions
            context: Additional context
            
        Returns:
            Dict with response and any database updates/Zoho operations performed
        """
        
        # Check if message contains database update requests
        db_updates = await self._detect_and_process_db_updates(agent_type, message)
        
        # Check if message contains Zoho Books operations
        zoho_operations = await self._detect_and_process_zoho_operations(agent_type, message)
        
        # Generate the regular AI response
        ai_response = await self.generate_agent_response(agent_type, message, context)
        
        # Combine results
        updates_summary = []
        if db_updates:
            updates_summary.append(self._summarize_db_updates(db_updates))
            ai_response["db_updates"] = db_updates
        
        if zoho_operations:
            updates_summary.append(self._summarize_zoho_operations(zoho_operations))
            ai_response["zoho_operations"] = zoho_operations
        
        if updates_summary:
            combined_summary = "\n".join(updates_summary)
            ai_response["message"] = f"{combined_summary}\n\n{ai_response['message']}"
            ai_response["type"] = "ai_response_with_operations"
        
        return ai_response
    
    async def _detect_and_process_db_updates(self, agent_type: str, message: str) -> List[Dict[str, Any]]:
        """
        Detect and process database update requests in user messages
        
        Args:
            agent_type: Type of agent processing the message
            message: User message to analyze
            
        Returns:
            List of database update results
        """
        
        db_tools = self._get_db_tools(agent_type)
        updates = []
        
        try:
            # Pattern matching for common update requests
            message_lower = message.lower()
            
            # VAT/TRN updates
            trn_patterns = [
                r"(?:our\s+)?(?:vat\s+)?(?:trn|tax\s+registration\s+number)\s+(?:is\s+)?(?:now\s+)?([a-z0-9\-]+)",
                r"(?:update|change|set)\s+(?:our\s+)?(?:vat\s+)?(?:trn|tax\s+registration\s+number)\s+(?:to\s+)?([a-z0-9\-]+)",
                r"(?:we\s+(?:got|received|have)\s+(?:our\s+)?(?:vat\s+)?(?:trn|tax\s+registration\s+number))\s*:?\s*([a-z0-9\-]+)"
            ]
            
            for pattern in trn_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    trn = match.group(1).upper()
                    result = await db_tools.update_vat_registration(trn=trn, registered=True)
                    if result["success"]:
                        updates.append({
                            "type": "vat_registration",
                            "action": "update_trn",
                            "value": trn,
                            "result": result
                        })
                    break
            
            # Corporate tax number updates
            corp_tax_patterns = [
                r"(?:our\s+)?(?:corporate\s+)?tax\s+number\s+(?:is\s+)?(?:now\s+)?([a-z0-9\-]+)",
                r"(?:update|change|set)\s+(?:our\s+)?(?:corporate\s+)?tax\s+number\s+(?:to\s+)?([a-z0-9\-]+)",
                r"(?:corporate\s+tax\s+number)\s+(?:to\s+)?([a-z0-9\-]+)"
            ]
            
            for pattern in corp_tax_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    tax_number = match.group(1).upper()
                    result = await db_tools.update_corporate_tax_registration(tax_number=tax_number, registered=True)
                    if result["success"]:
                        updates.append({
                            "type": "corporate_tax",
                            "action": "update_tax_number",
                            "value": tax_number,
                            "result": result
                        })
                    break
            
            # Trade license updates
            license_patterns = [
                r"(?:our\s+)?(?:trade\s+)?licen[cs]e\s+(?:number\s+)?(?:is\s+)?(?:now\s+)?([a-z0-9\-]+)",
                r"(?:update|change|set)\s+(?:our\s+)?(?:trade\s+)?licen[cs]e\s+(?:number\s+)?(?:to\s+)?([a-z0-9\-]+)",
                r"(?:trade\s+license\s+number)\s+(?:to\s+)?([a-z0-9\-]+)"
            ]
            
            for pattern in license_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    license_number = match.group(1).upper()
                    result = await db_tools.update_trade_license(license_number=license_number)
                    if result["success"]:
                        updates.append({
                            "type": "trade_license",
                            "action": "update_license_number",
                            "value": license_number,
                            "result": result
                        })
                    break
            
            # Company name updates
            company_name_patterns = [
                r"(?:our\s+)?(?:company\s+)?(?:legal\s+)?name\s+(?:is\s+)?(?:now\s+)?['\"]([^'\"]+)['\"]",
                r"(?:update|change|set)\s+(?:our\s+)?(?:company\s+)?(?:legal\s+)?name\s+(?:to\s+)?['\"]([^'\"]+)['\"]",
                r"(?:we\s+(?:are\s+)?(?:now\s+)?(?:called|named))\s+['\"]([^'\"]+)['\"]"
            ]
            
            for pattern in company_name_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    company_name = match.group(1).strip()
                    result = await db_tools.update_company_field("legal_name", company_name, message)
                    if result["success"]:
                        updates.append({
                            "type": "company_info",
                            "action": "update_legal_name",
                            "value": company_name,
                            "result": result
                        })
                    break
            
            # Address updates (basic)
            address_patterns = [
                r"(?:our\s+)?(?:office\s+)?address\s+(?:is\s+)?(?:now\s+)?['\"]([^'\"]+)['\"]",
                r"(?:we\s+(?:moved|relocated)\s+to)\s+['\"]([^'\"]+)['\"]",
                r"(?:moved\s+to)\s+['\"]([^'\"]+)['\"]",
                r"(?:address\s+(?:is\s+)?(?:now\s+)?)['\"]([^'\"]+)['\"]"
            ]
            
            for pattern in address_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    address = match.group(1).strip()
                    result = await db_tools.update_company_field("address_line_1", address, message)
                    if result["success"]:
                        updates.append({
                            "type": "company_info",
                            "action": "update_address",
                            "value": address,
                            "result": result
                        })
                    break
            
        except Exception as e:
            logger.error(f"Error processing database updates: {e}")
        
        return updates
    
    async def _detect_and_process_zoho_operations(self, agent_type: str, message: str) -> List[Dict[str, Any]]:
        """
        Detect and process Zoho Books operations in user messages
        
        Args:
            agent_type: Type of agent processing the message
            message: User message to analyze
            
        Returns:
            List of Zoho operations performed
        """
        
        zoho_tools = self._get_zoho_tools(agent_type)
        operations = []
        
        try:
            message_lower = message.lower()
            
            # Sync company profile to Zoho
            sync_patterns = [
                r"sync.*(?:company|profile|organization)",
                r"update.*(?:company|profile|organization).*(?:in\s+)?zoho",
                r"show.*(?:current|our).*(?:company|profile|organization)",
                r"get.*(?:company|profile|organization).*profile"
            ]
            
            for pattern in sync_patterns:
                if re.search(pattern, message_lower):
                    result = await zoho_tools.sync_company_profile_to_zoho(message)
                    if result["success"]:
                        operations.append({
                            "type": "sync_profile",
                            "action": "sync_company_profile_to_zoho",
                            "result": result
                        })
                    break
            
            # Get/List customers
            customer_list_patterns = [
                r"(?:list|show|get|display).*customers",
                r"customers.*(?:list|overview|summary)",
                r"who.*(?:are|our).*customers",
                r"show.*(?:all|existing).*customers"
            ]
            
            for pattern in customer_list_patterns:
                if re.search(pattern, message_lower):
                    result = await zoho_tools.get_customers_from_zoho()
                    if result["success"]:
                        operations.append({
                            "type": "customer_management",
                            "action": "get_customers",
                            "result": result
                        })
                    break
            
            # Create customer - improved patterns
            customer_patterns = [
                r"(?:create|add|new).*customer.*(?:named|called)\s+([a-zA-Z0-9\s&\-.,]+?)(?:\s+with|\s*$)",
                r"(?:create|add|new).*customer\s+([a-zA-Z0-9\s&\-.,]+?)(?:\s+with|\s*$)",
                r"customer.*(?:named|called)\s+([a-zA-Z0-9\s&\-.,]+?)(?:\s+with|\s*$)"
            ]
            
            for pattern in customer_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    customer_name = match.group(1).strip()
                    # Extract email if present
                    email_match = re.search(r"email[:\s]+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", message_lower)
                    email = email_match.group(1) if email_match else None
                    
                    result = await zoho_tools.create_customer_in_zoho(customer_name, email=email, user_message=message)
                    if result["success"]:
                        operations.append({
                            "type": "customer_management",
                            "action": "create_customer",
                            "value": customer_name,
                            "result": result
                        })
                    break

            # Quote management
            quote_patterns = [
                r"(?:create|generate|prepare).*quote.*(?:for\s+)?([a-zA-Z0-9\s&\-.,]+?)(?:\s+for\s+|\s+amount\s+|\s*$)",
                r"quote.*(?:for\s+)?([a-zA-Z0-9\s&\-.,]+?)(?:\s+for\s+|\s+amount\s+|\s*$)",
                r"estimate.*(?:for\s+)?([a-zA-Z0-9\s&\-.,]+?)(?:\s+for\s+|\s+amount\s+|\s*$)"
            ]
            
            for pattern in quote_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    customer_name = match.group(1).strip()
                    # Extract amount if present
                    amount_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:aed|dirham|dollar)", message_lower)
                    amount = float(amount_match.group(1)) if amount_match else None
                    
                    # For now, acknowledge quote request (would need customer ID lookup)
                    operations.append({
                        "type": "sales_management",
                        "action": "create_quote_requested",
                        "value": f"Quote for {customer_name}" + (f" - {amount} AED" if amount else ""),
                        "result": {"success": True, "message": f"Quote request for {customer_name} noted"}
                    })
                    break
            
            # Create invoice in Zoho - improved patterns
            invoice_patterns = [
                r"(?:create|generate|make).*invoice.*(?:for\s+)?([a-zA-Z0-9\s&\-.,]+?)(?:\s+for\s+|\s+amount\s+|\s*$)",
                r"invoice\s+([a-zA-Z0-9\s&\-.,]+?)(?:\s+for\s+|\s+amount\s+|\s*$)"
            ]
            
            for pattern in invoice_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    customer_name = match.group(1).strip()
                    # Extract amount if present
                    amount_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:aed|dirham|dollar)", message_lower)
                    amount = float(amount_match.group(1)) if amount_match else None
                    
                    result = await zoho_tools.create_invoice_in_zoho(customer_name, amount=amount, user_message=message)
                    if result["success"]:
                        operations.append({
                            "type": "invoice_management",
                            "action": "create_invoice",
                            "value": customer_name,
                            "result": result
                        })
                    break
            
            # Create expense in Zoho - improved patterns
            expense_patterns = [
                r"(?:record|add|create|enter).*expense.*?(?:of\s+)(\d+(?:\.\d+)?)\s*(?:aed|dirham|dollar)\s*(?:for\s+)?(.+?)(?:\s*$)",
                r"expense.*?(?:of\s+)(\d+(?:\.\d+)?)\s*(?:aed|dirham|dollar)\s*(?:for\s+)?(.+?)(?:\s*$)",
                r"spent.*?(\d+(?:\.\d+)?)\s*(?:aed|dirham|dollar)\s*(?:on|for)\s+(.+?)(?:\s*$)"
            ]
            
            for pattern in expense_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    amount = float(match.group(1))
                    description = match.group(2).strip()
                    
                    result = await zoho_tools.record_expense_in_zoho(amount, description, user_message=message)
                    if result["success"]:
                        operations.append({
                            "type": "expense_management",
                            "action": "record_expense",
                            "value": f"{amount} AED - {description}",
                            "result": result
                        })
                    break

            # Financial reports
            report_patterns = [
                r"(?:get|show|generate|display).*(?:profit.*loss|p&l).*(?:report|summary|statement)",
                r"(?:get|show|generate|display).*balance.*sheet",
                r"(?:get|show|generate|display).*(?:financial|report|statement)",
                r"(?:profit|loss|financial).*(?:report|summary|statement)",
                r"how.*(?:business|company).*(?:doing|performing)",
                r"financial.*(?:overview|summary|status)"
            ]
            
            for pattern in report_patterns:
                if re.search(pattern, message_lower):
                    # Determine date range
                    if "this month" in message_lower:
                        from_date = datetime.now().replace(day=1).strftime("%Y-%m-%d")
                        to_date = datetime.now().strftime("%Y-%m-%d")
                    elif "last month" in message_lower:
                        last_month = datetime.now().replace(day=1) - timedelta(days=1)
                        from_date = last_month.replace(day=1).strftime("%Y-%m-%d")
                        to_date = last_month.strftime("%Y-%m-%d")
                    else:
                        # Default: current year to date
                        from_date = datetime.now().replace(month=1, day=1).strftime("%Y-%m-%d")
                        to_date = datetime.now().strftime("%Y-%m-%d")
                    
                    result = await zoho_tools.get_profit_loss_report(from_date, to_date)
                    if result["success"]:
                        operations.append({
                            "type": "financial_reporting",
                            "action": "generate_report",
                            "value": f"Profit & Loss Report ({from_date} to {to_date})",
                            "result": result
                        })
                    break

            # Payment recording
            payment_patterns = [
                r"(?:record|received|got).*payment.*(?:of\s+)?(\d+(?:\.\d+)?)\s*(?:aed|dirham|dollar).*(?:from\s+)?(.+?)(?:\s*$)",
                r"payment.*(?:of\s+)?(\d+(?:\.\d+)?)\s*(?:aed|dirham|dollar).*(?:from\s+)?(.+?)(?:\s*$)",
                r"customer.*paid.*(\d+(?:\.\d+)?)\s*(?:aed|dirham|dollar)"
            ]
            
            for pattern in payment_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    amount = float(match.group(1))
                    customer_name = match.group(2).strip() if len(match.groups()) > 1 else "Unknown Customer"
                    
                    # For now, acknowledge payment (would need customer ID lookup)
                    operations.append({
                        "type": "payment_management",
                        "action": "record_payment_received",
                        "value": f"{amount} AED from {customer_name}",
                        "result": {"success": True, "message": f"Payment of {amount} AED from {customer_name} recorded"}
                    })
                    break
            
        except Exception as e:
            logger.error(f"Error processing Zoho operations for {agent_type}: {e}")
        
        return operations
    
    def _summarize_zoho_operations(self, operations: List[Dict[str, Any]]) -> str:
        """
        Create a summary message for Zoho Books operations performed
        
        Args:
            operations: List of operation results
            
        Returns:
            Summary message
        """
        
        if not operations:
            return ""
        
        summaries = []
        for operation in operations:
            if operation["result"]["success"]:
                if operation["type"] == "sync_profile":
                    summaries.append("✅ Synced company profile to Zoho Books")
                elif operation["type"] == "customer_management":
                    summaries.append(f"✅ Created customer in Zoho Books: {operation['value']}")
                elif operation["type"] == "invoice_management":
                    summaries.append(f"✅ Invoice creation requested for: {operation['value']}")
                elif operation["type"] == "expense_management":
                    summaries.append(f"✅ Expense recorded: {operation['value']}")
                elif operation["type"] == "reporting":
                    summaries.append("✅ Financial report generation initiated")
            else:
                summaries.append(f"❌ Failed Zoho operation: {operation['result'].get('error', 'Unknown error')}")
        
        if summaries:
            return "Zoho Books Operations:\n" + "\n".join(summaries)
        
        return ""
    
    def _summarize_db_updates(self, updates: List[Dict[str, Any]]) -> str:
        """
        Create a summary message for database updates performed
        
        Args:
            updates: List of update results
            
        Returns:
            Summary message
        """
        
        if not updates:
            return ""
        
        summaries = []
        for update in updates:
            if update["result"]["success"]:
                if update["type"] == "vat_registration":
                    summaries.append(f"✅ Updated VAT TRN to: {update['value']}")
                elif update["type"] == "corporate_tax":
                    summaries.append(f"✅ Updated Corporate Tax Number to: {update['value']}")
                elif update["type"] == "trade_license":
                    summaries.append(f"✅ Updated Trade License Number to: {update['value']}")
                elif update["type"] == "company_info":
                    if update["action"] == "update_legal_name":
                        summaries.append(f"✅ Updated Company Name to: {update['value']}")
                    elif update["action"] == "update_address":
                        summaries.append(f"✅ Updated Company Address to: {update['value']}")
            else:
                summaries.append(f"❌ Failed to update {update['type']}: {update['result'].get('error', 'Unknown error')}")
        
        if summaries:
            return "I've updated our company information:\n" + "\n".join(summaries)
        
        return ""
    
    async def _get_company_context(self) -> Dict[str, Any]:
        """Gather comprehensive company and financial context from available data sources"""
        try:
            # Initialize with defaults
            context = {
                "company": {
                    "name": "CMP Financial Services",
                    "country": "United Arab Emirates",
                    "business_type": "Financial Management Platform",
                    "vat_registered": False,
                    "vat_threshold_aed": 375000,  # UAE VAT threshold
                    "established": "2024",
                    "currency": "AED"
                },
                "financial": {
                    "current_revenue_ytd": 0,
                    "current_expenses_ytd": 0,
                    "projected_annual_revenue": 1500000,
                    "last_transaction_date": None,
                    "bank_balance": 0,
                    "active_accounts": 1
                },
                "operations": {
                    "total_transactions_processed": 0,
                    "invoices_processed_ytd": 0,
                    "last_reconciliation": None,
                    "ai_categorizations_count": 0,
                    "integration_status": "active"
                },
                "compliance": {
                    "vat_registration_required": False,
                    "next_vat_review_date": None,
                    "compliance_score": "Good",
                    "last_audit": None
                }
            }
            
            # Try to get actual company data from database
            try:
                with session_scope() as session:
                    # Get actual company information
                    company = session.query(Company).first()
                    if company:
                        context["company"].update({
                            "name": company.legal_name or company.trade_name or "CMP Financial Services",
                            "legal_name": company.legal_name,
                            "trade_name": company.trade_name,
                            "business_type": company.business_type or "Financial Management Platform",
                            "vat_registered": company.vat_registered or False,
                            "vat_registration_number": company.vat_registration_number,
                            "vat_registration_date": company.vat_registration_date.isoformat() if company.vat_registration_date else None,
                            "corporate_tax_registered": company.corporate_tax_registered or False,
                            "corporate_tax_number": company.corporate_tax_number,
                            "trade_license_number": company.trade_license_number,
                            "trade_license_authority": company.trade_license_authority,
                            "trade_license_expiry_date": company.trade_license_expiry_date.isoformat() if company.trade_license_expiry_date else None,
                            "primary_activity": company.primary_activity.value if company.primary_activity else None,
                            "city": company.city or "Dubai",
                            "emirate": company.emirate or "Dubai",
                            "country": company.country or "United Arab Emirates",
                            "currency": company.currency or "AED"
                        })
                        
                        # Update compliance status based on actual data
                        if company.vat_registered:
                            context["compliance"]["compliance_score"] = "Excellent"
                        
                        # Check if trade license is expiring soon
                        if company.trade_license_expiry_date:
                            days_to_expiry = (company.trade_license_expiry_date - datetime.now().date()).days
                            if days_to_expiry < 90:
                                context["compliance"]["compliance_score"] = "Attention Required"
                                context["compliance"]["next_review_reason"] = f"Trade license expires in {days_to_expiry} days"
                    
                    # Get recent ledger entries for activity context
                    from sqlalchemy import select, func
                    recent_entries = session.execute(
                        select(LedgerEntry)
                        .where(LedgerEntry.timestamp >= datetime.now() - timedelta(days=30))
                        .order_by(LedgerEntry.timestamp.desc())
                        .limit(10)
                    ).scalars().all()
                    
                    if recent_entries:
                        context["operations"]["total_transactions_processed"] = len(recent_entries)
                        context["operations"]["last_reconciliation"] = recent_entries[0].timestamp.date().isoformat()
                        
                        # Count different types of activities
                        invoice_count = sum(1 for entry in recent_entries if "invoice" in entry.action.lower())
                        context["operations"]["invoices_processed_ytd"] = invoice_count
                        
                        # Estimate revenue from transaction activity (simplified)
                        if len(recent_entries) > 5:
                            estimated_monthly = len(recent_entries) * 5000  # Rough estimate
                            context["financial"]["current_revenue_ytd"] = estimated_monthly * 9  # 9 months estimated
                            
                            # Check if approaching VAT threshold
                            if context["financial"]["current_revenue_ytd"] > 300000:  # 80% of threshold
                                context["compliance"]["vat_registration_required"] = True
                                context["compliance"]["next_vat_review_date"] = (datetime.now() + timedelta(days=30)).date().isoformat()
                    
            except Exception as e:
                logger.warning(f"Could not fetch database context: {e}")
                # Continue with default context
            
            # Add current date context
            context["system"] = {
                "current_date": datetime.now().date().isoformat(),
                "current_month": datetime.now().strftime("%B %Y"),
                "quarter": f"Q{(datetime.now().month - 1) // 3 + 1} {datetime.now().year}",
                "fiscal_year": str(datetime.now().year)
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Error gathering company context: {e}")
            # Return minimal context
            return {
                "company": {"name": "CMP Financial Services", "country": "UAE", "currency": "AED"},
                "system": {"current_date": datetime.now().date().isoformat()}
            }
    
    def _get_system_prompt(self, agent_type: str, context: Dict[str, Any] = None, company_context: Dict[str, Any] = None) -> str:
        """Generate system prompt for specific agent type with real company context"""
        
        # Extract company information
        company_info = company_context.get("company", {}) if company_context else {}
        financial_info = company_context.get("financial", {}) if company_context else {}
        operations_info = company_context.get("operations", {}) if company_context else {}
        compliance_info = company_context.get("compliance", {}) if company_context else {}
        system_info = company_context.get("system", {}) if company_context else {}
        
        company_name = company_info.get("name", "CMP Financial Services")
        current_date = system_info.get("current_date", datetime.now().date().isoformat())
        
        base_context = f"""
You are an AI-powered {agent_type.title()} for {company_name}, a comprehensive financial management platform based in the {company_info.get("country", "UAE")}.

COMPANY CONTEXT:
- Business: {company_info.get("business_type", "Financial Management Platform")}
- Currency: {company_info.get("currency", "AED")}
- Current Date: {current_date}
- Fiscal Year: {system_info.get("fiscal_year", "2024")}

CURRENT FINANCIAL STATUS:
- YTD Revenue: {financial_info.get("current_revenue_ytd", 0):,.0f} AED
- Projected Annual: {financial_info.get("projected_annual_revenue", 0):,.0f} AED
- Bank Balance: {financial_info.get("bank_balance", 0):,.0f} AED
- Active Accounts: {financial_info.get("active_accounts", 1)}

OPERATIONAL METRICS:
- Transactions Processed: {operations_info.get("total_transactions_processed", 0)}
- Invoices YTD: {operations_info.get("invoices_processed_ytd", 0)}
- Last Reconciliation: {operations_info.get("last_reconciliation", "N/A")}

VAT & COMPLIANCE:
- VAT Registered: {"Yes" if company_info.get("vat_registered", False) else "No"}
- VAT Threshold (UAE): {company_info.get("vat_threshold_aed", 375000):,.0f} AED
- Registration Required: {"Yes" if compliance_info.get("vat_registration_required", False) else "No"}
- Next Review: {compliance_info.get("next_vat_review_date", "Not scheduled")}

You should provide helpful, professional, and actionable responses specifically related to YOUR ROLE and OUR COMPANY'S situation.
Keep responses concise but informative (2-3 sentences max).
Be friendly and conversational while maintaining professionalism.
Always reference our actual business context and financial situation when relevant.

ZOHO BOOKS INTEGRATION:
You have full access to Zoho Books API and can perform real bookkeeping operations including:
- Creating and managing customers, vendors, and invoices
- Recording expenses and journal entries  
- Generating financial reports (P&L, Balance Sheet, Trial Balance)
- Managing chart of accounts and bank transactions
- Syncing company profile data between CMP and Zoho Books
- UAE VAT compliance and tax management

WHEN TO USE ZOHO BOOKS:
- User asks you to create customers, invoices, or record expenses
- User requests financial reports or account information
- User wants to sync company data or update Zoho Books profile
- User mentions specific bookkeeping tasks or operations
- You need to perform actual accounting transactions (not just discuss them)

EXAMPLE ZOHO OPERATIONS:
- "Create customer 'ABC Company' in Zoho Books"
- "Record expense of 1500 AED for office supplies"
- "Generate P&L report for this quarter"
- "Sync our company profile to Zoho Books"
- "Create invoice for customer XYZ"
"""
        
        role_prompts = {
            "accountant": f"""
YOUR SPECIALTIES:
- Transaction categorization and processing for {company_name}
- Invoice processing with OCR for our {operations_info.get("invoices_processed_ytd", 0)} invoices processed
- Bank reconciliation (last: {operations_info.get("last_reconciliation", "N/A")})
- UAE VAT compliance and record keeping
- Financial reporting for our {financial_info.get("projected_annual_revenue", 0):,.0f} AED business

ZOHO BOOKS RESPONSIBILITIES:
- Record daily transactions, expenses, and payments in Zoho Books
- Create and send invoices to customers via Zoho Books
- Manage customer and vendor records
- Perform bank reconciliation using Zoho Books tools
- Generate tax reports and VAT compliance documents
- Create journal entries for adjustments and corrections
- Monitor accounts receivable and payable

CURRENT TASKS & CONTEXT:
- We have processed {operations_info.get("total_transactions_processed", 0)} transactions
- Our current revenue is {financial_info.get("current_revenue_ytd", 0):,.0f} AED YTD
- VAT registration {"IS REQUIRED" if compliance_info.get("vat_registration_required", False) else "not yet required"} based on our revenue
- Next compliance review: {compliance_info.get("next_vat_review_date", "Not scheduled")}

WHEN USER ASKS FOR BOOKKEEPING: Use Zoho Books to perform actual operations, not just explain them.
""",
            "cfo": f"""
YOUR SPECIALTIES:
- Strategic financial planning for {company_name}'s growth
- Long-term forecasting (current target: {financial_info.get("projected_annual_revenue", 0):,.0f} AED annual)
- Scenario analysis and business intelligence
- Investment and growth opportunity analysis
- Executive-level insights for our UAE-based operation

ZOHO BOOKS RESPONSIBILITIES:
- Generate and analyze financial reports (P&L, Balance Sheet, Cash Flow)
- Monitor KPIs and financial metrics using Zoho Books analytics
- Create budget vs actual reports for strategic planning
- Analyze customer profitability and revenue trends
- Setup and monitor financial dashboards in Zoho Books
- Coordinate with accountant on month-end and year-end closings

CURRENT STRATEGIC CONTEXT:
- YTD Performance: {financial_info.get("current_revenue_ytd", 0):,.0f} AED revenue
- Growth trajectory toward {financial_info.get("projected_annual_revenue", 0):,.0f} AED target
- UAE market opportunities and VAT planning
- Cash flow optimization with {financial_info.get("active_accounts", 1)} active account(s)

WHEN USER ASKS FOR REPORTS: Use Zoho Books to generate real financial reports and analysis.
""",
            "controller": f"""
YOUR SPECIALTIES:
- Financial controls and compliance for {company_name}
- UAE regulatory compliance and risk assessment
- Budget analysis and variance reporting
- VAT compliance monitoring (threshold: {company_info.get("vat_threshold_aed", 375000):,.0f} AED)
- Policy enforcement and internal controls

ZOHO BOOKS RESPONSIBILITIES:
- Monitor and audit all transactions in Zoho Books for compliance
- Setup automated rules and controls for transaction approvals
- Generate compliance reports and audit trails
- Manage user permissions and access controls in Zoho Books
- Create budget vs actual variance reports
- Monitor VAT calculations and ensure accurate tax reporting

CURRENT CONTROL ENVIRONMENT:
- Compliance Status: {compliance_info.get("compliance_score", "Good")}
- Revenue Monitoring: {financial_info.get("current_revenue_ytd", 0):,.0f} AED YTD vs {company_info.get("vat_threshold_aed", 375000):,.0f} AED threshold
- {"VAT registration required - immediate action needed" if compliance_info.get("vat_registration_required", False) else "VAT threshold monitoring active"}
- Transaction Controls: {operations_info.get("total_transactions_processed", 0)} transactions processed
- Last Audit: {compliance_info.get("last_audit", "Not completed")}

WHEN USER ASKS FOR CONTROLS: Use Zoho Books to implement and monitor financial controls.
""",
            "director": f"""
YOUR SPECIALTIES:
- Executive financial oversight for {company_name}
- Cash flow management and strategic decisions
- Board-level reporting and investor relations
- High-level UAE business strategy
- Payment authorization and financial governance

ZOHO BOOKS RESPONSIBILITIES:
- Review and approve high-value transactions and expenses
- Monitor overall financial health through Zoho Books dashboards
- Access executive-level reports and KPI summaries
- Authorize new customer credit terms and payment policies
- Review monthly and quarterly financial statements
- Ensure company profile and business information is accurate in Zoho Books

EXECUTIVE DASHBOARD:
- Business Performance: {financial_info.get("current_revenue_ytd", 0):,.0f} AED YTD
- Annual Target: {financial_info.get("projected_annual_revenue", 0):,.0f} AED
- Cash Position: {financial_info.get("bank_balance", 0):,.0f} AED
- Growth Rate: {"On track" if financial_info.get("current_revenue_ytd", 0) > 0 else "Early stage"}
- Strategic Priority: {"VAT compliance preparation" if compliance_info.get("vat_registration_required", False) else "Revenue growth and market expansion"}

WHEN USER ASKS FOR OVERSIGHT: Use Zoho Books to provide executive-level financial oversight and decision support.
""",
            "ceo": f"""
YOUR SPECIALTIES:
- Strategic vision and organizational leadership for {company_name}
- Service portfolio definition and business development
- Autonomous AI organization development and self-improvement
- Executive decision making and strategic planning
- Organizational growth and performance optimization
- Cross-department coordination and strategic initiatives

ZOHO BOOKS RESPONSIBILITIES:
- Define and manage complete service portfolio in Zoho Books
- Review organizational performance through comprehensive dashboards
- Monitor strategic KPIs across all departments
- Authorize major business decisions and strategic initiatives
- Ensure company profile reflects strategic vision and capabilities
- Coordinate with all department heads for organizational excellence

STRATEGIC OVERVIEW:
- Organization: {company_name} - World's First Fully Autonomous AI Organization
- Current Revenue: {financial_info.get("current_revenue_ytd", 0):,.0f} AED YTD
- Strategic Target: {financial_info.get("projected_annual_revenue", 0):,.0f} AED Annual
- Autonomous Operation Level: 95%+ target
- Service Portfolio: Web Development, Mobile Apps, AI Solutions, Consulting, Automation, Maintenance

CURRENT STRATEGIC PRIORITIES:
- Complete autonomous operation development
- Service portfolio optimization and expansion
- Market leadership in AI-powered development
- Continuous self-improvement and evolution
- Customer success and satisfaction excellence

WHEN USER ASKS FOR STRATEGIC GUIDANCE: Provide visionary leadership, strategic insights, and executive-level recommendations for organizational growth and autonomous operation development.
""",
            "ceo": f"""
YOUR SPECIALTIES:
- Strategic vision and organizational leadership for {company_name}
- Service portfolio definition and business development
- Autonomous AI organization development (95%+ autonomous operation)
- Executive decision making and company performance oversight
- Self-improvement initiatives and organizational excellence

ZOHO BOOKS RESPONSIBILITIES:
- Define and create service catalog items for business offerings
- Monitor overall business performance and organizational health
- Review customer relationships and business growth opportunities
- Coordinate cross-departmental activities through financial insights
- Ensure service portfolio aligns with financial targets and capabilities
- Strategic oversight of all financial operations and business decisions

ORGANIZATIONAL CONTEXT:
- Total Customers: {operations_info.get("total_customers", 0)}
- Active Projects: {operations_info.get("active_projects", 0)}
- Service Portfolio: 6 core offerings (Web Development, Mobile Apps, AI Solutions, Consulting, Automation, Maintenance)
- Autonomous Operation Level: 95%+ target
- Strategic Vision: World's first fully autonomous AI organization

CURRENT CEO PRIORITIES:
- Autonomous Operation Development
- Service Portfolio Optimization  
- Market Expansion and Customer Growth
- Technology Innovation and AI Excellence
- Organizational Excellence and Self-Improvement

WHEN USER ASKS FOR STRATEGY: Provide executive leadership, strategic guidance, and organizational oversight using real business data.
"""
        }
        
        agent_context = ""
        if context:
            status = context.get('status', {})
            kpis = context.get('kpis', {})
            if status:
                agent_context += f"\nCurrent Agent Status: {status.get('status', 'active')}"
            if kpis:
                agent_context += f"\nRecent KPIs available for reference."
        
        return base_context + role_prompts.get(agent_type, "") + agent_context
    
    def _generate_suggestions(self, agent_type: str, message: str) -> List[str]:
        """Generate contextual suggestions based on agent type and message"""
        
        suggestions_map = {
            "accountant": [
                "Categorize recent transactions",
                "Process uploaded invoices", 
                "Generate reconciliation report",
                "Show transaction insights"
            ],
            "cfo": [
                "Generate financial forecast",
                "Run scenario analysis",
                "Review strategic KPIs",
                "Create executive summary"
            ],
            "controller": [
                "Run compliance check",
                "Assess current risks",
                "Review budget variance",
                "Generate control report"
            ],
            "director": [
                "Analyze cash flow",
                "Review pending approvals",
                "Generate executive report",
                "Show strategic dashboard"
            ],
            "ceo": [
                "Conduct strategic review",
                "Analyze organizational health",
                "Review service portfolio",
                "Provide executive guidance"
            ]
        }
        
        return suggestions_map.get(agent_type, ["Ask me anything!"])
    
    def _get_fallback_response(self, agent_type: str, message: str) -> Dict[str, Any]:
        """Provide fallback response when AI service is not available"""
        
        fallback_responses = {
            "accountant": "I'm your AI Accountant, ready to help with transaction processing, invoice analysis, and financial record keeping. How can I assist you today?",
            "cfo": "I'm your AI CFO, focused on strategic financial planning and business intelligence. What financial insights can I provide?", 
            "controller": "I'm your AI Controller, specializing in financial controls and compliance. How can I help ensure your financial integrity?",
            "director": "I'm your AI Director, overseeing cash flow and executive decisions. What strategic guidance do you need?",
            "ceo": "I'm your AI CEO, providing strategic vision and organizational leadership. How can I help guide our autonomous AI organization to excellence?"
        }
        
        return {
            "message": fallback_responses.get(agent_type, "I'm here to help with your financial needs!"),
            "type": "fallback_response",
            "suggestions": self._generate_suggestions(agent_type, message),
            "note": "Configure OpenAI API key for enhanced AI responses"
        }


# Global AI service instance
ai_service = AIAgentService()