"""
N8N Workflow Integration for AI Agents

This module integrates AI agents with N8N workflows to perform real automation tasks
instead of just creating GitHub issues. Agents will trigger actual workflows.
"""

import asyncio
import json
import logging
import aiohttp
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class N8NWorkflowIntegration:
    """Integrates AI agents with N8N workflows for real automation"""
    
    def __init__(self):
        self.n8n_url = os.getenv("N8N_URL", "http://localhost:5678")
        self.n8n_api_key = os.getenv("N8N_API_KEY")
        self.webhook_base_url = f"{self.n8n_url}/webhook"
        
    async def trigger_development_workflow(self, 
                                         task_type: str,
                                         task_details: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger N8N workflow for development tasks"""
        try:
            workflow_data = {
                "task_type": task_type,
                "task_details": task_details,
                "timestamp": datetime.now().isoformat(),
                "source": "ai_agent"
            }
            
            # Determine which workflow to trigger based on task type
            webhook_url = self._get_workflow_webhook_url(task_type)
            
            if not webhook_url:
                return {
                    "success": False,
                    "error": f"No N8N workflow configured for task type: {task_type}"
                }
            
            # Trigger the N8N workflow
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=workflow_data,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"✅ N8N workflow triggered successfully for {task_type}")
                        return {
                            "success": True,
                            "workflow_executed": True,
                            "n8n_response": result,
                            "webhook_url": webhook_url
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ N8N workflow failed: {response.status} - {error_text}")
                        return {
                            "success": False,
                            "error": f"N8N workflow failed: {response.status} - {error_text}"
                        }
                        
        except asyncio.TimeoutError:
            logger.error("⏰ N8N workflow request timed out")
            return {
                "success": False,
                "error": "N8N workflow request timed out"
            }
        except Exception as e:
            logger.error(f"❌ Error triggering N8N workflow: {e}")
            return {
                "success": False,
                "error": f"N8N integration error: {str(e)}"
            }
    
    def _get_workflow_webhook_url(self, task_type: str) -> Optional[str]:
        """Get the appropriate N8N webhook URL for the task type"""
        webhook_mappings = {
            "testing": f"{self.webhook_base_url}/ai-testing-workflow",
            "completion": f"{self.webhook_base_url}/ai-completion-workflow", 
            "enhancement": f"{self.webhook_base_url}/ai-enhancement-workflow",
            "code_generation": f"{self.webhook_base_url}/ai-code-generation",
            "file_operations": f"{self.webhook_base_url}/ai-file-operations",
            "system_optimization": f"{self.webhook_base_url}/ai-system-optimization",
            "git_operations": f"{self.webhook_base_url}/ai-git-operations",
            "api_integration": f"{self.webhook_base_url}/ai-api-integration",
            "database_operations": f"{self.webhook_base_url}/ai-database-operations"
        }
        
        return webhook_mappings.get(task_type)
    
    async def trigger_testing_workflow(self, modules_to_test: List[str]) -> Dict[str, Any]:
        """Trigger N8N workflow specifically for testing tasks"""
        task_details = {
            "modules_to_test": modules_to_test,
            "test_framework": "pytest",
            "coverage_target": 80,
            "test_types": ["unit", "integration"],
            "output_directory": "tests/"
        }
        
        return await self.trigger_development_workflow("testing", task_details)
    
    async def trigger_completion_workflow(self, todo_items: List[str], features_to_complete: List[str]) -> Dict[str, Any]:
        """Trigger N8N workflow for completing TODO items and features"""
        task_details = {
            "todo_items": todo_items,
            "features_to_complete": features_to_complete,
            "validation_required": True,
            "testing_required": True
        }
        
        return await self.trigger_development_workflow("completion", task_details)
    
    async def create_testing_workflow(self) -> Dict[str, Any]:
        """Create N8N workflow for automated testing"""
        try:
            workflow_definition = {
                "name": "AI Testing Workflow",
                "nodes": [
                    {
                        "parameters": {},
                        "name": "Webhook",
                        "type": "n8n-nodes-base.webhook",
                        "typeVersion": 1,
                        "position": [250, 300],
                        "webhookId": "ai-testing-workflow"
                    },
                    {
                        "parameters": {
                            "command": "cd {{ $json.workspace_path }} && python -m pytest {{ $json.modules_to_test.join(' ') }} -v --tb=short"
                        },
                        "name": "Run Tests",
                        "type": "n8n-nodes-base.executeCommand",
                        "typeVersion": 1,
                        "position": [450, 300]
                    },
                    {
                        "parameters": {
                            "command": "cd {{ $json.workspace_path }} && python -m pytest --cov=cmp --cov-report=json"
                        },
                        "name": "Generate Coverage",
                        "type": "n8n-nodes-base.executeCommand", 
                        "typeVersion": 1,
                        "position": [650, 300]
                    },
                    {
                        "parameters": {
                            "url": "{{ $json.callback_url }}",
                            "options": {
                                "bodyContentType": "json"
                            },
                            "jsonData": "{\n  \"workflow\": \"testing\",\n  \"status\": \"completed\",\n  \"test_results\": {{ $json }},\n  \"timestamp\": \"{{ $now }}\"\n}"
                        },
                        "name": "Send Results",
                        "type": "n8n-nodes-base.httpRequest",
                        "typeVersion": 1,
                        "position": [850, 300]
                    }
                ],
                "connections": {
                    "Webhook": {
                        "main": [
                            [
                                {
                                    "node": "Run Tests",
                                    "type": "main",
                                    "index": 0
                                }
                            ]
                        ]
                    },
                    "Run Tests": {
                        "main": [
                            [
                                {
                                    "node": "Generate Coverage",
                                    "type": "main",
                                    "index": 0
                                }
                            ]
                        ]
                    },
                    "Generate Coverage": {
                        "main": [
                            [
                                {
                                    "node": "Send Results",
                                    "type": "main",
                                    "index": 0
                                }
                            ]
                        ]
                    }
                },
                "active": True,
                "settings": {},
                "id": "ai-testing-workflow"
            }
            
            # Create workflow via N8N API
            if self.n8n_api_key:
                headers = {"X-N8N-API-KEY": self.n8n_api_key}
            else:
                headers = {}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.n8n_url}/api/v1/workflows",
                    json=workflow_definition,
                    headers=headers
                ) as response:
                    
                    if response.status == 201:
                        result = await response.json()
                        logger.info("✅ N8N testing workflow created successfully")
                        return {"success": True, "workflow_id": result.get("id")}
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Failed to create N8N workflow: {response.status} - {error_text}")
                        return {"success": False, "error": error_text}
                        
        except Exception as e:
            logger.error(f"❌ Error creating N8N testing workflow: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_completion_workflow(self) -> Dict[str, Any]:
        """Create N8N workflow for TODO completion and feature development"""
        workflow_definition = {
            "name": "AI Completion Workflow",
            "nodes": [
                {
                    "parameters": {},
                    "name": "Webhook",
                    "type": "n8n-nodes-base.webhook",
                    "typeVersion": 1,
                    "position": [250, 300],
                    "webhookId": "ai-completion-workflow"
                },
                {
                    "parameters": {
                        "command": "cd {{ $json.workspace_path }} && grep -r TODO cmp/ --include='*.py' | wc -l"
                    },
                    "name": "Count TODOs",
                    "type": "n8n-nodes-base.executeCommand",
                    "typeVersion": 1,
                    "position": [450, 200]
                },
                {
                    "parameters": {
                        "command": "cd {{ $json.workspace_path }} && find cmp/ -name '*.py' -exec grep -l 'TODO\\|FIXME\\|HACK' {} \\;"
                    },
                    "name": "Find TODO Files",
                    "type": "n8n-nodes-base.executeCommand",
                    "typeVersion": 1,
                    "position": [450, 400]
                },
                {
                    "parameters": {
                        "command": "cd {{ $json.workspace_path }} && python -m py_compile cmp/main.py"
                    },
                    "name": "Validate Code",
                    "type": "n8n-nodes-base.executeCommand",
                    "typeVersion": 1,
                    "position": [650, 300]
                },
                {
                    "parameters": {
                        "url": "{{ $json.callback_url }}",
                        "options": {
                            "bodyContentType": "json"
                        },
                        "jsonData": "{\n  \"workflow\": \"completion\",\n  \"status\": \"completed\",\n  \"todo_count\": {{ $node[\"Count TODOs\"].json.output }},\n  \"todo_files\": {{ $node[\"Find TODO Files\"].json.output }},\n  \"validation\": {{ $node[\"Validate Code\"].json }},\n  \"timestamp\": \"{{ $now }}\"\n}"
                    },
                    "name": "Send Results",
                    "type": "n8n-nodes-base.httpRequest",
                    "typeVersion": 1,
                    "position": [850, 300]
                }
            ],
            "connections": {
                "Webhook": {
                    "main": [
                        [
                            {
                                "node": "Count TODOs",
                                "type": "main",
                                "index": 0
                            },
                            {
                                "node": "Find TODO Files",
                                "type": "main",
                                "index": 0
                            }
                        ]
                    ]
                },
                "Count TODOs": {
                    "main": [
                        [
                            {
                                "node": "Validate Code",
                                "type": "main",
                                "index": 0
                            }
                        ]
                    ]
                },
                "Find TODO Files": {
                    "main": [
                        [
                            {
                                "node": "Validate Code",
                                "type": "main",
                                "index": 0
                            }
                        ]
                    ]
                },
                "Validate Code": {
                    "main": [
                        [
                            {
                                "node": "Send Results",
                                "type": "main",
                                "index": 0
                            }
                        ]
                    ]
                }
            },
            "active": True,
            "settings": {},
            "id": "ai-completion-workflow"
        }
        
        # Similar implementation to create_testing_workflow
        return await self._create_workflow_via_api(workflow_definition)
    
    async def _create_workflow_via_api(self, workflow_definition: Dict[str, Any]) -> Dict[str, Any]:
        """Helper method to create workflow via N8N API"""
        try:
            if self.n8n_api_key:
                headers = {"X-N8N-API-KEY": self.n8n_api_key}
            else:
                headers = {}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.n8n_url}/api/v1/workflows",
                    json=workflow_definition,
                    headers=headers
                ) as response:
                    
                    if response.status == 201:
                        result = await response.json()
                        logger.info(f"✅ N8N workflow '{workflow_definition['name']}' created successfully")
                        return {"success": True, "workflow_id": result.get("id")}
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Failed to create N8N workflow: {response.status} - {error_text}")
                        return {"success": False, "error": error_text}
                        
        except Exception as e:
            logger.error(f"❌ Error creating N8N workflow: {e}")
            return {"success": False, "error": str(e)}
    
    async def check_n8n_connection(self) -> Dict[str, Any]:
        """Check if N8N server is accessible"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.n8n_url}/api/v1/workflows",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status in [200, 401]:  # 401 is OK if no API key
                        logger.info("✅ N8N server is accessible")
                        return {
                            "success": True,
                            "n8n_accessible": True,
                            "n8n_url": self.n8n_url
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"N8N server returned status {response.status}"
                        }
                        
        except Exception as e:
            logger.error(f"❌ Cannot connect to N8N server: {e}")
            return {
                "success": False,
                "error": f"N8N connection failed: {str(e)}"
            }

# Global instance
n8n_integration = N8NWorkflowIntegration()