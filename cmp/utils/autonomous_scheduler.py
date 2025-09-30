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
        self.execution_interval = 300  # Execute tasks every 5 minutes (not 60 seconds!)
        self.workspace_path = "/Users/xidioda/Projects/CMP"
        self.last_execution_times = {}  # Track when each task was last executed
        
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
                # Check if agent has proactive development capability
                if hasattr(agent, 'get_current_proactive_tasks') and hasattr(agent, 'execute_proactive_development'):
                    # Get current tasks
                    tasks = agent.get_current_proactive_tasks()
                    
                    # Find overdue tasks
                    overdue_tasks = []
                    for task in tasks:
                        if self._is_task_overdue(task):
                            overdue_tasks.append(task)
                    
                    if overdue_tasks:
                        logger.info(f"🔧 {agent_id}: Executing {len(overdue_tasks)} overdue tasks using REAL MCP tools")
                        
                        # Mark tasks as being executed to prevent duplicates
                        for task in overdue_tasks:
                            self.last_execution_times[task.get('id', 'unknown')] = datetime.now()
                        
                        # Execute sophisticated proactive development
                        result = await agent.execute_proactive_development()
                        
                        # Log execution with more detail
                        self._log_task_execution(agent_id, overdue_tasks, result)
                        
                        logger.info(f"⚡ {agent_id}: Completed execution - {result.get('status', 'unknown')} - Real work: {result.get('real_work_performed', False)}")
                    else:
                        logger.debug(f"✅ {agent_id}: No overdue tasks")
                        
            except Exception as e:
                logger.error(f"💥 Error executing tasks for {agent_id}: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _is_task_overdue(self, task: Dict[str, Any]) -> bool:
        """Check if a task is overdue and needs execution"""
        task_id = task.get('id', 'unknown')
        task_type = task.get('type', task.get('id', '').split('_')[-1])
        
        # Check if we recently executed this specific task
        now = datetime.now()
        if task_id in self.last_execution_times:
            last_execution = self.last_execution_times[task_id]
            time_since_last = now - last_execution
            
            # Don't execute the same task more than once every 30 minutes
            if time_since_last.total_seconds() < 1800:  # 30 minutes
                return False
        
        # Check progress file for more detailed timing
        progress_file = f"{self.workspace_path}/local_storage/task_progress_{task_type}.json"
        
        # If no progress file exists, task is overdue (but only if we haven't executed it recently)
        if not os.path.exists(progress_file):
            return task_id not in self.last_execution_times
        
        try:
            with open(progress_file, 'r') as f:
                data = json.load(f)
            
            last_execution = datetime.fromisoformat(data.get('last_execution', '2024-01-01T00:00:00'))
            
            # Tasks are overdue if they haven't been executed in the last 2 hours
            time_since_execution = now - last_execution
            is_overdue = time_since_execution.total_seconds() > 7200  # 2 hours
            
            return is_overdue
            
        except Exception as e:
            logger.warning(f"Error reading progress file for {task_type}: {e}")
            return False
            
            # Task is overdue if it hasn't been executed in the last hour
            return (now - last_execution) > timedelta(hours=1)
            
        except:
            return True  # If we can't read the progress, assume it's overdue
    
    def _log_task_execution(self, agent_id: str, tasks: List[Dict[str, Any]], result: Dict[str, Any] = None):
        """Log task execution for monitoring"""
        execution_log = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_id,
            "tasks_executed": len(tasks),
            "task_titles": [task.get('title', 'Unknown') for task in tasks],
            "execution_result": result.get('status', 'unknown') if result else 'no_result',
            "real_work_performed": result.get('real_work_performed', False) if result else False
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