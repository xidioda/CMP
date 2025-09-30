
from fastapi import APIRouter, Depends
from datetime import datetime
from typing import Dict, Any, List
from ..auth import get_current_user
from ..utils.autonomous_scheduler import autonomous_scheduler

router = APIRouter(prefix="/api/v1/autonomous", tags=["autonomous"])

@router.get("/status")
async def get_autonomous_status(current_user: dict = Depends(get_current_user)):
    """Get current autonomous system status"""
    return {
        "status": "active",
        "agents_count": len(autonomous_scheduler.agents),
        "last_execution": autonomous_scheduler.last_execution,
        "total_tasks_executed": autonomous_scheduler.total_tasks_executed,
        "timestamp": datetime.now().isoformat()
    }

@router.get("/agents")
async def list_autonomous_agents(current_user: dict = Depends(get_current_user)):
    """List all registered autonomous agents"""
    return {
        "agents": [{"name": name, "active": True} for name in autonomous_scheduler.agents.keys()],
        "total": len(autonomous_scheduler.agents)
    }

@router.post("/trigger/{agent_name}")
async def trigger_agent_manually(agent_name: str, current_user: dict = Depends(get_current_user)):
    """Manually trigger a specific autonomous agent"""
    if agent_name in autonomous_scheduler.agents:
        result = await autonomous_scheduler.execute_agent_task(agent_name)
        return {"success": True, "result": result}
    else:
        return {"success": False, "error": "Agent not found"}
