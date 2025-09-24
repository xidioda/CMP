"""
Background Scheduler for Zoho Data Synchronization

This module provides background task scheduling for periodic synchronization
of Zoho Books data to maintain fresh local data while respecting API rate limits.

Features:
- Configurable sync intervals per data type
- Automatic retry logic with exponential backoff  
- Rate limit detection and handling
- Health monitoring and error reporting
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
import threading

from ..utils.zoho_sync_service import zoho_sync_service
from ..logging_config import get_logger

logger = get_logger("zoho_scheduler")


class ZohoSyncScheduler:
    """Background scheduler for Zoho Books data synchronization"""
    
    def __init__(self):
        self.is_running = False
        self.task = None
        self.sync_interval = 300  # Default 5 minutes (300 seconds)
        self.error_count = 0
        self.max_errors = 5
        self.last_sync_result = None
        self.scheduler_thread = None
        
    def start_scheduler(self, sync_interval_seconds: int = 300):
        """Start the background sync scheduler"""
        if self.is_running:
            logger.warning("Sync scheduler is already running")
            return
            
        self.sync_interval = sync_interval_seconds
        self.is_running = True
        self.error_count = 0
        
        # Start the scheduler in a separate thread
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info(f"Zoho sync scheduler started with {sync_interval_seconds}s interval")
    
    def stop_scheduler(self):
        """Stop the background sync scheduler"""
        if not self.is_running:
            logger.warning("Sync scheduler is not running")
            return
            
        self.is_running = False
        
        if self.task and not self.task.done():
            self.task.cancel()
            
        logger.info("Zoho sync scheduler stopped")
    
    def _run_scheduler(self):
        """Run the async scheduler in a thread with its own event loop"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self._scheduler_loop())
        except Exception as e:
            logger.error(f"Scheduler thread error: {e}")
        finally:
            loop.close()
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        logger.info("Starting sync scheduler loop...")
        
        while self.is_running:
            try:
                # Run sync operation
                sync_result = await zoho_sync_service.sync_all_data()
                self.last_sync_result = sync_result
                
                # Log sync results
                total_records = (sync_result.get("customers", {}).get("records", 0) + 
                               sync_result.get("projects", {}).get("records", 0) + 
                               sync_result.get("items", {}).get("records", 0))
                
                total_api_calls = sync_result.get("total_api_calls", 0)
                
                if total_api_calls > 0:
                    logger.info(f"Sync completed: {total_records} records, {total_api_calls} API calls")
                else:
                    logger.debug("Sync check completed: no updates needed")
                
                # Check for errors
                has_errors = (sync_result.get("customers", {}).get("status") == "error" or 
                            sync_result.get("projects", {}).get("status") == "error" or 
                            sync_result.get("items", {}).get("status") == "error")
                
                if has_errors:
                    self.error_count += 1
                    logger.warning(f"Sync completed with errors (error count: {self.error_count})")
                    
                    # If too many errors, increase sync interval
                    if self.error_count >= self.max_errors:
                        new_interval = min(self.sync_interval * 2, 3600)  # Max 1 hour
                        logger.warning(f"Too many sync errors, increasing interval to {new_interval}s")
                        self.sync_interval = new_interval
                        self.error_count = 0
                else:
                    # Reset error count on successful sync
                    if self.error_count > 0:
                        self.error_count = 0
                        logger.info("Sync errors cleared")
                
                # Wait for next sync interval
                await asyncio.sleep(self.sync_interval)
                
            except asyncio.CancelledError:
                logger.info("Sync scheduler cancelled")
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                self.error_count += 1
                
                # Wait before retrying
                retry_delay = min(60 * self.error_count, 300)  # Max 5 minutes
                logger.info(f"Retrying sync in {retry_delay} seconds")
                await asyncio.sleep(retry_delay)
    
    async def trigger_manual_sync(self, force_sync: bool = False) -> dict:
        """Trigger a manual sync operation"""
        if not self.is_running:
            logger.warning("Scheduler not running, performing one-time sync")
            
        logger.info("Manual sync triggered")
        sync_result = await zoho_sync_service.sync_all_data(force_sync=force_sync)
        self.last_sync_result = sync_result
        
        return sync_result
    
    def get_scheduler_status(self) -> dict:
        """Get current scheduler status and last sync results"""
        return {
            "is_running": self.is_running,
            "sync_interval": self.sync_interval,
            "error_count": self.error_count,
            "max_errors": self.max_errors,
            "last_sync_result": self.last_sync_result,
            "scheduler_health": "healthy" if self.error_count < self.max_errors else "degraded"
        }


# Global scheduler instance
zoho_scheduler = ZohoSyncScheduler()


# Auto-start scheduler on import (can be disabled if needed)
def auto_start_scheduler():
    """Auto-start the scheduler with default settings"""
    if not zoho_scheduler.is_running:
        # Start with 5 minute intervals (300 seconds)
        zoho_scheduler.start_scheduler(sync_interval_seconds=300)


# Uncomment the line below to enable auto-start
# auto_start_scheduler()