from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from ..db import get_db
from ..utils.monitoring import system_health_monitor, performance_metrics

router = APIRouter()


@router.get("/healthz")
async def healthz():
    """Basic health check endpoint"""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@router.get("/health/detailed")
async def detailed_health(db: Session = Depends(get_db)):
    """Comprehensive health check with system metrics"""
    return await system_health_monitor.get_comprehensive_health(db)


@router.get("/health/performance")
async def performance_stats():
    """Get performance metrics and statistics"""
    return {
        "performance_metrics": performance_metrics.get_stats(),
        "system_metrics": system_health_monitor.get_system_metrics(),
        "uptime": system_health_monitor.get_uptime()
    }


@router.get("/health/agents")
async def agents_health():
    """Check AI agents health status"""
    return await system_health_monitor.check_agents_health()
