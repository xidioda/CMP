"""
Agent Control Panel Router
Handles routes for individual AI agent control panels and interactions
"""

from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import json

from ..models import User
from ..utils.monitoring import performance_metrics
from ..utils.ai_service import ai_service
from ..logging_config import get_logger
from .auth import get_current_user

# Import all AI agents
from ..agents.accountant import accountant
from ..agents.cfo import cfo
from ..agents.controller import controller
from ..agents.director import director

# Executive Leadership
from ..agents.ceo import ceo
from ..agents.cto import cto
from ..agents.cmo import cmo

# Operations Department  
from ..agents.coo import coo
from ..agents.pmo import pmo
from ..agents.project_manager import project_manager_general as project_manager
from ..agents.operations_manager import operations_manager

# Development Department
from ..agents.lead_developer import lead_developer
from ..agents.devops_engineer import devops_engineer
from ..agents.n8n_manager import n8n_manager

# Marketing & Sales Department
from ..agents.sales_manager import sales_manager
from ..agents.marketing_manager import marketing_manager
from ..agents.customer_success_manager import customer_success_manager

logger = get_logger("agents_router")

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(prefix="/agents", tags=["agent-panels"])

# Agent registry for dynamic routing
AGENTS = {
    # Finance Department (Original)
    "accountant": {
        "instance": accountant,
        "name": "AI Accountant",
        "icon": "fas fa-calculator",
        "color": "#10b981",
        "description": "Intelligent bookkeeping, transaction categorization, and invoice processing",
        "department": "Finance"
    },
    "cfo": {
        "instance": cfo,
        "name": "AI CFO", 
        "icon": "fas fa-chart-line",
        "color": "#3b82f6",
        "description": "Strategic financial planning, modeling, and business intelligence",
        "department": "Finance"
    },
    "controller": {
        "instance": controller,
        "name": "AI Controller",
        "icon": "fas fa-shield-alt", 
        "color": "#f59e0b",
        "description": "Financial controls, compliance monitoring, and risk assessment",
        "department": "Finance"
    },
    "director": {
        "instance": director,
        "name": "AI Director",
        "icon": "fas fa-briefcase",
        "color": "#8b5cf6", 
        "description": "Cash flow management, payment authorization, and executive reporting",
        "department": "Finance"
    },
    
    # Executive Leadership
    "ceo": {
        "instance": ceo,
        "name": "AI CEO",
        "icon": "fas fa-crown",
        "color": "#dc2626",
        "description": "Strategic vision, business operations, and organizational leadership",
        "department": "Executive"
    },
    "cto": {
        "instance": cto,
        "name": "AI CTO",
        "icon": "fas fa-microchip",
        "color": "#7c3aed",
        "description": "Technology strategy, architecture, and innovation leadership",
        "department": "Executive"
    },
    "cmo": {
        "instance": cmo,
        "name": "AI CMO",
        "icon": "fas fa-bullhorn",
        "color": "#ec4899",
        "description": "Marketing strategy, brand development, and market positioning",
        "department": "Executive"
    },
    
    # Operations Department
    "coo": {
        "instance": coo,
        "name": "AI COO",
        "icon": "fas fa-cogs",
        "color": "#059669",
        "description": "Operations strategy, process optimization, and performance management",
        "department": "Operations"
    },
    "pmo": {
        "instance": pmo,
        "name": "AI PMO",
        "icon": "fas fa-project-diagram",
        "color": "#0891b2",
        "description": "Portfolio management, governance, and strategic project oversight",
        "department": "Operations"
    },
    "project_manager": {
        "instance": project_manager,
        "name": "AI Project Manager",
        "icon": "fas fa-tasks",
        "color": "#06b6d4",
        "description": "Project planning, execution, and delivery management",
        "department": "Operations"
    },
    "operations_manager": {
        "instance": operations_manager,
        "name": "AI Operations Manager",
        "icon": "fas fa-industry",
        "color": "#84cc16",
        "description": "Daily operations, resource management, and process coordination",
        "department": "Operations"
    },
    
    # Development Department
    "lead_developer": {
        "instance": lead_developer,
        "name": "AI Lead Developer",
        "icon": "fas fa-code",
        "color": "#6366f1",
        "description": "AI-powered development, code generation, and technical leadership",
        "department": "Development"
    },
    "devops_engineer": {
        "instance": devops_engineer,
        "name": "AI DevOps Engineer",
        "icon": "fas fa-server",
        "color": "#0f172a",
        "description": "Infrastructure automation, CI/CD, and deployment management",
        "department": "Development"
    },
    "n8n_manager": {
        "instance": n8n_manager,
        "name": "AI N8N Manager",
        "icon": "fas fa-share-alt",
        "color": "#ea580c",
        "description": "Workflow automation, integration management, and process orchestration",
        "department": "Development"
    },
    
    # Marketing & Sales Department
    "sales_manager": {
        "instance": sales_manager,
        "name": "AI Sales Manager",
        "icon": "fas fa-handshake",
        "color": "#16a34a",
        "description": "Lead qualification, sales pipeline, and revenue generation",
        "department": "Marketing & Sales"
    },
    "marketing_manager": {
        "instance": marketing_manager,
        "name": "AI Marketing Manager",
        "icon": "fas fa-chart-pie",
        "color": "#d946ef",
        "description": "Marketing strategy, content creation, and brand development",
        "department": "Marketing & Sales"
    },
    "customer_success_manager": {
        "instance": customer_success_manager,
        "name": "AI Customer Success Manager",
        "icon": "fas fa-heart",
        "color": "#f97316",
        "description": "Customer onboarding, success planning, and retention management",
        "department": "Marketing & Sales"
    }
}


@router.get("/", response_class=HTMLResponse)
async def agents_overview(request: Request):
    """Overview page of all AI agents with quick access panels - authentication handled by JavaScript"""
    
    # Return basic template without authentication - JavaScript will load data
    return templates.TemplateResponse(
        request,
        "agents_overview.html",
        {
            "request": request,
            "agents": AGENTS  # Basic agent config without status
        }
    )


@router.get("/{agent_id}", response_class=HTMLResponse)
async def agent_control_panel(
    agent_id: str, 
    request: Request
):
    """Individual agent control panel with chat, KPIs, and controls - authentication handled by JavaScript"""
    
    if agent_id not in AGENTS:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    
    agent_config = AGENTS[agent_id]
    
    # Provide default KPIs to prevent template errors - JavaScript will load real data
    default_kpis = get_default_kpis(agent_id)
    
    # Return generic template that works for all agents
    return templates.TemplateResponse(
        request,
        "agent_generic.html",
        {
            "request": request,
            "agent": agent_config,
            "agent_id": agent_id,
            "kpis": default_kpis  # Provide default KPIs to prevent template errors
        }
    )


# API Endpoints for JavaScript to call with authentication

def sanitize_for_json(obj):
    """Recursively sanitize objects to be JSON-serializable"""
    if obj is None:
        return None
    elif isinstance(obj, (str, int, float, bool)):
        return obj
    elif isinstance(obj, (datetime)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: sanitize_for_json(value) for key, value in obj.items() 
                if not hasattr(value, '__dict__') or not str(type(value)).startswith('<class \'aiohttp')}
    elif isinstance(obj, (list, tuple)):
        return [sanitize_for_json(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        # For objects with __dict__, check if it's a known problematic type
        if str(type(obj)).startswith('<class \'aiohttp'):
            return str(obj)  # Convert aiohttp objects to string representation
        try:
            return {key: sanitize_for_json(value) for key, value in obj.__dict__.items()}
        except:
            return str(obj)
    else:
        return str(obj)

@router.get("/api/status")
async def get_all_agents_status(current_user: User = Depends(get_current_user)):
    """API endpoint to get status for all agents - used by JavaScript"""
    
    agents_status = {}
    for agent_id, agent_config in AGENTS.items():
        try:
            status = await agent_config["instance"].get_status()
            # Sanitize the status to ensure JSON serialization
            sanitized_status = sanitize_for_json(status)
            
            agents_status[agent_id] = {
                "name": agent_config["name"],
                "icon": agent_config["icon"],
                "color": agent_config["color"],
                "description": agent_config["description"],
                "department": agent_config["department"],
                "status": sanitized_status,
                "is_active": True
            }
        except Exception as e:
            logger.error(f"Failed to get status for {agent_id}: {e}")
            agents_status[agent_id] = {
                "name": agent_config["name"],
                "icon": agent_config["icon"],
                "color": agent_config["color"],
                "description": agent_config["description"],
                "department": agent_config["department"],
                "status": {"status": "offline", "error": str(e)},
                "is_active": False
            }
    
    logger.info(f"Agents status API accessed by user: {current_user.email}")
    return {"agents": agents_status}


@router.get("/api/{agent_id}/data")
async def get_agent_data(agent_id: str, current_user: User = Depends(get_current_user)):
    """API endpoint to get full agent data including status and KPIs - used by JavaScript"""
    
    if agent_id not in AGENTS:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    
    agent_config = AGENTS[agent_id]
    
    try:
        # Get agent status and KPIs
        status = await agent_config["instance"].get_status()
        kpis = await get_agent_kpis(agent_id, agent_config["instance"])
        
        # Sanitize both status and kpis
        sanitized_status = sanitize_for_json(status)
        sanitized_kpis = sanitize_for_json(kpis)
        
        logger.info(f"Agent {agent_id} data API accessed by user: {current_user.email}")
        
        return {
            "agent": {
                "name": agent_config["name"],
                "icon": agent_config["icon"], 
                "color": agent_config["color"],
                "description": agent_config["description"],
                "department": agent_config["department"],
                "status": sanitized_status,
                "is_active": True
            },
            "agent_id": agent_id,
            "kpis": sanitized_kpis,
            "user": {"email": current_user.email, "role": current_user.role.value}
        }
    except Exception as e:
        logger.error(f"Failed to load agent {agent_id} data: {e}")
        return {
            "agent": {
                "name": agent_config["name"],
                "icon": agent_config["icon"],
                "color": agent_config["color"], 
                "description": agent_config["description"],
                "department": agent_config["department"],
                "status": {"status": "offline", "error": str(e)},
                "is_active": False
            },
            "agent_id": agent_id,
            "kpis": get_default_kpis(agent_id),
            "user": {"email": current_user.email, "role": current_user.role.value},
            "error": str(e)
        }


# Individual Agent Detail Page Data API - NO AUTH for testing
@router.get("/api/{agent_id}/detail-data")
async def get_individual_agent_detail_data(agent_id: str):
    """Get detailed data for individual agent pages - temporary no auth for testing"""
    try:
        if agent_id not in AGENTS:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
        
        agent = AGENTS[agent_id]["instance"]
        agent_config = AGENTS[agent_id]
        
        # Initialize default data
        agent_data = {
            "status": "active",
            "current_tasks": "0",
            "completed_today": "0", 
            "active_time": "02:45",
            "efficiency": "95",
            "current_activity": "Standard operations",
            "proactive_tasks": [],
            "capabilities": []
        }
        
        try:
            # Get proactive tasks if available
            if hasattr(agent, 'get_current_proactive_tasks'):
                proactive_tasks = agent.get_current_proactive_tasks()
                if isinstance(proactive_tasks, list):
                    agent_data["proactive_tasks"] = proactive_tasks
                    agent_data["current_tasks"] = str(len(proactive_tasks))
                    
                    # Calculate completed today (simulate based on task progress)
                    completed_today = sum(1 for task in proactive_tasks if task.get('progress', 0) >= 100)
                    agent_data["completed_today"] = str(completed_today)
                    
                    # Set current activity to the first active task
                    active_tasks = [task for task in proactive_tasks if task.get('status') == 'in_progress']
                    if active_tasks:
                        agent_data["current_activity"] = active_tasks[0].get('title', 'Processing tasks')
                    elif proactive_tasks:
                        agent_data["current_activity"] = f"Managing {len(proactive_tasks)} proactive tasks"
            
            # Get agent capabilities
            if hasattr(agent, 'capabilities'):
                agent_data["capabilities"] = agent.capabilities
            elif hasattr(agent, 'specialization'):
                agent_data["capabilities"] = [agent.specialization]
            else:
                # Default capabilities based on agent type
                role = getattr(agent, 'role', agent_id).replace('_', ' ').title()
                if 'ceo' in agent_id.lower():
                    agent_data["capabilities"] = [
                        "Strategic Leadership",
                        "Organizational Vision",
                        "Decision Making", 
                        "Team Coordination",
                        "Business Strategy"
                    ]
                elif 'cfo' in agent_id.lower():
                    agent_data["capabilities"] = [
                        "Financial Planning",
                        "Budget Management",
                        "Investment Analysis",
                        "Risk Assessment",
                        "Performance Metrics"
                    ]
                elif 'cto' in agent_id.lower():
                    agent_data["capabilities"] = [
                        "Technology Strategy",
                        "System Architecture",
                        "Innovation Management",
                        "Technical Leadership",
                        "Digital Transformation"
                    ]
                elif 'cmo' in agent_id.lower():
                    agent_data["capabilities"] = [
                        "Marketing Strategy",
                        "Brand Management",
                        "Digital Marketing",
                        "Customer Engagement",
                        "Market Analysis"
                    ]
                elif 'coo' in agent_id.lower():
                    agent_data["capabilities"] = [
                        "Operations Management",
                        "Process Optimization",
                        "Resource Allocation",
                        "Quality Control",
                        "Workflow Coordination"
                    ]
                else:
                    agent_data["capabilities"] = [
                        f"{role} Operations",
                        "Task Management",
                        "Process Execution",
                        "Quality Assurance",
                        "Performance Optimization"
                    ]
            
            # Calculate efficiency based on task progress
            if agent_data["proactive_tasks"]:
                total_progress = sum(task.get('progress', 0) for task in agent_data["proactive_tasks"])
                avg_progress = total_progress / len(agent_data["proactive_tasks"])
                agent_data["efficiency"] = str(int(80 + (avg_progress * 0.2)))  # 80-100% range
            
            # Simulate active time (in production, this would be real tracking)
            import random
            hours = random.randint(1, 8)
            minutes = random.randint(0, 59)
            agent_data["active_time"] = f"{hours:02d}:{minutes:02d}"
            
            logger.info(f"Successfully loaded detail data for agent {agent_id}")
            return agent_data
            
        except Exception as e:
            logger.error(f"Error getting detailed data for agent {agent_id}: {e}")
            # Return default data with error indication
            agent_data["status"] = "warning"
            agent_data["current_activity"] = "Data loading issue"
            return agent_data
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in individual agent detail data endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/{agent_id}/data")
async def get_agent_data(agent_id: str, current_user: User = Depends(get_current_user)):
    """API endpoint to get full agent data including status and KPIs - used by JavaScript"""
    
    if agent_id not in AGENTS:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    
    agent_config = AGENTS[agent_id]
    
    try:
        # Get agent status and KPIs
        status = await agent_config["instance"].get_status()
        kpis = await get_agent_kpis(agent_id, agent_config["instance"])
        
        # Sanitize both status and kpis
        sanitized_status = sanitize_for_json(status)
        sanitized_kpis = sanitize_for_json(kpis)
        
        logger.info(f"Agent {agent_id} data API accessed by user: {current_user.email}")
        
        return {
            "agent": {
                "name": agent_config["name"],
                "icon": agent_config["icon"], 
                "color": agent_config["color"],
                "description": agent_config["description"],
                "department": agent_config["department"],
                "status": sanitized_status,
                "is_active": True
            },
            "agent_id": agent_id,
            "kpis": sanitized_kpis,
            "user": {"email": current_user.email, "role": current_user.role.value}
        }
    except Exception as e:
        logger.error(f"Failed to load agent {agent_id} data: {e}")
        return {
            "agent": {
                "name": agent_config["name"],
                "icon": agent_config["icon"],
                "color": agent_config["color"], 
                "description": agent_config["description"],
                "department": agent_config["department"],
                "status": {"status": "offline", "error": str(e)},
                "is_active": False
            },
            "agent_id": agent_id,
            "kpis": get_default_kpis(agent_id),
            "user": {"email": current_user.email, "role": current_user.role.value},
            "error": str(e)
        }


@router.post("/{agent_id}/chat")
async def chat_with_agent(
    agent_id: str,
    message: str = Form(...)
):
    """Send a message to an AI agent and get response - authentication handled by frontend"""
    
    if agent_id not in AGENTS:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    
    agent_instance = AGENTS[agent_id]["instance"]
    
    try:
        # Process the chat message with the agent (using a mock user for now)
        mock_user = type('MockUser', (), {
            'username': 'authenticated_user',
            'email': 'user@cmp.com',
            'full_name': 'CMP User'
        })()
        
        response = await process_agent_chat(agent_id, message, agent_instance, mock_user)
        
        return JSONResponse({
            "success": True,
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "agent": AGENTS[agent_id]["name"]
        })
        
    except Exception as e:
        logger.error(f"Chat error with {agent_id}: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, status_code=500)


@router.post("/{agent_id}/task")
async def assign_task_to_agent(
    agent_id: str,
    task_type: str = Form(...),
    task_data: str = Form(...)
):
    """Assign a specific task to an AI agent - authentication handled by frontend"""
    
    if agent_id not in AGENTS:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    
    agent_instance = AGENTS[agent_id]["instance"]
    
    try:
        task_data_parsed = json.loads(task_data) if task_data else {}
        
        # Execute agent-specific task
        result = await execute_agent_task(agent_id, task_type, task_data_parsed, agent_instance)
        
        return JSONResponse({
            "success": True,
            "result": result,
            "task_type": task_type,
            "timestamp": datetime.now().isoformat(),
            "agent": AGENTS[agent_id]["name"]
        })
        
    except Exception as e:
        logger.error(f"Task execution error for {agent_id}: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, status_code=500)


@router.get("/{agent_id}/kpis")
async def get_agent_kpis_endpoint(
    agent_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get real-time KPIs for a specific agent"""
    
    if agent_id not in AGENTS:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    
    try:
        agent_instance = AGENTS[agent_id]["instance"]
        kpis = await get_agent_kpis(agent_id, agent_instance)
        
        return JSONResponse({
            "success": True,
            "kpis": kpis,
            "timestamp": datetime.now().isoformat(),
            "agent": AGENTS[agent_id]["name"]
        })
        
    except Exception as e:
        logger.error(f"Error fetching KPIs for {agent_id}: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, status_code=500)


async def get_agent_kpis(agent_id: str, agent_instance) -> Dict[str, Any]:
    """Get KPIs specific to each agent type"""
    
    kpis = {}
    
    if agent_id == "accountant":
        kpis = {
            "transactions_processed": len(getattr(agent_instance, 'processed_invoices', [])),
            "ai_insights_generated": len(getattr(agent_instance, 'ai_insights', [])),
            "categorization_accuracy": 95.8,  # Mock data - could be real from ML model
            "invoices_processed_today": 12,
            "bank_reconciliation_status": "Up to date",
            "performance_metrics": getattr(agent_instance, 'performance_metrics', {})
        }
    
    elif agent_id == "cfo":
        kpis = {
            "financial_models_active": 3,
            "revenue_growth_forecast": "18.5%",
            "strategic_recommendations": 5,
            "scenario_analyses_run": 8,
            "investment_opportunities": 2,
            "performance_metrics": getattr(agent_instance, 'performance_metrics', {})
        }
    
    elif agent_id == "controller":
        kpis = {
            "policy_violations_detected": 2,
            "budget_variance_alerts": 1,
            "fraud_risk_score": "Low",
            "compliance_checks_passed": "98%",
            "a_p_aging_status": "Good",
            "risk_assessments": 4
        }
    
    elif agent_id == "director":
        kpis = {
            "cash_flow_projection": "Positive",
            "payment_approvals_pending": 3,
            "monthly_p_l_status": "Generated",
            "executive_reports": 2,
            "kpi_targets_met": "85%",
            "strategic_decisions": 6
        }
    
    return kpis


def get_default_kpis(agent_id: str) -> Dict[str, Any]:
    """Get default KPIs when agent is offline or has errors"""
    
    if agent_id == "accountant":
        return {
            "transactions_processed": 0,
            "ai_insights_generated": 0,
            "categorization_accuracy": 0.0,  # Use numeric value instead of "N/A"
            "invoices_processed_today": 0,
            "bank_reconciliation_status": "Offline",
            "performance_metrics": {
                "cache_hit_rate": 0.0,
                "avg_processing_time": 0.0,
                "error_rate": 0.0,
                "total_operations": 0,
                "errors_count": 0
            }
        }
    
    elif agent_id == "cfo":
        return {
            "financial_models_active": 0,
            "revenue_growth_forecast": "0%",  # Keep as string for display
            "strategic_recommendations": 0,
            "scenario_analyses_run": 0,
            "investment_opportunities": 0,
            "performance_metrics": {
                "models_generated": 0,
                "scenarios_analyzed": 0,
                "optimization_cycles": 0,
                "total_processing_time": 0,
                "last_operation_time": None,
                "errors_count": 0
            }
        }
    
    elif agent_id == "controller":
        return {
            "policy_violations_detected": 0,  # Use numeric values
            "budget_variance_alerts": 0,
            "fraud_risk_score": 0.0,
            "compliance_checks_passed": 0,
            "a_p_aging_status": "Offline",
            "risk_assessments": 0,
            "performance_metrics": {
                "compliance_rate": 0.0,
                "risk_assessments_completed": 0,
                "policy_checks": 0,
                "violations_detected": 0,
                "errors_count": 0
            }
        }
    
    elif agent_id == "director":
        return {
            "cash_flow_projection": "0",  # Keep as string for display
            "payment_approvals_pending": 0,  # Use numeric
            "monthly_p_l_status": "Offline",
            "executive_reports": 0,
            "kpi_targets_met": 0.0,  # Use numeric
            "strategic_decisions": 0,
            "performance_metrics": {
                "pending_tasks": 0,
                "kpis_met": 0.0,
                "reports_generated": 0,
                "decisions_made": 0,
                "errors_count": 0
            }
        }
    
    return {}


async def process_agent_chat(agent_id: str, message: str, agent_instance, user: User) -> Dict[str, Any]:
    """Process chat messages with intelligent AI-powered agent responses"""
    
    # Get agent status for context
    try:
        agent_status = await agent_instance.get_status()
    except:
        agent_status = {"status": "active"}
    
    # Get default KPIs for additional context
    default_kpis = get_default_kpis(agent_id)
    
    # Build context for AI
    context = {
        "status": agent_status,
        "kpis": default_kpis,
        "user": user.username if hasattr(user, 'username') else "User"
    }
    
    # Generate AI-powered response with database update capabilities
    response = await ai_service.process_message_with_db_updates(agent_id, message, context)
    
    return response


async def generate_accountant_response(message: str, status: Dict, instance) -> Dict[str, Any]:
    """Generate intelligent responses for AI Accountant"""
    
    message_lower = message.lower()
    
    if any(word in message_lower for word in ["status", "how are you", "what's up"]):
        perf_metrics = getattr(instance, 'performance_metrics', {})
        return {
            "message": f"I'm operating well! I've processed {perf_metrics.get('operations_count', 0)} operations with an average processing time of {perf_metrics.get('total_processing_time', 0):.2f}s. My categorization cache has {perf_metrics.get('cache_hits', 0)} hits.",
            "type": "status_update",
            "data": perf_metrics,
            "suggestions": ["Categorize new transactions", "Process bank statements", "Generate reconciliation report"]
        }
    
    elif any(word in message_lower for word in ["categorize", "transaction", "classify"]):
        return {
            "message": "I can help categorize transactions using my AI model. I have intelligent caching that improves performance over time. Would you like me to categorize recent transactions or analyze a specific transaction?",
            "type": "capability_info",
            "suggestions": ["Categorize recent transactions", "Analyze transaction patterns", "Show categorization accuracy"]
        }
    
    elif any(word in message_lower for word in ["invoice", "ocr", "document"]):
        return {
            "message": "I can process invoices using OCR and extract key information automatically. I analyze vendor details, amounts, and categorize expenses intelligently. Upload an invoice and I'll handle the rest!",
            "type": "capability_info",
            "suggestions": ["Process uploaded invoice", "Show invoice processing stats", "Generate expense report"]
        }
    
    elif any(word in message_lower for word in ["bank", "reconcile", "statement"]):
        return {
            "message": "I handle bank reconciliation automatically by fetching data from Emirates NBD and other sources. I can detect anomalies and ensure all transactions are properly categorized.",
            "type": "capability_info",
            "suggestions": ["Run bank reconciliation", "Fetch recent transactions", "Show reconciliation status"]
        }
    
    else:
        return {
            "message": "I'm your AI Accountant, specializing in intelligent transaction processing, OCR invoice analysis, and automated bank reconciliation. What would you like me to help you with?",
            "type": "general_help",
            "suggestions": ["Show my capabilities", "Process recent transactions", "Generate financial report"]
        }


async def generate_cfo_response(message: str, status: Dict, instance) -> Dict[str, Any]:
    """Generate intelligent responses for AI CFO"""
    
    message_lower = message.lower()
    
    if any(word in message_lower for word in ["status", "how are you", "performance"]):
        perf_metrics = getattr(instance, 'performance_metrics', {})
        return {
            "message": f"I'm strategically focused and running optimally! I've generated {perf_metrics.get('models_generated', 0)} financial models and analyzed {perf_metrics.get('scenarios_analyzed', 0)} scenarios. Strategic planning is my forte.",
            "type": "status_update", 
            "data": perf_metrics,
            "suggestions": ["Generate financial forecast", "Run scenario analysis", "Review strategic KPIs"]
        }
    
    elif any(word in message_lower for word in ["forecast", "model", "projection"]):
        return {
            "message": "I create sophisticated financial models with AI-powered projections. I can generate 3-year forecasts, revenue projections, and scenario analyses with Monte Carlo simulations.",
            "type": "capability_info",
            "suggestions": ["Generate 3-year model", "Create revenue forecast", "Run sensitivity analysis"]
        }
    
    elif any(word in message_lower for word in ["kpi", "metrics", "performance"]):
        strategic_kpis = getattr(instance, 'strategic_kpis', {})
        return {
            "message": f"I monitor key strategic KPIs including revenue growth target ({strategic_kpis.get('revenue_growth_target', 0.2)*100:.0f}%), EBITDA margin target ({strategic_kpis.get('ebitda_margin_target', 0.25)*100:.0f}%), and ROE target ({strategic_kpis.get('return_on_equity_target', 0.15)*100:.0f}%).",
            "type": "kpi_info",
            "data": strategic_kpis,
            "suggestions": ["Review all KPIs", "Update targets", "Generate executive dashboard"]
        }
    
    else:
        return {
            "message": "I'm your AI CFO, responsible for strategic financial planning, advanced modeling, and business intelligence. I help with long-term vision and executive decision-making.",
            "type": "general_help", 
            "suggestions": ["Show strategic overview", "Generate executive report", "Plan growth scenarios"]
        }


async def generate_controller_response(message: str, status: Dict, instance) -> Dict[str, Any]:
    """Generate intelligent responses for AI Controller"""
    
    message_lower = message.lower()
    
    if any(word in message_lower for word in ["status", "compliance", "controls"]):
        return {
            "message": "All financial controls are active and monitoring effectively. I've detected no major policy violations and all compliance checks are passing. Risk assessment is ongoing.",
            "type": "status_update",
            "suggestions": ["Review policy violations", "Check budget variance", "Run risk assessment"]
        }
    
    elif any(word in message_lower for word in ["budget", "variance", "analysis"]):
        return {
            "message": "I continuously monitor budget vs. actuals with a 15% variance threshold. I can provide detailed variance analysis and flag any concerning trends.",
            "type": "capability_info",
            "suggestions": ["Show budget analysis", "Review variances", "Generate budget report"]
        }
    
    elif any(word in message_lower for word in ["risk", "fraud", "security"]):
        risk_thresholds = getattr(instance, 'risk_thresholds', {})
        return {
            "message": f"I monitor for fraud and risk with thresholds including high-value transactions over {risk_thresholds.get('high_value_transaction', 10000):,} AED. Current risk level is low.",
            "type": "risk_info",
            "data": risk_thresholds,
            "suggestions": ["Run fraud scan", "Review risk thresholds", "Check policy compliance"]
        }
    
    else:
        return {
            "message": "I'm your AI Controller, ensuring financial accuracy, policy compliance, and risk management. I provide oversight and control for all financial operations.",
            "type": "general_help",
            "suggestions": ["Review controls status", "Check compliance", "Analyze risks"]
        }


async def generate_director_response(message: str, status: Dict, instance) -> Dict[str, Any]:
    """Generate intelligent responses for AI Director"""
    
    message_lower = message.lower()
    
    if any(word in message_lower for word in ["status", "cash", "flow"]):
        return {
            "message": "Cash flow management is on track. I've reviewed payment runs and authorized transactions within limits. Monthly performance summaries are up to date.",
            "type": "status_update",
            "suggestions": ["Review cash position", "Check pending payments", "Generate monthly report"]
        }
    
    elif any(word in message_lower for word in ["payment", "authorization", "approve"]):
        payment_limits = getattr(instance, 'payment_limits', {})
        return {
            "message": f"I manage payment authorizations with limits: single payment {payment_limits.get('single_payment', 10000):,} AED, daily total {payment_limits.get('daily_total', 50000):,} AED. All within policy.",
            "type": "payment_info",
            "data": payment_limits,
            "suggestions": ["Review pending payments", "Check authorization limits", "Process payment run"]
        }
    
    elif any(word in message_lower for word in ["report", "executive", "summary"]):
        return {
            "message": "I prepare comprehensive executive reports including P&L, Balance Sheet, and KPI summaries. Board-ready presentations are my specialty.",
            "type": "capability_info",
            "suggestions": ["Generate executive summary", "Create board report", "Review monthly P&L"]
        }
    
    else:
        return {
            "message": "I'm your AI Director, responsible for strategic financial management, cash flow oversight, and executive reporting. How can I assist with strategic decisions?",
            "type": "general_help",
            "suggestions": ["Review strategic position", "Generate executive dashboard", "Check payment status"]
        }


async def execute_agent_task(agent_id: str, task_type: str, task_data: Dict, agent_instance) -> Dict[str, Any]:
    """Execute specific tasks for each agent type"""
    
    try:
        if agent_id == "accountant":
            if task_type == "categorize_transactions":
                # This would call the actual agent method
                return {"status": "Task queued", "message": "Transaction categorization started"}
            elif task_type == "reconcile_bank":
                return {"status": "Task queued", "message": "Bank reconciliation initiated"}
            elif task_type == "process_invoices":
                return {"status": "Task queued", "message": "Invoice processing started"}
            elif task_type == "generate_report":
                return {"status": "Task completed", "message": "Financial summary report generated successfully"}
                
        elif agent_id == "cfo":
            if task_type == "generate_forecast":
                # This would call the actual agent method
                return {"status": "Task queued", "message": "Financial forecast generation started"}
            elif task_type == "scenario_analysis":
                return {"status": "Task queued", "message": "Scenario analysis initiated"}
            elif task_type == "strategic_planning":
                return {"status": "Task queued", "message": "Strategic planning session initiated"}
                
        elif agent_id == "controller":
            if task_type == "compliance_check":
                return {"status": "Task queued", "message": "Compliance check started"}
            elif task_type == "risk_assessment":
                return {"status": "Task queued", "message": "Risk assessment initiated"}
            elif task_type == "policy_review":
                return {"status": "Task queued", "message": "Policy review and validation started"}
                
        elif agent_id == "director":
            if task_type == "cash_flow_analysis":
                return {"status": "Task queued", "message": "Cash flow analysis started"}
            elif task_type == "generate_executive_report":
                return {"status": "Task queued", "message": "Executive report generation started"}
            elif task_type == "strategic_decision":
                return {"status": "Task queued", "message": "Strategic decision analysis initiated"}
        
        return {"status": "Unknown task", "message": f"Task type '{task_type}' not recognized for {agent_id}"}
        
    except Exception as e:
        logger.error(f"Task execution failed for {agent_id}.{task_type}: {e}")
        return {"status": "Error", "message": f"Task execution failed: {str(e)}"}