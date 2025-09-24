"""
Agent Database Tools

Provides secure database modification functions that AI agents can use 
to update company information, save documents, and modify settings 
when users provide new details through conversation.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, date
import hashlib
import os
from pathlib import Path

from ..db import session_scope
from ..models import Company, BusinessDocument, BusinessActivity, DocumentType, append_ledger_entry
from ..logging_config import get_logger
from ..config import settings

logger = get_logger("agent_db_tools")


class AgentDatabaseTools:
    """
    Database modification tools for AI agents
    
    These tools allow agents to safely update company information
    and save documents when users provide new details.
    """
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.actor = f"AI:{agent_name}"
    
    async def update_company_field(self, field_name: str, value: Any, user_message: str = None) -> Dict[str, Any]:
        """
        Update a specific company field
        
        Args:
            field_name: Name of the field to update (e.g., 'vat_registration_number')
            value: New value for the field
            user_message: Original user message that triggered the update
            
        Returns:
            Dict with success status and updated value
        """
        try:
            with session_scope() as session:
                company = session.query(Company).first()
                if not company:
                    # Create company if it doesn't exist
                    company = Company(
                        legal_name="CMP Financial Services LLC",
                        trade_name="CMP Financial Services",
                        city="Dubai",
                        emirate="Dubai",
                        country="United Arab Emirates",
                        currency="AED"
                    )
                    session.add(company)
                    session.flush()
                
                # Validate field exists and type
                if not hasattr(company, field_name):
                    return {
                        "success": False,
                        "error": f"Field '{field_name}' does not exist",
                        "field": field_name
                    }
                
                # Get the old value for logging
                old_value = getattr(company, field_name)
                
                # Handle different data types
                if field_name.endswith('_date') and isinstance(value, str):
                    try:
                        value = datetime.strptime(value, '%Y-%m-%d').date()
                    except ValueError:
                        return {
                            "success": False,
                            "error": f"Invalid date format for {field_name}. Use YYYY-MM-DD",
                            "field": field_name
                        }
                
                # Handle boolean fields
                if field_name in ['vat_registered', 'corporate_tax_registered']:
                    if isinstance(value, str):
                        value = value.lower() in ['true', 'yes', '1', 'on']
                
                # Handle enum fields
                if field_name == 'primary_activity' and isinstance(value, str):
                    try:
                        value = BusinessActivity(value.lower().replace(' ', '_'))
                    except ValueError:
                        return {
                            "success": False,
                            "error": f"Invalid business activity: {value}",
                            "field": field_name,
                            "valid_options": [activity.value for activity in BusinessActivity]
                        }
                
                # Update the field
                setattr(company, field_name, value)
                company.updated_by = self.actor
                
                # Log the change
                append_ledger_entry(
                    session,
                    actor=self.actor,
                    action=f"update_company_{field_name}",
                    data={
                        "field": field_name,
                        "old_value": str(old_value) if old_value else None,
                        "new_value": str(value) if value else None,
                        "user_message": user_message,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                session.commit()
                
                logger.info(f"{self.actor}: Updated company {field_name} from '{old_value}' to '{value}'")
                
                return {
                    "success": True,
                    "field": field_name,
                    "old_value": old_value,
                    "new_value": value,
                    "message": f"Successfully updated {field_name.replace('_', ' ')} to {value}"
                }
                
        except Exception as e:
            logger.error(f"{self.actor}: Error updating company field {field_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "field": field_name
            }
    
    async def update_vat_registration(self, trn: str, registration_date: str = None, registered: bool = True) -> Dict[str, Any]:
        """
        Update VAT registration information
        
        Args:
            trn: Tax Registration Number
            registration_date: Date of registration (YYYY-MM-DD)
            registered: Whether company is VAT registered
            
        Returns:
            Dict with success status and updated information
        """
        try:
            results = []
            
            # Update VAT registered status
            result = await self.update_company_field('vat_registered', registered)
            results.append(result)
            
            # Update TRN
            if trn:
                result = await self.update_company_field('vat_registration_number', trn)
                results.append(result)
            
            # Update registration date
            if registration_date:
                result = await self.update_company_field('vat_registration_date', registration_date)
                results.append(result)
            
            success = all(r.get('success', False) for r in results)
            
            return {
                "success": success,
                "updates": results,
                "message": "VAT registration information updated successfully" if success else "Some VAT updates failed"
            }
            
        except Exception as e:
            logger.error(f"{self.actor}: Error updating VAT registration: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_corporate_tax_registration(self, tax_number: str, registration_date: str = None, registered: bool = True) -> Dict[str, Any]:
        """
        Update corporate tax registration information
        
        Args:
            tax_number: Corporate tax number
            registration_date: Date of registration (YYYY-MM-DD)
            registered: Whether company is corporate tax registered
            
        Returns:
            Dict with success status and updated information
        """
        try:
            results = []
            
            # Update corporate tax registered status
            result = await self.update_company_field('corporate_tax_registered', registered)
            results.append(result)
            
            # Update tax number
            if tax_number:
                result = await self.update_company_field('corporate_tax_number', tax_number)
                results.append(result)
            
            # Update registration date
            if registration_date:
                result = await self.update_company_field('corporate_tax_registration_date', registration_date)
                results.append(result)
            
            success = all(r.get('success', False) for r in results)
            
            return {
                "success": success,
                "updates": results,
                "message": "Corporate tax registration information updated successfully" if success else "Some corporate tax updates failed"
            }
            
        except Exception as e:
            logger.error(f"{self.actor}: Error updating corporate tax registration: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_trade_license(self, license_number: str = None, authority: str = None, 
                                 issue_date: str = None, expiry_date: str = None) -> Dict[str, Any]:
        """
        Update trade license information
        
        Args:
            license_number: Trade license number
            authority: Licensing authority
            issue_date: Issue date (YYYY-MM-DD)
            expiry_date: Expiry date (YYYY-MM-DD)
            
        Returns:
            Dict with success status and updated information
        """
        try:
            results = []
            
            if license_number:
                result = await self.update_company_field('trade_license_number', license_number)
                results.append(result)
            
            if authority:
                result = await self.update_company_field('trade_license_authority', authority)
                results.append(result)
            
            if issue_date:
                result = await self.update_company_field('trade_license_issue_date', issue_date)
                results.append(result)
            
            if expiry_date:
                result = await self.update_company_field('trade_license_expiry_date', expiry_date)
                results.append(result)
            
            success = all(r.get('success', False) for r in results)
            
            return {
                "success": success,
                "updates": results,
                "message": "Trade license information updated successfully" if success else "Some trade license updates failed"
            }
            
        except Exception as e:
            logger.error(f"{self.actor}: Error updating trade license: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_company_info(self) -> Dict[str, Any]:
        """
        Get current company information
        
        Returns:
            Dict with company information
        """
        try:
            with session_scope() as session:
                company = session.query(Company).first()
                if not company:
                    return {
                        "success": False,
                        "error": "No company information found"
                    }
                
                return {
                    "success": True,
                    "company": {
                        "legal_name": company.legal_name,
                        "trade_name": company.trade_name,
                        "business_type": company.business_type,
                        "vat_registered": company.vat_registered,
                        "vat_registration_number": company.vat_registration_number,
                        "vat_registration_date": company.vat_registration_date.isoformat() if company.vat_registration_date else None,
                        "corporate_tax_registered": company.corporate_tax_registered,
                        "corporate_tax_number": company.corporate_tax_number,
                        "corporate_tax_registration_date": company.corporate_tax_registration_date.isoformat() if company.corporate_tax_registration_date else None,
                        "trade_license_number": company.trade_license_number,
                        "trade_license_authority": company.trade_license_authority,
                        "trade_license_issue_date": company.trade_license_issue_date.isoformat() if company.trade_license_issue_date else None,
                        "trade_license_expiry_date": company.trade_license_expiry_date.isoformat() if company.trade_license_expiry_date else None,
                        "primary_activity": company.primary_activity.value if company.primary_activity else None,
                        "city": company.city,
                        "emirate": company.emirate,
                        "country": company.country,
                        "currency": company.currency,
                        "fiscal_year_end": company.fiscal_year_end
                    }
                }
                
        except Exception as e:
            logger.error(f"{self.actor}: Error getting company info: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def save_document_reference(self, document_type: str, title: str, description: str = None, 
                                    document_number: str = None, file_name: str = None) -> Dict[str, Any]:
        """
        Save a reference to a business document
        
        Args:
            document_type: Type of document (trade_license, vat_certificate, etc.)
            title: Document title
            description: Document description
            document_number: Document number/reference
            file_name: Name of the uploaded file (if any)
            
        Returns:
            Dict with success status and document ID
        """
        try:
            with session_scope() as session:
                company = session.query(Company).first()
                if not company:
                    return {
                        "success": False,
                        "error": "No company found to associate document with"
                    }
                
                # Validate document type
                try:
                    doc_type = DocumentType(document_type.lower().replace(' ', '_'))
                except ValueError:
                    return {
                        "success": False,
                        "error": f"Invalid document type: {document_type}",
                        "valid_types": [doc_type.value for doc_type in DocumentType]
                    }
                
                # Create document record
                document = BusinessDocument(
                    company_id=company.id,
                    document_type=doc_type,
                    title=title,
                    description=description,
                    document_number=document_number,
                    file_name=file_name or f"document_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    original_file_name=file_name or title,
                    file_path="",  # Will be updated when file is uploaded
                    file_size=0,
                    content_type="application/octet-stream",
                    file_hash="",  # Will be updated when file is uploaded
                    uploaded_by=self.actor
                )
                
                session.add(document)
                session.flush()
                
                # Log the action
                append_ledger_entry(
                    session,
                    actor=self.actor,
                    action="save_document_reference",
                    data={
                        "document_id": document.id,
                        "document_type": document_type,
                        "title": title,
                        "document_number": document_number,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                session.commit()
                
                logger.info(f"{self.actor}: Saved document reference: {title} ({document_type})")
                
                return {
                    "success": True,
                    "document_id": document.id,
                    "message": f"Document reference saved: {title}"
                }
                
        except Exception as e:
            logger.error(f"{self.actor}: Error saving document reference: {e}")
            return {
                "success": False,
                "error": str(e)
            }