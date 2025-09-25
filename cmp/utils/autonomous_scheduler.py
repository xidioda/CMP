"""
Autonomous Task Scheduler for AI Agents

This scheduler ensures that AI agents actually execute their tasks automatically
rather than just displaying mock progress. It runs real tasks in the background.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json
import os

logger = logging.getLogger(__name__)

class AutonomousTaskScheduler:
    """Background scheduler that makes agents execute real tasks automatically"""
    
    def __init__(self):
        self.running = False
        self.agents = {}
        self.execution_interval = 60  # Execute tasks every 60 seconds
        self.workspace_path = "/Users/xidioda/Projects/CMP"
        
    def register_agent(self, agent_id: str, agent_instance):
        """Register an agent for autonomous task execution"""
        self.agents[agent_id] = agent_instance
        logger.info(f"Registered agent {agent_id} for autonomous task execution")
    
    async def start_scheduler(self):
        """Start the autonomous task execution scheduler"""
        if self.running:
            return
            
        self.running = True
        logger.info("🚀 Starting Autonomous Task Scheduler - Agents will now perform REAL WORK!")
        
        while self.running:
            try:
                await self._execute_agent_tasks()
                await asyncio.sleep(self.execution_interval)
            except Exception as e:
                logger.error(f"Error in autonomous scheduler: {e}")
                await asyncio.sleep(10)  # Short delay before retry
    
    def stop_scheduler(self):
        """Stop the autonomous task scheduler"""
        self.running = False
        logger.info("Autonomous Task Scheduler stopped")
    
    async def _execute_agent_tasks(self):
        """Execute overdue tasks for all registered agents"""
        for agent_id, agent in self.agents.items():
            try:
                if hasattr(agent, 'get_current_proactive_tasks') and hasattr(agent, '_execute_overdue_tasks'):
                    # Get current tasks
                    tasks = agent.get_current_proactive_tasks()
                    
                    # Find overdue tasks
                    overdue_tasks = []
                    for task in tasks:
                        if self._is_task_overdue(task):
                            overdue_tasks.append(task)
                    
                    if overdue_tasks:
                        logger.info(f"🔧 {agent_id}: Executing {len(overdue_tasks)} overdue tasks")
                        
                        # Execute overdue tasks
                        await agent._execute_overdue_tasks(overdue_tasks)
                        
                        # Log execution
                        self._log_task_execution(agent_id, overdue_tasks)
                    else:
                        logger.debug(f"✅ {agent_id}: No overdue tasks")
                        
            except Exception as e:
                logger.error(f"Error executing tasks for {agent_id}: {e}")
    
    def _is_task_overdue(self, task: Dict[str, Any]) -> bool:
        """Check if a task is overdue and needs execution"""
        task_type = task.get('type', task.get('id', '').split('_')[-1])
        progress_file = f"{self.workspace_path}/local_storage/task_progress_{task_type}.json"
        
        # If no progress file exists, task is overdue
        if not os.path.exists(progress_file):
            return True
        
        try:
            with open(progress_file, 'r') as f:
                data = json.load(f)
            
            last_execution = datetime.fromisoformat(data.get('last_execution', '2024-01-01T00:00:00'))
            now = datetime.now()
            
            # Task is overdue if it hasn't been executed in the last hour
            return (now - last_execution) > timedelta(hours=1)
            
        except:
            return True  # If we can't read the progress, assume it's overdue
    
    def _log_task_execution(self, agent_id: str, tasks: List[Dict[str, Any]]):
        """Log task execution for monitoring"""
        execution_log = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_id,
            "tasks_executed": len(tasks),
            "task_titles": [task.get('title', 'Unknown') for task in tasks]
        }
        
        log_file = f"{self.workspace_path}/local_storage/execution_log.json"
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Append to log
        logs = []
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            except:
                logs = []
        
        logs.append(execution_log)
        
        # Keep only last 100 log entries
        logs = logs[-100:]
        
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)

# Global scheduler instance
autonomous_scheduler = AutonomousTaskScheduler()