"""
Inter-Department Coordination Service

Facilitates communication and collaboration between all departments:
- Finance, Executive, Operations, Marketing & Sales, Development

Enables:
- Cross-departmental data sharing
- Coordinated task planning
- Resource allocation requests
- Strategic alignment
- Real-time status updates
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)

class CoordinationPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high" 
    MEDIUM = "medium"
    LOW = "low"

class CoordinationStatus(Enum):
    REQUESTED = "requested"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"

@dataclass
class CoordinationRequest:
    """Represents a cross-departmental coordination request"""
    id: str
    requesting_department: str
    requesting_agent: str
    target_department: str
    target_agent: Optional[str]  # None means any agent in department
    request_type: str  # "data_request", "task_coordination", "resource_request", "strategic_alignment"
    title: str
    description: str
    priority: CoordinationPriority
    status: CoordinationStatus
    data_payload: Dict[str, Any]
    created_at: datetime
    expected_completion: datetime
    actual_completion: Optional[datetime] = None
    response_data: Optional[Dict[str, Any]] = None
    coordination_notes: List[str] = None

    def __post_init__(self):
        if self.coordination_notes is None:
            self.coordination_notes = []

class InterDepartmentCoordinator:
    """Manages all inter-department coordination and communication"""
    
    def __init__(self):
        self.active_requests: Dict[str, CoordinationRequest] = {}
        self.department_capabilities = self._initialize_department_capabilities()
        self.coordination_history: List[CoordinationRequest] = []
        
        # Track ongoing coordination patterns
        self.coordination_metrics = {
            "total_requests": 0,
            "successful_completions": 0,
            "average_completion_time": 0,
            "most_active_department": "",
            "coordination_efficiency_score": 0
        }
    
    def _initialize_department_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """Initialize what each department can provide/request"""
        return {
            "Finance": {
                "provides": [
                    "budget_analysis", "financial_projections", "cost_analysis",
                    "revenue_reports", "expense_tracking", "cash_flow_data",
                    "investment_recommendations", "financial_compliance_status"
                ],
                "requests": [
                    "project_cost_estimates", "resource_requirements", 
                    "sales_forecasts", "marketing_spend_data", 
                    "operational_costs", "development_budgets"
                ],
                "agents": ["CFO", "Accountant", "Controller", "Director"]
            },
            "Executive": {
                "provides": [
                    "strategic_direction", "company_objectives", "policy_decisions",
                    "resource_allocation_approvals", "strategic_partnerships",
                    "innovation_roadmap", "organizational_priorities"
                ],
                "requests": [
                    "departmental_status_reports", "performance_metrics",
                    "strategic_recommendations", "resource_needs_assessment",
                    "market_opportunities", "operational_efficiency_reports"
                ],
                "agents": ["CEO", "CTO", "CMO"]
            },
            "Operations": {
                "provides": [
                    "project_status", "resource_utilization", "workflow_optimization",
                    "process_improvements", "operational_metrics", "quality_assurance",
                    "delivery_timelines", "efficiency_reports"
                ],
                "requests": [
                    "project_requirements", "budget_allocations", "team_assignments",
                    "technology_specifications", "marketing_requirements",
                    "client_feedback", "strategic_priorities"
                ],
                "agents": ["COO", "PMO", "Project Manager", "Operations Manager"]
            },
            "Marketing & Sales": {
                "provides": [
                    "market_analysis", "customer_insights", "sales_forecasts",
                    "lead_generation_data", "customer_feedback", "brand_metrics",
                    "competitive_intelligence", "campaign_performance"
                ],
                "requests": [
                    "product_development_updates", "budget_approvals", 
                    "operational_capacity", "technology_requirements",
                    "customer_support_data", "financial_performance_data"
                ],
                "agents": ["Marketing Manager", "Sales Manager", "Customer Success Manager"]
            },
            "Development": {
                "provides": [
                    "technical_specifications", "development_timelines", 
                    "system_architecture", "performance_metrics", "security_status",
                    "automation_capabilities", "technical_recommendations"
                ],
                "requests": [
                    "feature_requirements", "budget_allocations", "resource_assignments",
                    "business_requirements", "user_feedback", "operational_needs",
                    "strategic_technology_direction"
                ],
                "agents": ["Lead Developer", "DevOps Engineer", "N8N Manager"]
            }
        }
    
    def create_coordination_request(
        self,
        requesting_dept: str,
        requesting_agent: str,
        target_dept: str,
        request_type: str,
        title: str,
        description: str,
        priority: CoordinationPriority,
        data_payload: Dict[str, Any],
        target_agent: Optional[str] = None
    ) -> str:
        """Create a new inter-department coordination request"""
        
        request_id = f"coord_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.active_requests)}"
        
        coordination_request = CoordinationRequest(
            id=request_id,
            requesting_department=requesting_dept,
            requesting_agent=requesting_agent,
            target_department=target_dept,
            target_agent=target_agent,
            request_type=request_type,
            title=title,
            description=description,
            priority=priority,
            status=CoordinationStatus.REQUESTED,
            data_payload=data_payload,
            created_at=datetime.now(),
            expected_completion=datetime.now() + self._get_expected_duration(priority)
        )
        
        self.active_requests[request_id] = coordination_request
        self.coordination_metrics["total_requests"] += 1
        
        logger.info(f"Created coordination request {request_id}: {requesting_dept} -> {target_dept}")
        
        return request_id
    
    def _get_expected_duration(self, priority: CoordinationPriority) -> timedelta:
        """Get expected completion time based on priority"""
        duration_map = {
            CoordinationPriority.CRITICAL: timedelta(hours=1),
            CoordinationPriority.HIGH: timedelta(hours=4),
            CoordinationPriority.MEDIUM: timedelta(hours=12),
            CoordinationPriority.LOW: timedelta(days=1)
        }
        return duration_map.get(priority, timedelta(hours=8))
    
    def process_coordination_request(self, request_id: str, response_data: Dict[str, Any]) -> bool:
        """Process a coordination request with response data"""
        
        if request_id not in self.active_requests:
            logger.error(f"Coordination request {request_id} not found")
            return False
        
        request = self.active_requests[request_id]
        request.response_data = response_data
        request.status = CoordinationStatus.COMPLETED
        request.actual_completion = datetime.now()
        
        # Move to history
        self.coordination_history.append(request)
        del self.active_requests[request_id]
        
        self.coordination_metrics["successful_completions"] += 1
        self._update_coordination_metrics()
        
        logger.info(f"Completed coordination request {request_id}")
        return True
    
    def get_pending_requests_for_department(self, department: str) -> List[CoordinationRequest]:
        """Get all pending coordination requests for a specific department"""
        return [
            request for request in self.active_requests.values()
            if request.target_department == department and request.status == CoordinationStatus.REQUESTED
        ]
    
    def get_active_coordinations_summary(self) -> Dict[str, Any]:
        """Get summary of all active coordination activities"""
        
        by_department = {}
        by_priority = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        by_type = {}
        
        for request in self.active_requests.values():
            # By department
            dept_key = f"{request.requesting_department} -> {request.target_department}"
            by_department[dept_key] = by_department.get(dept_key, 0) + 1
            
            # By priority
            by_priority[request.priority.value] += 1
            
            # By type
            by_type[request.request_type] = by_type.get(request.request_type, 0) + 1
        
        return {
            "total_active_requests": len(self.active_requests),
            "coordination_by_department": by_department,
            "coordination_by_priority": by_priority,
            "coordination_by_type": by_type,
            "coordination_metrics": self.coordination_metrics,
            "department_capabilities": self.department_capabilities
        }
    
    def _update_coordination_metrics(self):
        """Update coordination efficiency metrics"""
        if self.coordination_history:
            completion_times = [
                (req.actual_completion - req.created_at).total_seconds() / 3600
                for req in self.coordination_history[-50:]  # Last 50 requests
                if req.actual_completion
            ]
            
            if completion_times:
                self.coordination_metrics["average_completion_time"] = sum(completion_times) / len(completion_times)
        
        # Calculate efficiency score (0-100)
        total = self.coordination_metrics["total_requests"]
        completed = self.coordination_metrics["successful_completions"]
        
        if total > 0:
            success_rate = completed / total
            # Factor in average completion time (lower is better)
            avg_time = self.coordination_metrics["average_completion_time"]
            time_efficiency = max(0, (24 - min(24, avg_time)) / 24)  # Normalize to 0-1
            
            self.coordination_metrics["coordination_efficiency_score"] = int((success_rate * 0.7 + time_efficiency * 0.3) * 100)

# Global coordinator instance
inter_dept_coordinator = InterDepartmentCoordinator()