"""
Zoho Books Data Synchronization Service

This service manages the synchronization of data between Zoho Books API and our local database
to reduce API calls and improve performance while staying within rate limits.

Key Features:
- Periodic sync of customers, projects, and items from Zoho Books
- Local caching with configurable sync intervals
- Rate limit awareness and management
- Error handling and retry logic
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, update

from ..db import session_scope
from ..models import ZohoCustomer, ZohoProject, ZohoItem, ZohoSyncStatus
from ..utils.zoho_books_api import zoho_books_api
from ..logging_config import get_logger

logger = get_logger("zoho_sync_service")


class ZohoSyncService:
    """Service for synchronizing Zoho Books data with local database"""
    
    def __init__(self):
        self.api = zoho_books_api
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        self.rate_limit_delay = 60  # wait 1 minute if rate limited
        
    async def sync_all_data(self, force_sync: bool = False) -> Dict[str, Any]:
        """Sync all Zoho Books data types that need updates"""
        
        results = {
            "customers": {"status": "skipped", "records": 0, "error": None},
            "projects": {"status": "skipped", "records": 0, "error": None}, 
            "items": {"status": "skipped", "records": 0, "error": None},
            "total_api_calls": 0,
            "sync_time": datetime.now().isoformat()
        }
        
        try:
            with session_scope() as session:
                # Check which data types need syncing
                sync_statuses = session.execute(
                    select(ZohoSyncStatus).where(ZohoSyncStatus.is_enabled == True)
                ).scalars().all()
                
                for sync_status in sync_statuses:
                    if self._should_sync(sync_status, force_sync):
                        
                        if sync_status.data_type == "customers":
                            result = await self._sync_customers(session, sync_status)
                            results["customers"] = result
                            results["total_api_calls"] += 1
                            
                        elif sync_status.data_type == "projects":
                            result = await self._sync_projects(session, sync_status)
                            results["projects"] = result
                            results["total_api_calls"] += 1
                            
                        elif sync_status.data_type == "items":
                            result = await self._sync_items(session, sync_status)
                            results["items"] = result
                            results["total_api_calls"] += 1
                        
                        # Add delay between API calls to respect rate limits
                        if results["total_api_calls"] > 0:
                            await asyncio.sleep(2)  # 2 second delay between calls
                
                session.commit()
                
        except Exception as e:
            logger.error(f"Error in sync_all_data: {e}")
            results["error"] = str(e)
        
        return results
    
    def _should_sync(self, sync_status: ZohoSyncStatus, force_sync: bool = False) -> bool:
        """Check if data type should be synced based on schedule"""
        
        if force_sync:
            return True
            
        if sync_status.last_sync_time is None:
            return True  # Never synced before
            
        next_sync_time = sync_status.last_sync_time + timedelta(minutes=sync_status.sync_interval_minutes)
        return datetime.now() >= next_sync_time
    
    async def _sync_customers(self, session: Session, sync_status: ZohoSyncStatus) -> Dict[str, Any]:
        """Sync customers from Zoho Books to local database"""
        
        result = {"status": "error", "records": 0, "error": None}
        
        try:
            # Update sync status to running
            sync_status.sync_status = "running"
            sync_status.last_sync_time = datetime.now()
            session.commit()
            
            # Fetch customers from Zoho Books
            logger.info("Syncing customers from Zoho Books...")
            response = await self.api.get_customers()
            
            if not response.get("success", False):
                raise Exception(f"Zoho API error: {response.get('message', 'Unknown error')}")
                
            customers_data = response.get("customers", [])
            records_synced = 0
            
            for customer_data in customers_data:
                try:
                    # Check if customer already exists
                    existing_customer = session.execute(
                        select(ZohoCustomer).where(
                            ZohoCustomer.zoho_customer_id == str(customer_data.get("customer_id"))
                        )
                    ).scalar_one_or_none()
                    
                    if existing_customer:
                        # Update existing customer
                        existing_customer.customer_name = customer_data.get("customer_name", "")
                        existing_customer.company_name = customer_data.get("company_name")
                        existing_customer.email = customer_data.get("email")
                        existing_customer.phone = customer_data.get("phone")
                        existing_customer.website = customer_data.get("website")
                        existing_customer.currency_code = customer_data.get("currency_code")
                        existing_customer.opening_balance = customer_data.get("opening_balance")
                        existing_customer.credit_limit = customer_data.get("credit_limit")
                        existing_customer.status = customer_data.get("status", "active")
                        existing_customer.last_synced = datetime.now()
                        existing_customer.sync_status = "synced"
                    else:
                        # Create new customer
                        new_customer = ZohoCustomer(
                            zoho_customer_id=str(customer_data.get("customer_id")),
                            customer_name=customer_data.get("customer_name", ""),
                            company_name=customer_data.get("company_name"),
                            email=customer_data.get("email"),
                            phone=customer_data.get("phone"),
                            website=customer_data.get("website"),
                            currency_code=customer_data.get("currency_code"),
                            opening_balance=customer_data.get("opening_balance"),
                            credit_limit=customer_data.get("credit_limit"),
                            status=customer_data.get("status", "active"),
                            last_synced=datetime.now(),
                            sync_status="synced"
                        )
                        session.add(new_customer)
                    
                    records_synced += 1
                    
                except Exception as e:
                    logger.error(f"Error syncing customer {customer_data.get('customer_id')}: {e}")
                    continue
            
            # Update sync status
            sync_status.sync_status = "success"
            sync_status.last_successful_sync = datetime.now()
            sync_status.records_synced = records_synced
            sync_status.sync_errors = None
            sync_status.updated_at = datetime.now()
            
            result = {"status": "success", "records": records_synced, "error": None}
            logger.info(f"Successfully synced {records_synced} customers")
            
        except Exception as e:
            logger.error(f"Error syncing customers: {e}")
            sync_status.sync_status = "error"
            sync_status.sync_errors = str(e)
            sync_status.updated_at = datetime.now()
            result = {"status": "error", "records": 0, "error": str(e)}
        
        return result
    
    async def _sync_projects(self, session: Session, sync_status: ZohoSyncStatus) -> Dict[str, Any]:
        """Sync projects from Zoho Books to local database"""
        
        result = {"status": "error", "records": 0, "error": None}
        
        try:
            # Update sync status to running
            sync_status.sync_status = "running"
            sync_status.last_sync_time = datetime.now()
            session.commit()
            
            # Fetch projects from Zoho Books
            logger.info("Syncing projects from Zoho Books...")
            response = await self.api.get_projects()
            
            if not response.get("success", False):
                raise Exception(f"Zoho API error: {response.get('message', 'Unknown error')}")
                
            projects_data = response.get("projects", [])
            records_synced = 0
            
            for project_data in projects_data:
                try:
                    # Check if project already exists
                    existing_project = session.execute(
                        select(ZohoProject).where(
                            ZohoProject.zoho_project_id == str(project_data.get("project_id"))
                        )
                    ).scalar_one_or_none()
                    
                    if existing_project:
                        # Update existing project
                        existing_project.project_name = project_data.get("project_name", "")
                        existing_project.project_code = project_data.get("project_code")
                        existing_project.description = project_data.get("description")
                        existing_project.customer_id = project_data.get("customer_id")
                        existing_project.customer_name = project_data.get("customer_name")
                        existing_project.budget_type = project_data.get("budget_type")
                        existing_project.budget_amount = project_data.get("budget_amount")
                        existing_project.budget_hours = project_data.get("budget_hours")
                        existing_project.status = project_data.get("status", "active")
                        existing_project.billing_type = project_data.get("billing_type")
                        existing_project.rate = project_data.get("rate")
                        existing_project.currency_code = project_data.get("currency_code")
                        existing_project.last_synced = datetime.now()
                        existing_project.sync_status = "synced"
                    else:
                        # Create new project
                        new_project = ZohoProject(
                            zoho_project_id=str(project_data.get("project_id")),
                            project_name=project_data.get("project_name", ""),
                            project_code=project_data.get("project_code"),
                            description=project_data.get("description"),
                            customer_id=project_data.get("customer_id"),
                            customer_name=project_data.get("customer_name"),
                            budget_type=project_data.get("budget_type"),
                            budget_amount=project_data.get("budget_amount"),
                            budget_hours=project_data.get("budget_hours"),
                            status=project_data.get("status", "active"),
                            billing_type=project_data.get("billing_type"),
                            rate=project_data.get("rate"),
                            currency_code=project_data.get("currency_code"),
                            last_synced=datetime.now(),
                            sync_status="synced"
                        )
                        session.add(new_project)
                    
                    records_synced += 1
                    
                except Exception as e:
                    logger.error(f"Error syncing project {project_data.get('project_id')}: {e}")
                    continue
            
            # Update sync status
            sync_status.sync_status = "success"
            sync_status.last_successful_sync = datetime.now()
            sync_status.records_synced = records_synced
            sync_status.sync_errors = None
            sync_status.updated_at = datetime.now()
            
            result = {"status": "success", "records": records_synced, "error": None}
            logger.info(f"Successfully synced {records_synced} projects")
            
        except Exception as e:
            logger.error(f"Error syncing projects: {e}")
            sync_status.sync_status = "error"
            sync_status.sync_errors = str(e)
            sync_status.updated_at = datetime.now()
            result = {"status": "error", "records": 0, "error": str(e)}
        
        return result
    
    async def _sync_items(self, session: Session, sync_status: ZohoSyncStatus) -> Dict[str, Any]:
        """Sync items from Zoho Books to local database"""
        
        result = {"status": "error", "records": 0, "error": None}
        
        try:
            # Update sync status to running
            sync_status.sync_status = "running"
            sync_status.last_sync_time = datetime.now()
            session.commit()
            
            # Fetch items from Zoho Books
            logger.info("Syncing items from Zoho Books...")
            response = await self.api.get_items()
            
            if not response.get("success", False):
                raise Exception(f"Zoho API error: {response.get('message', 'Unknown error')}")
                
            items_data = response.get("items", [])
            records_synced = 0
            
            for item_data in items_data:
                try:
                    # Check if item already exists
                    existing_item = session.execute(
                        select(ZohoItem).where(
                            ZohoItem.zoho_item_id == str(item_data.get("item_id"))
                        )
                    ).scalar_one_or_none()
                    
                    if existing_item:
                        # Update existing item
                        existing_item.name = item_data.get("name", "")
                        existing_item.sku = item_data.get("sku")
                        existing_item.description = item_data.get("description")
                        existing_item.item_type = item_data.get("item_type", "sales")
                        existing_item.rate = item_data.get("rate")
                        existing_item.unit = item_data.get("unit")
                        existing_item.is_taxable = item_data.get("is_taxable", True)
                        existing_item.tax_name = item_data.get("tax_name")
                        existing_item.tax_percentage = item_data.get("tax_percentage")
                        existing_item.status = item_data.get("status", "active")
                        existing_item.last_synced = datetime.now()
                        existing_item.sync_status = "synced"
                    else:
                        # Create new item
                        new_item = ZohoItem(
                            zoho_item_id=str(item_data.get("item_id")),
                            name=item_data.get("name", ""),
                            sku=item_data.get("sku"),
                            description=item_data.get("description"),
                            item_type=item_data.get("item_type", "sales"),
                            rate=item_data.get("rate"),
                            unit=item_data.get("unit"),
                            is_taxable=item_data.get("is_taxable", True),
                            tax_name=item_data.get("tax_name"),
                            tax_percentage=item_data.get("tax_percentage"),
                            status=item_data.get("status", "active"),
                            last_synced=datetime.now(),
                            sync_status="synced"
                        )
                        session.add(new_item)
                    
                    records_synced += 1
                    
                except Exception as e:
                    logger.error(f"Error syncing item {item_data.get('item_id')}: {e}")
                    continue
            
            # Update sync status
            sync_status.sync_status = "success"
            sync_status.last_successful_sync = datetime.now()
            sync_status.records_synced = records_synced
            sync_status.sync_errors = None
            sync_status.updated_at = datetime.now()
            
            result = {"status": "success", "records": records_synced, "error": None}
            logger.info(f"Successfully synced {records_synced} items")
            
        except Exception as e:
            logger.error(f"Error syncing items: {e}")
            sync_status.sync_status = "error"
            sync_status.sync_errors = str(e)
            sync_status.updated_at = datetime.now()
            result = {"status": "error", "records": 0, "error": str(e)}
        
        return result
    
    # Data Access Methods - Use local database instead of API
    
    def get_customers_from_db(self) -> Dict[str, Any]:
        """Get customers from local database instead of API"""
        try:
            with session_scope() as session:
                customers = session.execute(
                    select(ZohoCustomer).where(ZohoCustomer.status == "active")
                ).scalars().all()
                
                customers_list = []
                for customer in customers:
                    customers_list.append({
                        "customer_id": customer.zoho_customer_id,
                        "customer_name": customer.customer_name,
                        "company_name": customer.company_name,
                        "email": customer.email,
                        "phone": customer.phone,
                        "website": customer.website,
                        "currency_code": customer.currency_code,
                        "status": customer.status,
                        "last_synced": customer.last_synced.isoformat() if customer.last_synced else None
                    })
                
                return {"success": True, "customers": customers_list}
                
        except Exception as e:
            logger.error(f"Error getting customers from database: {e}")
            return {"success": False, "error": str(e), "customers": []}
    
    def get_projects_from_db(self) -> Dict[str, Any]:
        """Get projects from local database instead of API"""
        try:
            with session_scope() as session:
                projects = session.execute(
                    select(ZohoProject).where(ZohoProject.status == "active")
                ).scalars().all()
                
                projects_list = []
                for project in projects:
                    projects_list.append({
                        "project_id": project.zoho_project_id,
                        "project_name": project.project_name,
                        "project_code": project.project_code,
                        "description": project.description,
                        "customer_id": project.customer_id,
                        "customer_name": project.customer_name,
                        "budget_amount": project.budget_amount,
                        "status": project.status,
                        "project_status": project.status,  # Alias for compatibility
                        "last_synced": project.last_synced.isoformat() if project.last_synced else None
                    })
                
                return {"success": True, "projects": projects_list}
                
        except Exception as e:
            logger.error(f"Error getting projects from database: {e}")
            return {"success": False, "error": str(e), "projects": []}
    
    def get_items_from_db(self) -> Dict[str, Any]:
        """Get items from local database instead of API"""
        try:
            with session_scope() as session:
                items = session.execute(
                    select(ZohoItem).where(ZohoItem.status == "active")
                ).scalars().all()
                
                items_list = []
                for item in items:
                    items_list.append({
                        "item_id": item.zoho_item_id,
                        "name": item.name,
                        "sku": item.sku,
                        "description": item.description,
                        "item_type": item.item_type,
                        "rate": item.rate,
                        "unit": item.unit,
                        "is_taxable": item.is_taxable,
                        "status": item.status,
                        "last_synced": item.last_synced.isoformat() if item.last_synced else None
                    })
                
                return {"success": True, "items": items_list}
                
        except Exception as e:
            logger.error(f"Error getting items from database: {e}")
            return {"success": False, "error": str(e), "items": []}
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status for all data types"""
        try:
            with session_scope() as session:
                sync_statuses = session.execute(select(ZohoSyncStatus)).scalars().all()
                
                status_info = {}
                for sync_status in sync_statuses:
                    status_info[sync_status.data_type] = {
                        "last_sync": sync_status.last_sync_time.isoformat() if sync_status.last_sync_time else None,
                        "last_successful_sync": sync_status.last_successful_sync.isoformat() if sync_status.last_successful_sync else None,
                        "sync_status": sync_status.sync_status,
                        "records_synced": sync_status.records_synced,
                        "sync_interval_minutes": sync_status.sync_interval_minutes,
                        "is_enabled": sync_status.is_enabled,
                        "sync_errors": sync_status.sync_errors
                    }
                
                return {"success": True, "sync_status": status_info}
                
        except Exception as e:
            logger.error(f"Error getting sync status: {e}")
            return {"success": False, "error": str(e), "sync_status": {}}


# Global sync service instance
zoho_sync_service = ZohoSyncService()