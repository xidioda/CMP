"""
Autonomous Communication System
Enables AI agents to communicate development requests and system improvements to human developers
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
import httpx
from pathlib import Path

logger = logging.getLogger(__name__)

class AutonomousCommunicationHub:
    """Central hub for autonomous agent-to-human communications"""
    
    def __init__(self):
        self.communication_log_file = Path("local_storage/agent_communications.json")
        self.pending_requests_file = Path("local_storage/pending_dev_requests.json")
        self.human_contact_methods = {
            "terminal_notification": True,  # Display in terminal where user runs the system
            "log_file": True,              # Write to dedicated log file
            "dashboard_alert": True,       # Show in admin dashboard
            "webhook_notification": False,  # Could integrate with Slack, Discord, etc.
        }
        
    async def send_development_request_to_human(
        self, 
        agent_id: str, 
        request_type: str,
        priority: str,
        description: str,
        technical_details: Dict[str, Any],
        suggested_solution: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a development request from an AI agent to the human developer
        
        Args:
            agent_id: ID of the requesting agent
            request_type: Type of request (bug_fix, enhancement, optimization, feature)
            priority: Priority level (critical, high, medium, low)
            description: Human-readable description of what's needed
            technical_details: Technical specifications, file paths, error details, etc.
            suggested_solution: Optional suggested approach/solution from the agent
            
        Returns:
            Dict with request ID and delivery status
        """
        
        request_id = f"{agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        request_data = {
            "request_id": request_id,
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            "request_type": request_type,
            "priority": priority,
            "description": description,
            "technical_details": technical_details,
            "suggested_solution": suggested_solution,
            "status": "pending_human_review",
            "estimated_effort": self._estimate_development_effort(request_type, technical_details),
            "auto_generated": True
        }
        
        # Store the request
        await self._store_communication_request(request_data)
        
        # Deliver through available channels
        delivery_results = await self._deliver_to_human(request_data)
        
        logger.info(f"🤖➡️👤 Agent {agent_id} sent development request: {request_type} - {description}")
        
        return {
            "request_id": request_id,
            "delivery_status": delivery_results,
            "timestamp": request_data["timestamp"]
        }
        
    async def _store_communication_request(self, request_data: Dict[str, Any]):
        """Store the communication request for tracking"""
        
        # Ensure directory exists
        self.communication_log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing communications
        existing_comms = []
        if self.communication_log_file.exists():
            try:
                with open(self.communication_log_file, 'r') as f:
                    existing_comms = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load existing communications: {e}")
                existing_comms = []
        
        # Add new request
        existing_comms.append(request_data)
        
        # Keep only last 100 communications
        if len(existing_comms) > 100:
            existing_comms = existing_comms[-100:]
        
        # Save updated communications
        with open(self.communication_log_file, 'w') as f:
            json.dump(existing_comms, f, indent=2)
            
        # Also add to pending requests
        await self._add_to_pending_requests(request_data)
        
    async def _add_to_pending_requests(self, request_data: Dict[str, Any]):
        """Add to pending requests queue"""
        
        pending = []
        if self.pending_requests_file.exists():
            try:
                with open(self.pending_requests_file, 'r') as f:
                    pending = json.load(f)
            except Exception:
                pending = []
        
        pending.append(request_data)
        
        # Save pending requests
        self.pending_requests_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.pending_requests_file, 'w') as f:
            json.dump(pending, f, indent=2)
    
    async def _deliver_to_human(self, request_data: Dict[str, Any]) -> Dict[str, bool]:
        """Deliver the development request through available channels"""
        
        delivery_results = {}
        
        # Terminal notification (most immediate)
        if self.human_contact_methods.get("terminal_notification"):
            try:
                await self._send_terminal_notification(request_data)
                delivery_results["terminal"] = True
            except Exception as e:
                logger.error(f"Terminal notification failed: {e}")
                delivery_results["terminal"] = False
        
        # Log file notification
        if self.human_contact_methods.get("log_file"):
            try:
                await self._write_to_dedicated_log(request_data)
                delivery_results["log_file"] = True
            except Exception as e:
                logger.error(f"Log file notification failed: {e}")
                delivery_results["log_file"] = False
        
        # Dashboard alert
        if self.human_contact_methods.get("dashboard_alert"):
            try:
                await self._create_dashboard_alert(request_data)
                delivery_results["dashboard"] = True
            except Exception as e:
                logger.error(f"Dashboard alert failed: {e}")
                delivery_results["dashboard"] = False
        
        return delivery_results
    
    async def _send_terminal_notification(self, request_data: Dict[str, Any]):
        """Send notification to terminal where system is running"""
        
        priority_icons = {
            "critical": "🚨",
            "high": "⚡",
            "medium": "🔔",
            "low": "ℹ️"
        }
        
        icon = priority_icons.get(request_data["priority"], "🤖")
        
        # Write to main log which appears in terminal
        terminal_message = f"""
{icon} AUTONOMOUS DEVELOPMENT REQUEST {icon}
Agent: {request_data['agent_id']}
Type: {request_data['request_type'].upper()}
Priority: {request_data['priority'].upper()}
Description: {request_data['description']}

Technical Details:
{json.dumps(request_data['technical_details'], indent=2)}

Suggested Solution: {request_data.get('suggested_solution', 'None provided')}

Request ID: {request_data['request_id']}
Timestamp: {request_data['timestamp']}
        """
        
        logger.info(terminal_message)
    
    async def _write_to_dedicated_log(self, request_data: Dict[str, Any]):
        """Write to dedicated development requests log file"""
        
        dev_log_file = Path("logs/autonomous_dev_requests.log")
        dev_log_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(dev_log_file, 'a') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"AUTONOMOUS DEVELOPMENT REQUEST - {datetime.now().isoformat()}\n")
            f.write(f"{'='*80}\n")
            f.write(f"Request ID: {request_data['request_id']}\n")
            f.write(f"Agent: {request_data['agent_id']}\n") 
            f.write(f"Type: {request_data['request_type']}\n")
            f.write(f"Priority: {request_data['priority']}\n")
            f.write(f"Description: {request_data['description']}\n\n")
            f.write(f"Technical Details:\n{json.dumps(request_data['technical_details'], indent=2)}\n\n")
            f.write(f"Suggested Solution: {request_data.get('suggested_solution', 'None')}\n")
            f.write(f"Estimated Effort: {request_data['estimated_effort']}\n")
            f.write(f"\n{'='*80}\n\n")
    
    async def _create_dashboard_alert(self, request_data: Dict[str, Any]):
        """Create alert in admin dashboard"""
        
        alert_file = Path("local_storage/dashboard_alerts.json")
        alert_file.parent.mkdir(parents=True, exist_ok=True)
        
        alerts = []
        if alert_file.exists():
            try:
                with open(alert_file, 'r') as f:
                    alerts = json.load(f)
            except Exception:
                alerts = []
        
        alert = {
            "id": request_data["request_id"],
            "type": "development_request",
            "agent_id": request_data["agent_id"],
            "priority": request_data["priority"],
            "message": f"Development Request: {request_data['description']}",
            "details": request_data,
            "timestamp": request_data["timestamp"],
            "read": False
        }
        
        alerts.append(alert)
        
        # Keep only last 50 alerts
        if len(alerts) > 50:
            alerts = alerts[-50:]
        
        with open(alert_file, 'w') as f:
            json.dump(alerts, f, indent=2)
    
    def _estimate_development_effort(self, request_type: str, technical_details: Dict[str, Any]) -> str:
        """Estimate development effort based on request type and complexity"""
        
        complexity_indicators = {
            "file_count": len(technical_details.get("files_involved", [])),
            "api_changes": len(technical_details.get("api_endpoints", [])),
            "database_changes": bool(technical_details.get("database_changes")),
            "ui_changes": bool(technical_details.get("ui_changes")),
            "integration_changes": len(technical_details.get("integrations", []))
        }
        
        total_complexity = sum([
            complexity_indicators["file_count"] * 0.5,
            complexity_indicators["api_changes"] * 1.5,
            int(complexity_indicators["database_changes"]) * 2,
            int(complexity_indicators["ui_changes"]) * 1,
            complexity_indicators["integration_changes"] * 2
        ])
        
        if total_complexity < 2:
            return "Small (1-2 hours)"
        elif total_complexity < 5:
            return "Medium (2-4 hours)" 
        elif total_complexity < 10:
            return "Large (4-8 hours)"
        else:
            return "Complex (8+ hours)"
    
    async def get_pending_requests(self) -> List[Dict[str, Any]]:
        """Get all pending development requests"""
        
        if not self.pending_requests_file.exists():
            return []
        
        try:
            with open(self.pending_requests_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading pending requests: {e}")
            return []
    
    async def mark_request_completed(self, request_id: str) -> bool:
        """Mark a development request as completed"""
        
        try:
            pending = await self.get_pending_requests()
            updated_pending = [req for req in pending if req["request_id"] != request_id]
            
            with open(self.pending_requests_file, 'w') as f:
                json.dump(updated_pending, f, indent=2)
            
            logger.info(f"✅ Marked development request {request_id} as completed")
            return True
            
        except Exception as e:
            logger.error(f"Error marking request completed: {e}")
            return False

# Global instance
communication_hub = AutonomousCommunicationHub()