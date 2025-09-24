"""
AI Project Manager Agent

Responsibilities:
- Individual project delivery and execution management
- Team coordination and task assignment
- Client communication and stakeholder management
- Project timeline and milestone tracking
- Risk identification and issue resolution
- Budget monitoring and resource management
- Quality assurance and delivery standards
- Progress reporting and status updates
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
import json
import random

from ..logging_config import get_logger
from ..utils.agent_zoho_tools import AgentZohoBooks
from ..utils.ai_service import AIAgentService
from ..db import session_scope
from ..models import append_ledger_entry

logger = get_logger("agents.project_manager")


class AIProjectManager:
    """AI Project Manager - individual project delivery and team coordination"""
    
    def __init__(self, project_id: str = None, specialization: str = "software_development"):
        self.name = f"AI:ProjectManager"
        self.project_id = project_id
        self.specialization = specialization
        self.zoho_tools = AgentZohoBooks(self.name)
        self.ai_service = AIAgentService()
        
        # Project management standards
        self.project_standards = {
            "on_time_delivery_target": 0.95,    # 95%
            "budget_variance_threshold": 0.10,  # 10%
            "quality_score_minimum": 0.90,      # 90%
            "team_utilization_optimal": 0.85,   # 85%
            "client_satisfaction_target": 0.92  # 92%
        }
        
        # Project phases and milestones
        self.project_phases = {
            "initiation": {"duration": 1, "key_deliverables": ["Project charter", "Requirements gathering"]},
            "planning": {"duration": 2, "key_deliverables": ["Project plan", "Resource allocation", "Risk register"]},
            "execution": {"duration": 8, "key_deliverables": ["Development", "Testing", "Documentation"]},
            "monitoring": {"duration": 10, "key_deliverables": ["Progress reports", "Quality reviews"]},
            "closure": {"duration": 1, "key_deliverables": ["Delivery", "Knowledge transfer", "Retrospective"]}
        }
        
        # Performance tracking
        self.performance_metrics = {
            "projects_managed": 0,
            "successful_deliveries": 0,
            "client_meetings": 0,
            "issues_resolved": 0,
            "team_meetings": 0,
            "last_status_update": None
        }
        
        logger.info(f"{self.name} initialized for {specialization} projects")
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current project manager status and project overview"""
        try:
            current_status = {
                "status": "active",
                "timestamp": datetime.now().isoformat(),
                "specialization": self.specialization,
                "assigned_project": self.project_id,
                "performance_metrics": self.performance_metrics
            }
            
            # If assigned to specific project, get project details
            if self.project_id:
                project_status = await self._get_project_status()
                current_status["project_status"] = project_status
            else:
                # Get overview of all projects
                projects_overview = await self._get_projects_overview()
                current_status["projects_overview"] = projects_overview
            
            # Get current workload and priorities
            workload_analysis = await self._analyze_current_workload()
            current_status["workload_analysis"] = workload_analysis
            
            # Get upcoming deadlines and milestones
            upcoming_items = await self._get_upcoming_deadlines()
            current_status["upcoming_deadlines"] = upcoming_items
            
            logger.info(f"{self.name}: Status retrieved successfully")
            return current_status
            
        except Exception as e:
            logger.error(f"{self.name}: Error getting status - {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def manage_daily_operations(self) -> Dict[str, Any]:
        """Perform daily project management operations"""
        logger.info(f"{self.name}: Conducting daily project management")
        
        try:
            daily_report = {
                "date": date.today().isoformat(),
                "project_status": {},
                "team_coordination": {},
                "client_communication": {},
                "risk_management": {},
                "action_items": [],
                "escalations": []
            }
            
            # 1. Project Status Update
            project_status = await self._update_project_status()
            daily_report["project_status"] = project_status
            
            # 2. Team Coordination
            team_coordination = await self._coordinate_team_activities()
            daily_report["team_coordination"] = team_coordination
            
            # 3. Client Communication
            client_communication = await self._manage_client_communication()
            daily_report["client_communication"] = client_communication
            
            # 4. Risk Management
            risk_management = await self._manage_project_risks()
            daily_report["risk_management"] = risk_management
            
            # 5. Generate Action Items
            action_items = await self._generate_daily_action_items(
                project_status, team_coordination, risk_management
            )
            daily_report["action_items"] = action_items
            
            # 6. Identify Escalations
            escalations = await self._identify_escalations(project_status, risk_management)
            daily_report["escalations"] = escalations
            
            # Update performance metrics
            self.performance_metrics["last_status_update"] = datetime.now().isoformat()
            
            # Log daily operations
            await self._log_project_activity(
                "daily_operations",
                daily_report,
                "Completed daily project management operations"
            )
            
            logger.info(f"{self.name}: Daily operations completed")
            return daily_report
            
        except Exception as e:
            logger.error(f"{self.name}: Error in daily operations - {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "action": "daily_operations"
            }
    
    async def coordinate_project_delivery(self, milestone: str = None) -> Dict[str, Any]:
        """Coordinate project delivery activities and milestone achievement"""
        logger.info(f"{self.name}: Coordinating project delivery")
        
        try:
            delivery_coordination = {
                "coordination_date": date.today().isoformat(),
                "current_milestone": milestone,
                "delivery_status": {},
                "team_assignments": {},
                "quality_checkpoints": {},
                "timeline_analysis": {},
                "delivery_plan": []
            }
            
            # 1. Assess Current Delivery Status
            delivery_status = await self._assess_delivery_status(milestone)
            delivery_coordination["delivery_status"] = delivery_status
            
            # 2. Coordinate Team Assignments
            team_assignments = await self._coordinate_team_assignments()
            delivery_coordination["team_assignments"] = team_assignments
            
            # 3. Manage Quality Checkpoints
            quality_checkpoints = await self._manage_quality_checkpoints(milestone)
            delivery_coordination["quality_checkpoints"] = quality_checkpoints
            
            # 4. Analyze Timeline and Progress
            timeline_analysis = await self._analyze_project_timeline()
            delivery_coordination["timeline_analysis"] = timeline_analysis
            
            # 5. Create Delivery Plan
            delivery_plan = await self._create_delivery_plan(
                delivery_status, timeline_analysis, milestone
            )
            delivery_coordination["delivery_plan"] = delivery_plan
            
            # Update performance metrics
            if milestone:
                self.performance_metrics["successful_deliveries"] += 1
            
            # Log delivery coordination
            await self._log_project_activity(
                "delivery_coordination",
                delivery_coordination,
                f"Coordinated project delivery for milestone: {milestone or 'general'}"
            )
            
            logger.info(f"{self.name}: Project delivery coordination completed")
            return delivery_coordination
            
        except Exception as e:
            logger.error(f"{self.name}: Error in delivery coordination - {str(e)}")
            return {
                "error": str(e),
                "milestone": milestone,
                "timestamp": datetime.now().isoformat()
            }
    
    async def manage_stakeholder_communication(self, communication_type: str = "regular_update") -> Dict[str, Any]:
        """Manage communication with project stakeholders"""
        logger.info(f"{self.name}: Managing stakeholder communication")
        
        try:
            communication_report = {
                "communication_date": date.today().isoformat(),
                "communication_type": communication_type,
                "stakeholder_engagement": {},
                "client_updates": {},
                "team_communication": {},
                "executive_reporting": {},
                "follow_up_actions": []
            }
            
            # 1. Client Updates and Engagement
            client_updates = await self._prepare_client_updates()
            communication_report["client_updates"] = client_updates
            
            # 2. Team Communication
            team_communication = await self._facilitate_team_communication()
            communication_report["team_communication"] = team_communication
            
            # 3. Executive Reporting
            if communication_type in ["milestone_report", "executive_summary"]:
                executive_reporting = await self._prepare_executive_reporting()
                communication_report["executive_reporting"] = executive_reporting
            
            # 4. Stakeholder Engagement Analysis
            stakeholder_engagement = await self._analyze_stakeholder_engagement()
            communication_report["stakeholder_engagement"] = stakeholder_engagement
            
            # 5. Follow-up Actions
            follow_up_actions = await self._identify_communication_follow_ups(
                client_updates, team_communication, stakeholder_engagement
            )
            communication_report["follow_up_actions"] = follow_up_actions
            
            # Update performance metrics
            self.performance_metrics["client_meetings"] += 1
            
            # Log communication activity
            await self._log_project_activity(
                "stakeholder_communication",
                communication_report,
                f"Managed stakeholder communication - {communication_type}"
            )
            
            logger.info(f"{self.name}: Stakeholder communication completed")
            return communication_report
            
        except Exception as e:
            logger.error(f"{self.name}: Error in stakeholder communication - {str(e)}")
            return {
                "error": str(e),
                "communication_type": communication_type,
                "timestamp": datetime.now().isoformat()
            }
    
    async def track_project_budget(self) -> Dict[str, Any]:
        """Track and manage project budget and expenses"""
        logger.info(f"{self.name}: Tracking project budget")
        
        try:
            budget_report = {
                "tracking_date": date.today().isoformat(),
                "budget_overview": {},
                "expense_analysis": {},
                "variance_analysis": {},
                "forecasting": {},
                "recommendations": []
            }
            
            # 1. Get Budget Overview
            budget_overview = await self._get_budget_overview()
            budget_report["budget_overview"] = budget_overview
            
            # 2. Analyze Project Expenses
            expense_analysis = await self._analyze_project_expenses()
            budget_report["expense_analysis"] = expense_analysis
            
            # 3. Budget Variance Analysis
            variance_analysis = self._calculate_budget_variance(budget_overview, expense_analysis)
            budget_report["variance_analysis"] = variance_analysis
            
            # 4. Budget Forecasting
            forecasting = await self._forecast_project_budget(expense_analysis)
            budget_report["forecasting"] = forecasting
            
            # 5. Generate Budget Recommendations
            recommendations = await self._generate_budget_recommendations(
                variance_analysis, forecasting
            )
            budget_report["recommendations"] = recommendations
            
            # Log budget tracking
            await self._log_project_activity(
                "budget_tracking",
                budget_report,
                "Completed project budget tracking and analysis"
            )
            
            logger.info(f"{self.name}: Project budget tracking completed")
            return budget_report
            
        except Exception as e:
            logger.error(f"{self.name}: Error in budget tracking - {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "action": "budget_tracking"
            }
    
    # Private helper methods
    
    async def _get_project_status(self) -> Dict[str, Any]:
        """Get status of assigned project"""
        if not self.project_id:
            return {"status": "no_project_assigned"}
        
        # Get project data from Zoho
        projects_data = await self.zoho_tools.get_projects_from_zoho()
        project = next((p for p in projects_data.get('projects', []) 
                       if p.get('id') == self.project_id), None)
        
        if not project:
            return {"status": "project_not_found", "project_id": self.project_id}
        
        return {
            "project_id": self.project_id,
            "project_name": project.get('name', 'Unknown'),
            "status": project.get('status', 'unknown'),
            "progress": "75%",  # Simulated
            "next_milestone": "Testing Phase",
            "health": "green"
        }
    
    async def _get_projects_overview(self) -> Dict[str, Any]:
        """Get overview of all projects"""
        projects_data = await self.zoho_tools.get_projects_from_zoho()
        projects = projects_data.get('projects', [])
        
        return {
            "total_projects": len(projects),
            "active_projects": len([p for p in projects if p.get('status', '').lower() == 'active']),
            "projects_on_track": len(projects) - 1,  # Simulated
            "projects_at_risk": 1,
            "upcoming_deliveries": 2
        }
    
    async def _analyze_current_workload(self) -> Dict[str, Any]:
        """Analyze current workload and capacity"""
        return {
            "current_capacity": "85%",
            "availability": "15%",
            "priority_tasks": [
                "Client review meeting - Project Alpha",
                "Code review - Feature X",
                "Budget reconciliation"
            ],
            "overdue_items": [],
            "team_capacity": {
                "developers": "90%",
                "designers": "70%",
                "qa": "85%"
            }
        }
    
    async def _get_upcoming_deadlines(self) -> List[Dict[str, Any]]:
        """Get upcoming deadlines and milestones"""
        return [
            {
                "type": "milestone",
                "title": "Alpha Testing Complete",
                "due_date": (datetime.now() + timedelta(days=5)).isoformat(),
                "priority": "high",
                "project": "Project Alpha"
            },
            {
                "type": "deliverable",
                "title": "Design Review",
                "due_date": (datetime.now() + timedelta(days=3)).isoformat(),
                "priority": "medium",
                "project": "Project Beta"
            }
        ]
    
    async def _update_project_status(self) -> Dict[str, Any]:
        """Update and assess current project status"""
        return {
            "overall_health": "green",
            "schedule_status": "on_track",
            "budget_status": "within_limits",
            "quality_status": "good",
            "team_morale": "high",
            "client_satisfaction": "excellent",
            "risk_level": "low"
        }
    
    async def _coordinate_team_activities(self) -> Dict[str, Any]:
        """Coordinate daily team activities"""
        return {
            "daily_standup": "completed",
            "task_assignments": {
                "new_assignments": 3,
                "completed_tasks": 5,
                "blocked_tasks": 1
            },
            "team_availability": {
                "developers": 3,
                "designers": 2,
                "qa": 2
            },
            "collaboration_issues": [],
            "productivity_score": 0.87
        }
    
    async def _manage_client_communication(self) -> Dict[str, Any]:
        """Manage client communication and updates"""
        return {
            "last_client_contact": "2 days ago",
            "scheduled_meetings": [
                {
                    "type": "progress_review",
                    "date": (datetime.now() + timedelta(days=2)).isoformat(),
                    "attendees": ["Client", "Project Manager", "Technical Lead"]
                }
            ],
            "pending_client_responses": ["Design approval", "Requirements clarification"],
            "client_satisfaction_score": 0.91,
            "communication_frequency": "appropriate"
        }
    
    async def _manage_project_risks(self) -> Dict[str, Any]:
        """Manage and assess project risks"""
        return {
            "active_risks": [
                {
                    "risk": "Resource dependency",
                    "probability": "medium",
                    "impact": "high",
                    "mitigation": "Cross-train team members"
                }
            ],
            "new_risks_identified": [],
            "risks_resolved": ["Third-party API delay"],
            "overall_risk_level": "medium",
            "risk_trend": "stable"
        }
    
    async def _generate_daily_action_items(self, project_status, team_coordination, risk_management) -> List[Dict[str, Any]]:
        """Generate daily action items based on current status"""
        return [
            {
                "priority": "high",
                "action": "Resolve blocked task in development",
                "owner": "Technical Lead",
                "deadline": (datetime.now() + timedelta(days=1)).isoformat(),
                "category": "task_management"
            },
            {
                "priority": "medium",
                "action": "Schedule resource cross-training",
                "owner": "Project Manager",
                "deadline": (datetime.now() + timedelta(days=3)).isoformat(),
                "category": "risk_mitigation"
            }
        ]
    
    async def _identify_escalations(self, project_status, risk_management) -> List[Dict[str, Any]]:
        """Identify issues that need escalation"""
        escalations = []
        
        # Check for high-impact risks
        for risk in risk_management.get("active_risks", []):
            if risk.get("impact") == "high" and risk.get("probability") in ["high", "medium"]:
                escalations.append({
                    "level": "pmo",
                    "issue": f"High-impact risk: {risk.get('risk')}",
                    "recommended_action": "PMO review and additional mitigation planning"
                })
        
        return escalations
    
    async def _log_project_activity(self, activity_type: str, data: Dict[str, Any], description: str):
        """Log project management activity to database"""
        try:
            with session_scope() as session:
                append_ledger_entry(
                    session,
                    agent_name=self.name,
                    action=activity_type,
                    description=description,
                    amount=0.0,
                    currency="AED",
                    metadata=json.dumps(data, default=str)
                )
                
                logger.info(f"{self.name}: Logged project activity - {activity_type}")
                
        except Exception as e:
            logger.error(f"{self.name}: Error logging project activity - {str(e)}")

    def get_current_proactive_tasks(self):
        """Get current proactive tasks the Project Manager is working on"""
        current_time = datetime.now()
        
        # Import the zoho sync service to get local data
        from ..utils.zoho_sync_service import zoho_sync_service
        
        # Get some basic data from local database for realistic tasks
        projects = zoho_sync_service.get_projects_from_db()
        customers = zoho_sync_service.get_customers_from_db()
        
        tasks = []
        
        # Active project delivery management
        delivery_progress = min(91, 45 + (current_time.hour * 2))
        tasks.append({
            "id": "pm_delivery_management",
            "title": "Active Project Delivery Management",
            "description": f"Managing delivery timelines and milestones for {len(projects)} active projects",
            "progress": delivery_progress,
            "type": "project_delivery",
            "priority": "high",
            "last_update": f"{max(1, 16 - current_time.hour)} hours ago",
            "details": f"Coordinating sprints, deliverables, and client communications for {self.specialization} projects"
        })
        
        # Team coordination and resource optimization
        team_progress = min(85, 35 + (current_time.minute % 45))
        tasks.append({
            "id": "pm_team_coordination",
            "title": "Development Team Coordination",
            "description": "Optimizing team collaboration and resolving development blockers",
            "progress": team_progress,
            "type": "team_management",
            "priority": "high",
            "last_update": f"{current_time.minute % 30} minutes ago",
            "details": "Managing developer assignments, code reviews, and sprint planning sessions"
        })
        
        # Quality assurance and testing oversight
        qa_progress = min(78, 25 + (current_time.hour % 14) * 3)
        tasks.append({
            "id": "pm_qa_oversight",
            "title": "Quality Assurance & Testing Oversight",
            "description": "Ensuring code quality standards and comprehensive testing coverage",
            "progress": qa_progress,
            "type": "quality_assurance",
            "priority": "medium",
            "last_update": f"{(current_time.hour * 60 + current_time.minute) % 150} minutes ago",
            "details": "Monitoring automated tests, code coverage metrics, and deployment readiness"
        })
        
        # Client stakeholder management and reporting
        stakeholder_progress = min(88, 40 + (current_time.day % 12) * 4)
        tasks.append({
            "id": "pm_stakeholder_management",
            "title": "Client Stakeholder Management & Reporting",
            "description": f"Managing client relationships and project reporting for {len(customers)} accounts",
            "progress": stakeholder_progress,
            "type": "stakeholder_management",
            "priority": "medium",
            "last_update": f"{current_time.day % 4} days ago",
            "details": "Preparing status reports, conducting stakeholder meetings, and managing project scope changes"
        })
        
        return tasks


# Create global project manager instances
project_manager_alpha = AIProjectManager(project_id="alpha", specialization="web_development")
project_manager_beta = AIProjectManager(project_id="beta", specialization="mobile_development")
project_manager_general = AIProjectManager(specialization="software_development")