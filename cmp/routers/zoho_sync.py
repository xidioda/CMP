"""
Zoho Sync Management API Router

This router provides administrative endpoints for managing the Zoho Books synchronization
service, including manual sync triggers, status monitoring, and configuration.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any
import logging

from ..routers.auth import require_admin
from ..utils.zoho_sync_service import zoho_sync_service
from ..utils.zoho_scheduler import zoho_scheduler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/zoho-sync", tags=["Zoho Sync"])


@router.post("/trigger-sync")
async def trigger_manual_sync(
    force_sync: bool = False,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user=Depends(require_admin)
) -> Dict[str, Any]:
    """Trigger a manual synchronization of Zoho Books data"""
    try:
        logger.info(f"Manual sync triggered by user: {current_user.get('username', 'unknown')}")
        
        # Run sync in background to avoid timeout
        result = await zoho_scheduler.trigger_manual_sync(force_sync=force_sync)
        
        return {
            "message": "Manual sync triggered successfully",
            "sync_result": result,
            "force_sync": force_sync,
            "timestamp": result.get("sync_time")
        }
        
    except Exception as e:
        logger.error(f"Error triggering manual sync: {e}")
        raise HTTPException(status_code=500, detail=f"Sync trigger failed: {str(e)}")


@router.get("/status")
async def get_sync_status(current_user=Depends(require_admin)) -> Dict[str, Any]:
    """Get current synchronization status and scheduler information"""
    try:
        # Get sync status from database
        db_sync_status = zoho_sync_service.get_sync_status()
        
        # Get scheduler status
        scheduler_status = zoho_scheduler.get_scheduler_status()
        
        # Get data counts from local database
        customers = zoho_sync_service.get_customers_from_db()
        projects = zoho_sync_service.get_projects_from_db()
        items = zoho_sync_service.get_items_from_db()
        
        return {
            "sync_status": db_sync_status.get("sync_status", {}),
            "scheduler": scheduler_status,
            "local_data_counts": {
                "customers": len(customers.get("customers", [])),
                "projects": len(projects.get("projects", [])),
                "items": len(items.get("items", []))
            },
            "api_usage": {
                "status": "Using local database - no API calls for data retrieval",
                "sync_frequency": f"Every {scheduler_status.get('sync_interval', 300)} seconds",
                "rate_limit_protection": "Active"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        raise HTTPException(status_code=500, detail=f"Status retrieval failed: {str(e)}")


@router.post("/scheduler/start")
async def start_scheduler(
    sync_interval_seconds: int = 300,
    current_user=Depends(require_admin)
) -> Dict[str, Any]:
    """Start the automatic sync scheduler"""
    try:
        zoho_scheduler.start_scheduler(sync_interval_seconds=sync_interval_seconds)
        
        return {
            "message": "Sync scheduler started successfully",
            "sync_interval_seconds": sync_interval_seconds,
            "status": "running"
        }
        
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")
        raise HTTPException(status_code=500, detail=f"Scheduler start failed: {str(e)}")


@router.post("/scheduler/stop")
async def stop_scheduler(current_user=Depends(require_admin)) -> Dict[str, Any]:
    """Stop the automatic sync scheduler"""
    try:
        zoho_scheduler.stop_scheduler()
        
        return {
            "message": "Sync scheduler stopped successfully",
            "status": "stopped"
        }
        
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
        raise HTTPException(status_code=500, detail=f"Scheduler stop failed: {str(e)}")


@router.get("/data/customers")
async def get_local_customers(current_user=Depends(require_admin)) -> Dict[str, Any]:
    """Get customers from local database"""
    try:
        customers = zoho_sync_service.get_customers_from_db()
        return customers
        
    except Exception as e:
        logger.error(f"Error getting local customers: {e}")
        raise HTTPException(status_code=500, detail=f"Customer retrieval failed: {str(e)}")


@router.get("/data/projects")
async def get_local_projects(current_user=Depends(require_admin)) -> Dict[str, Any]:
    """Get projects from local database"""
    try:
        projects = zoho_sync_service.get_projects_from_db()
        return projects
        
    except Exception as e:
        logger.error(f"Error getting local projects: {e}")
        raise HTTPException(status_code=500, detail=f"Project retrieval failed: {str(e)}")


@router.get("/data/items")
async def get_local_items(current_user=Depends(require_admin)) -> Dict[str, Any]:
    """Get items/services from local database"""
    try:
        items = zoho_sync_service.get_items_from_db()
        return items
        
    except Exception as e:
        logger.error(f"Error getting local items: {e}")
        raise HTTPException(status_code=500, detail=f"Item retrieval failed: {str(e)}")


@router.get("/health")
async def sync_health_check() -> Dict[str, Any]:
    """Health check endpoint for sync service (no authentication required)"""
    try:
        scheduler_status = zoho_scheduler.get_scheduler_status()
        sync_status = zoho_sync_service.get_sync_status()
        
        # Determine overall health
        is_healthy = (
            scheduler_status.get("scheduler_health") == "healthy" and
            sync_status.get("success", False)
        )
        
        return {
            "status": "healthy" if is_healthy else "degraded",
            "scheduler_running": scheduler_status.get("is_running", False),
            "scheduler_health": scheduler_status.get("scheduler_health", "unknown"),
            "last_sync": scheduler_status.get("last_sync_result", {}).get("sync_time"),
            "error_count": scheduler_status.get("error_count", 0)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }