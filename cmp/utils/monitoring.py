"""
Enhanced monitoring and logging system for CMP platform
Provides performance metrics, contextual logging, and system health monitoring
"""

import logging
import time
import sys
import functools
import traceback
import threading
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List, Union
from contextlib import contextmanager
from collections import defaultdict, deque

from sqlalchemy import text

# Try to import psutil, fall back to basic monitoring if not available
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class PerformanceMetrics:
    """Track and analyze performance metrics"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.request_times = deque(maxlen=max_history)
        self.error_counts = defaultdict(int)
        self.endpoint_stats = defaultdict(lambda: {
            'count': 0,
            'total_time': 0,
            'min_time': float('inf'),
            'max_time': 0,
            'error_count': 0
        })
        self._lock = threading.Lock()
    
    def record_request(self, endpoint: str, duration: float, status_code: int):
        """Record a request's performance metrics"""
        with self._lock:
            # Record overall request time
            self.request_times.append({
                'timestamp': datetime.utcnow(),
                'duration': duration,
                'endpoint': endpoint,
                'status_code': status_code
            })
            
            # Update endpoint stats
            stats = self.endpoint_stats[endpoint]
            stats['count'] += 1
            stats['total_time'] += duration
            stats['min_time'] = min(stats['min_time'], duration)
            stats['max_time'] = max(stats['max_time'], duration)
            
            if status_code >= 400:
                stats['error_count'] += 1
                self.error_counts[status_code] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        with self._lock:
            if not self.request_times:
                return {"message": "No requests recorded yet"}
            
            recent_requests = list(self.request_times)
            total_requests = len(recent_requests)
            
            # Calculate overall stats
            total_time = sum(req['duration'] for req in recent_requests)
            avg_response_time = total_time / total_requests if total_requests > 0 else 0
            
            # Calculate percentiles
            sorted_times = sorted(req['duration'] for req in recent_requests)
            p50 = sorted_times[int(len(sorted_times) * 0.5)] if sorted_times else 0
            p95 = sorted_times[int(len(sorted_times) * 0.95)] if sorted_times else 0
            p99 = sorted_times[int(len(sorted_times) * 0.99)] if sorted_times else 0
            
            # Error rate
            error_count = sum(1 for req in recent_requests if req['status_code'] >= 400)
            error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0
            
            # Recent activity (last 5 minutes)
            five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
            recent_activity = sum(1 for req in recent_requests 
                                if req['timestamp'] > five_minutes_ago)
            
            return {
                "total_requests": total_requests,
                "avg_response_time": round(avg_response_time, 3),
                "p50_response_time": round(p50, 3),
                "p95_response_time": round(p95, 3),
                "p99_response_time": round(p99, 3),
                "error_rate": round(error_rate, 2),
                "requests_last_5min": recent_activity,
                "error_breakdown": dict(self.error_counts),
                "endpoint_stats": {
                    endpoint: {
                        "count": stats['count'],
                        "avg_time": round(stats['total_time'] / stats['count'], 3),
                        "min_time": round(stats['min_time'], 3),
                        "max_time": round(stats['max_time'], 3),
                        "error_rate": round((stats['error_count'] / stats['count']) * 100, 2)
                    }
                    for endpoint, stats in self.endpoint_stats.items()
                }
            }


class ContextualLogger:
    """Enhanced logger with context and structured logging"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.context = {}
    
    @contextmanager
    def context_manager(self, **context):
        """Add context for the duration of the context manager"""
        old_context = self.context.copy()
        self.context.update(context)
        try:
            yield
        finally:
            self.context = old_context
    
    def _format_message(self, message: str, extra_context: Optional[Dict] = None) -> str:
        """Format message with context"""
        context = {**self.context}
        if extra_context:
            context.update(extra_context)
        
        if context:
            context_str = " | ".join(f"{k}={v}" for k, v in context.items())
            return f"{message} [{context_str}]"
        return message
    
    def info(self, message: str, **context):
        """Log info message with context"""
        self.logger.info(self._format_message(message, context))
    
    def warning(self, message: str, **context):
        """Log warning message with context"""
        self.logger.warning(self._format_message(message, context))
    
    def error(self, message: str, **context):
        """Log error message with context"""
        self.logger.error(self._format_message(message, context))
    
    def debug(self, message: str, **context):
        """Log debug message with context"""
        self.logger.debug(self._format_message(message, context))


# Global instances
performance_metrics = PerformanceMetrics()
contextual_logger = ContextualLogger("cmp.monitoring")


def performance_monitor(endpoint_name: Optional[str] = None):
    """Decorator to monitor function performance"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            endpoint = endpoint_name or f"{func.__module__}.{func.__name__}"
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                performance_metrics.record_request(endpoint, duration, 200)
                return result
            except Exception as e:
                duration = time.time() - start_time
                performance_metrics.record_request(endpoint, duration, 500)
                contextual_logger.error(
                    f"Function {endpoint} failed",
                    duration=duration,
                    error=str(e)
                )
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            endpoint = endpoint_name or f"{func.__module__}.{func.__name__}"
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                performance_metrics.record_request(endpoint, duration, 200)
                return result
            except Exception as e:
                duration = time.time() - start_time
                performance_metrics.record_request(endpoint, duration, 500)
                contextual_logger.error(
                    f"Function {endpoint} failed",
                    duration=duration,
                    error=str(e)
                )
                raise
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class SystemHealthMonitor:
    """Monitor system health and application status"""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.health_checks = {}
    
    def register_health_check(self, name: str, check_func: Callable):
        """Register a health check function"""
        self.health_checks[name] = check_func
    
    def get_uptime(self) -> Dict[str, Any]:
        """Get system uptime information"""
        uptime = datetime.utcnow() - self.start_time
        return {
            "start_time": self.start_time.isoformat(),
            "uptime_seconds": int(uptime.total_seconds()),
            "uptime_human": str(uptime)
        }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system resource metrics"""
        if not PSUTIL_AVAILABLE:
            return {"error": "psutil not available - install with: pip install psutil"}
        
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_usage": round(cpu_percent, 1),
                "memory_usage": round(memory.percent, 1),
                "memory_available": round(memory.available / (1024**3), 2),  # GB
                "disk_usage": round(disk.percent, 1),
                "disk_free": round(disk.free / (1024**3), 2)  # GB
            }
        except Exception as e:
            return {"error": f"Failed to get system metrics: {str(e)}"}
    
    async def check_database_health(self, db_session) -> Dict[str, Any]:
        """Check database connectivity and health"""
        try:
            # Simple connectivity test
            result = db_session.execute(text("SELECT 1"))
            result.fetchone()  # Remove await since it's not async
            
            return {
                "status": "healthy",
                "message": "Database connection successful"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def check_agents_health(self) -> Dict[str, Any]:
        """Check AI agents health and status"""
        try:
            # Import here to avoid circular imports
            from cmp.agents.accountant import accountant
            from cmp.agents.cfo import cfo
            from cmp.agents.controller import controller
            from cmp.agents.director import director
            
            agents_status = {}
            for name, agent in [
                ("accountant", accountant),
                ("cfo", cfo),
                ("controller", controller),
                ("director", director)
            ]:
                try:
                    # Check if agent has a status method
                    if hasattr(agent, 'get_status'):
                        if asyncio.iscoroutinefunction(agent.get_status):
                            status = await agent.get_status()
                        else:
                            status = agent.get_status()
                    else:
                        status = {"status": "available", "message": "Agent loaded"}
                    
                    agents_status[name] = status
                except Exception as e:
                    agents_status[name] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            return {
                "status": "checked",
                "agents": agents_status
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to check agents: {str(e)}"
            }
    
    async def get_comprehensive_health(self, db_session=None) -> Dict[str, Any]:
        """Get comprehensive health report"""
        health_report = {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": self.get_uptime(),
            "system": self.get_system_metrics(),
            "performance": performance_metrics.get_stats()
        }
        
        # Add database health if session provided
        if db_session:
            health_report["database"] = await self.check_database_health(db_session)
        
        # Add agents health
        health_report["agents"] = await self.check_agents_health()
        
        # Run custom health checks
        if self.health_checks:
            custom_checks = {}
            for name, check_func in self.health_checks.items():
                try:
                    if asyncio.iscoroutinefunction(check_func):
                        result = await check_func()
                    else:
                        result = check_func()
                    custom_checks[name] = result
                except Exception as e:
                    custom_checks[name] = {
                        "status": "error",
                        "error": str(e)
                    }
            health_report["custom_checks"] = custom_checks
        
        return health_report


# Global instances
system_health_monitor = SystemHealthMonitor()


def log_performance(message: str, **context):
    """Log performance-related information"""
    contextual_logger.info(f"PERFORMANCE: {message}", **context)


def log_error_with_context(error: Exception, **context):
    """Log error with full context and traceback"""
    contextual_logger.error(
        f"ERROR: {str(error)}",
        error_type=type(error).__name__,
        traceback=traceback.format_exc(),
        **context
    )


def setup_monitoring_middleware(app):
    """Setup monitoring middleware for FastAPI app"""
    
    @app.middleware("http")
    async def monitoring_middleware(request, call_next):
        start_time = time.time()
        
        # Add request context
        with contextual_logger.context_manager(
            request_id=f"{int(time.time() * 1000)}",
            endpoint=request.url.path,
            method=request.method
        ):
            try:
                response = await call_next(request)
                duration = time.time() - start_time
                
                # Record metrics
                performance_metrics.record_request(
                    endpoint=request.url.path,
                    duration=duration,
                    status_code=response.status_code
                )
                
                # Log request
                contextual_logger.info(
                    f"Request completed",
                    duration=round(duration, 3),
                    status_code=response.status_code
                )
                
                return response
            
            except Exception as e:
                duration = time.time() - start_time
                performance_metrics.record_request(
                    endpoint=request.url.path,
                    duration=duration,
                    status_code=500
                )
                
                log_error_with_context(
                    e,
                    duration=duration,
                    request_path=request.url.path
                )
                raise


# Export key components
__all__ = [
    'PerformanceMetrics',
    'ContextualLogger', 
    'SystemHealthMonitor',
    'performance_metrics',
    'contextual_logger',
    'system_health_monitor',
    'performance_monitor',
    'log_performance',
    'log_error_with_context',
    'setup_monitoring_middleware'
]