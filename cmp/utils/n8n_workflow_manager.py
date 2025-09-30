"""
N8N Workflow Management for Autonomous AI Agents
Allows AI agents to programmatically create, manage, and execute N8N workflows
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import httpx
import os

logger = logging.getLogger(__name__)

class N8NWorkflowManager:
    """Manages N8N workflows for autonomous AI agents"""
    
    def __init__(self):
        self.n8n_api_url = os.getenv("N8N_API_URL", "http://localhost:5678/api/v1")
        self.n8n_api_key = os.getenv("N8N_API_KEY", "")  # Optional for local development
        self.workspace_path = "/Users/xidioda/Projects/CMP"
        
    async def create_agent_workflow(
        self,
        agent_id: str,
        workflow_name: str,
        webhook_path: str,
        description: str = "Autonomous AI agent workflow"
    ) -> Dict[str, Any]:
        """Create a new N8N workflow for an AI agent"""
        
        try:
            # Create workflow definition
            workflow_definition = self._generate_workflow_definition(
                agent_id, workflow_name, webhook_path, description
            )
            
            # First, check if workflow already exists
            existing_workflow = await self._find_existing_workflow(workflow_name)
            if existing_workflow:
                logger.info(f"✅ Workflow '{workflow_name}' already exists (ID: {existing_workflow['id']})")
                return {
                    "success": True,
                    "workflow_id": existing_workflow['id'],
                    "webhook_url": f"http://localhost:5678/webhook/{webhook_path}",
                    "status": "exists"
                }
            
            # Create new workflow via N8N API
            async with httpx.AsyncClient() as client:
                headers = {"Content-Type": "application/json"}
                if self.n8n_api_key:
                    headers["X-N8N-API-KEY"] = self.n8n_api_key
                    
                response = await client.post(
                    f"{self.n8n_api_url}/workflows",
                    json=workflow_definition,
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code in [200, 201]:  # N8N can return either 200 or 201
                    workflow_data = response.json()
                    logger.info(f"✅ Created N8N workflow '{workflow_name}' (ID: {workflow_data['id']})")
                    
                    # Activate the workflow
                    await self._activate_workflow(workflow_data['id'])
                    
                    return {
                        "success": True,
                        "workflow_id": workflow_data['id'],
                        "webhook_url": f"http://localhost:5678/webhook/{webhook_path}",
                        "status": "created"
                    }
                else:
                    logger.error(f"❌ Failed to create workflow: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"N8N API error: {response.status_code}",
                        "status": "failed"
                    }
                    
        except Exception as e:
            logger.error(f"❌ Error creating N8N workflow: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": "error"
            }
    
    def _generate_workflow_definition(
        self,
        agent_id: str,
        workflow_name: str,
        webhook_path: str,
        description: str
    ) -> Dict[str, Any]:
        """Generate N8N workflow definition for an autonomous AI agent"""
        
        return {
            "name": workflow_name,
            "nodes": [
                {
                    "id": "webhook",
                    "name": "Agent Webhook",
                    "type": "n8n-nodes-base.webhook",
                    "typeVersion": 1,
                    "position": [240, 300],
                    "webhookId": webhook_path,
                    "parameters": {
                        "httpMethod": "POST",
                        "path": webhook_path,
                        "responseMode": "responseNode"
                    }
                },
                {
                    "id": "process",
                    "name": "Process Agent Data",
                    "type": "n8n-nodes-base.set",
                    "typeVersion": 1,
                    "position": [460, 300],
                    "parameters": {
                        "values": {
                            "string": [
                                {
                                    "name": "agent_id",
                                    "value": agent_id
                                },
                                {
                                    "name": "processed_at",
                                    "value": "={{ new Date().toISOString() }}"
                                },
                                {
                                    "name": "workflow_name",
                                    "value": workflow_name
                                }
                            ]
                        }
                    }
                },
                {
                    "id": "respond",
                    "name": "Respond to Agent",
                    "type": "n8n-nodes-base.respondToWebhook",
                    "typeVersion": 1,
                    "position": [680, 300],
                    "parameters": {
                        "options": {},
                        "respondWith": "json",
                        "responseBody": json.dumps({
                            "status": "success",
                            "message": "Task received by N8N automation",
                            "agent_id": f"{{{{ $json.agent_id }}}}",
                            "task_id": f"{{{{ $json.task_id }}}}",
                            "processed_at": f"{{{{ $json.processed_at }}}}"
                        })
                    }
                }
            ],
            "connections": {
                "Agent Webhook": {
                    "main": [
                        [
                            {
                                "node": "Process Agent Data",
                                "type": "main",
                                "index": 0
                            }
                        ]
                    ]
                },
                "Process Agent Data": {
                    "main": [
                        [
                            {
                                "node": "Respond to Agent",
                                "type": "main",
                                "index": 0
                            }
                        ]
                    ]
                }
            },
            "settings": {},
            "staticData": {}
        }
    
    async def _find_existing_workflow(self, workflow_name: str) -> Optional[Dict[str, Any]]:
        """Find an existing workflow by name"""
        try:
            async with httpx.AsyncClient() as client:
                headers = {}
                if self.n8n_api_key:
                    headers["X-N8N-API-KEY"] = self.n8n_api_key
                    
                response = await client.get(
                    f"{self.n8n_api_url}/workflows",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    workflows = response.json()
                    for workflow in workflows.get('data', []):
                        if workflow.get('name') == workflow_name:
                            return workflow
                            
        except Exception as e:
            logger.warning(f"⚠️ Could not check existing workflows: {e}")
        
        return None
    
    async def _activate_workflow(self, workflow_id: str) -> bool:
        """Activate a workflow"""
        try:
            async with httpx.AsyncClient() as client:
                headers = {}
                if self.n8n_api_key:
                    headers["X-N8N-API-KEY"] = self.n8n_api_key
                    
                response = await client.patch(
                    f"{self.n8n_api_url}/workflows/{workflow_id}",
                    json={"active": True},
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ Activated N8N workflow {workflow_id}")
                    return True
                else:
                    logger.warning(f"⚠️ Could not activate workflow: {response.status_code}")
                    
        except Exception as e:
            logger.warning(f"⚠️ Could not activate workflow: {e}")
            
        return False
    
    async def ensure_agent_workflows_exist(self, agent_id: str) -> List[Dict[str, Any]]:
        """Ensure all required workflows exist for an AI agent"""
        
        agent_workflows = [
            {
                "name": f"{agent_id}_automation",
                "webhook_path": f"{agent_id}_automation",
                "description": f"Main automation workflow for {agent_id} agent"
            },
            {
                "name": f"{agent_id}_system_optimization", 
                "webhook_path": f"{agent_id}_system_optimization",
                "description": f"System optimization workflow for {agent_id} agent"
            },
            {
                "name": f"{agent_id}_git_operations",
                "webhook_path": f"{agent_id}_git_operations", 
                "description": f"Git operations workflow for {agent_id} agent"
            },
            {
                "name": f"{agent_id}_file_operations",
                "webhook_path": f"{agent_id}_file_operations",
                "description": f"File operations workflow for {agent_id} agent"
            }
        ]
        
        results = []
        for workflow_config in agent_workflows:
            result = await self.create_agent_workflow(
                agent_id=agent_id,
                workflow_name=workflow_config["name"],
                webhook_path=workflow_config["webhook_path"],
                description=workflow_config["description"]
            )
            results.append({
                **result,
                "workflow_name": workflow_config["name"],
                "webhook_path": workflow_config["webhook_path"]
            })
            
        return results

# Create global instance
n8n_workflow_manager = N8NWorkflowManager()