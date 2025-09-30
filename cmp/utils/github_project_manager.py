"""
GitHub Project Management Integration for AI Agents
Enables autonomous agents to create, track, and manage GitHub issues, projects, and tasks
"""

import os
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import httpx
from github import Github
from github.GithubException import GithubException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class GitHubProjectManager:
    """Manages GitHub issues, projects, and tasks for AI agents"""
    
    def __init__(self):
        # Reload env vars to ensure we get the latest
        load_dotenv(override=True)
        
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.repo_owner = os.getenv("GITHUB_REPO_OWNER", "xidioda")
        self.repo_name = os.getenv("GITHUB_REPO_NAME", "CMP")
        self.github_client = None
        self.repo = None
        
        if self.github_token:
            try:
                self.github_client = Github(self.github_token)
                self.repo = self.github_client.get_repo(f"{self.repo_owner}/{self.repo_name}")
                logger.info(f"✅ GitHub integration initialized successfully for {self.repo_owner}/{self.repo_name}")
            except Exception as e:
                logger.error(f"❌ GitHub integration failed: {e}")
        else:
            logger.warning("⚠️ No GITHUB_TOKEN found - GitHub integration disabled")
    
    async def create_agent_task_issue(
        self,
        agent_id: str,
        task_type: str,
        title: str,
        description: str,
        priority: str = "medium",
        labels: List[str] = None,
        assignee: str = None
    ) -> Dict[str, Any]:
        """Create a GitHub issue for an agent task"""
        
        if not self.repo:
            return {"success": False, "error": "GitHub not available"}
        
        try:
            # Prepare labels (use simple, short names for GitHub compatibility)
            # Map complex task types to simple labels
            task_type_mapping = {
                'system_optimization': 'optimization',
                'n8n_workflow': 'automation',
                'git_operations': 'git',
                'file_operations': 'files',
                'code_generation': 'codegen',
                'api_integration': 'api',
                'database_operations': 'database'
            }
            
            simple_task_type = task_type_mapping.get(task_type, task_type[:10])  # Max 10 chars
            safe_agent_id = agent_id.replace('_', '-')[:15]  # Max 15 chars
            
            issue_labels = ["ai-agent", f"agent-{safe_agent_id}", f"type-{simple_task_type}", f"priority-{priority}"]
            if labels:
                # Keep labels simple and short
                clean_labels = [label.replace('_', '-')[:20] for label in labels]
                issue_labels.extend(clean_labels)
            
            # Create comprehensive issue body
            issue_body = f"""
## 🤖 Autonomous Agent Task

**Agent:** {agent_id}  
**Task Type:** {task_type}  
**Priority:** {priority.upper()}  
**Created:** {datetime.now().isoformat()}

---

### Description
{description}

### Autonomous Execution Details
- **Agent Responsible:** {agent_id}
- **Task Category:** {task_type}
- **Execution Mode:** Autonomous
- **Status:** In Progress

### Progress Tracking
- [ ] Task analysis completed
- [ ] Implementation in progress  
- [ ] Testing and validation
- [ ] Task completion and closure

---
*This issue was created autonomously by an AI agent as part of the CMP self-improvement system.*
            """
            
            # Create the issue
            issue_params = {
                "title": f"[{agent_id.upper()}] {title}",
                "body": issue_body,
                "labels": issue_labels
            }
            
            # Only add assignee if it's provided
            if assignee:
                issue_params["assignee"] = assignee
                
            issue = self.repo.create_issue(**issue_params)
            
            logger.info(f"✅ Created GitHub issue #{issue.number}: {title}")
            
            return {
                "success": True,
                "issue_number": issue.number,
                "issue_url": issue.html_url,
                "issue_id": issue.id,
                "title": issue.title
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to create GitHub issue: {e}")
            logger.error(f"❌ Exception type: {type(e)}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return {"success": False, "error": str(e)}
    
    async def update_task_progress(
        self,
        issue_number: int,
        progress_update: str,
        completion_percentage: int = None,
        status: str = None
    ) -> Dict[str, Any]:
        """Update progress on a GitHub issue"""
        
        if not self.repo:
            return {"success": False, "error": "GitHub not available"}
        
        try:
            issue = self.repo.get_issue(issue_number)
            
            # Create progress comment
            progress_comment = f"""
## 🔄 Autonomous Progress Update

**Timestamp:** {datetime.now().isoformat()}  
**Status:** {status or 'In Progress'}  
**Completion:** {completion_percentage}% {self._get_progress_bar(completion_percentage) if completion_percentage else ''}

### Update Details
{progress_update}

---
*Progress updated autonomously by AI agent*
            """
            
            issue.create_comment(progress_comment)
            
            # Update labels if status changed
            if status:
                self._update_issue_status_labels(issue, status)
            
            logger.info(f"✅ Updated progress for issue #{issue_number}")
            
            return {
                "success": True,
                "issue_number": issue_number,
                "status": status
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to update issue progress: {e}")
            return {"success": False, "error": str(e)}
    
    async def complete_task(
        self,
        issue_number: int,
        completion_summary: str,
        results: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Mark a task as completed and close the issue"""
        
        if not self.repo:
            return {"success": False, "error": "GitHub not available"}
        
        try:
            issue = self.repo.get_issue(issue_number)
            
            # Create completion comment
            completion_comment = f"""
## ✅ Task Completed Autonomously

**Completion Time:** {datetime.now().isoformat()}  
**Status:** COMPLETED  
**Success:** ✅

### Completion Summary
{completion_summary}

### Results
```json
{json.dumps(results, indent=2) if results else 'No specific results recorded'}
```

---
*Task completed autonomously by AI agent. Closing issue.*
            """
            
            issue.create_comment(completion_comment)
            
            # Update labels and close
            current_labels = [label.name for label in issue.labels]
            current_labels = [l for l in current_labels if not l.startswith('status-')]
            current_labels.append('status-completed')
            
            issue.edit(labels=current_labels, state='closed')
            
            logger.info(f"✅ Completed and closed issue #{issue_number}")
            
            return {
                "success": True,
                "issue_number": issue_number,
                "status": "completed",
                "closed": True
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to complete task: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_agent_tasks(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all open tasks (issues) for a specific agent"""
        
        if not self.repo:
            return []
        
        try:
            # Get issues with agent label
            issues = self.repo.get_issues(
                state='open',
                labels=[f'ai-agent', f'agent-{agent_id}']
            )
            
            agent_tasks = []
            for issue in issues:
                task_info = {
                    "issue_number": issue.number,
                    "title": issue.title,
                    "description": issue.body,
                    "created_at": issue.created_at.isoformat(),
                    "updated_at": issue.updated_at.isoformat(),
                    "labels": [label.name for label in issue.labels],
                    "state": issue.state,
                    "url": issue.html_url,
                    "comments_count": issue.comments
                }
                agent_tasks.append(task_info)
            
            return agent_tasks
            
        except Exception as e:
            logger.error(f"❌ Failed to get agent tasks: {e}")
            return []
    
    async def create_project_milestone(
        self,
        title: str,
        description: str,
        due_date: datetime = None
    ) -> Dict[str, Any]:
        """Create a project milestone for tracking major goals"""
        
        if not self.repo:
            return {"success": False, "error": "GitHub not available"}
        
        try:
            milestone = self.repo.create_milestone(
                title=title,
                description=description,
                due_on=due_date
            )
            
            logger.info(f"✅ Created milestone: {title}")
            
            return {
                "success": True,
                "milestone_number": milestone.number,
                "milestone_url": milestone.html_url,
                "title": milestone.title
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to create milestone: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_progress_bar(self, percentage: int) -> str:
        """Generate a visual progress bar"""
        if percentage is None:
            return ""
        
        filled = int(percentage / 10)
        empty = 10 - filled
        return f"[{'█' * filled}{'░' * empty}] {percentage}%"
    
    def _update_issue_status_labels(self, issue, status: str):
        """Update status labels on an issue"""
        try:
            current_labels = [label.name for label in issue.labels]
            # Remove old status labels
            current_labels = [l for l in current_labels if not l.startswith('status-')]
            # Add new status label
            current_labels.append(f'status-{status}')
            issue.edit(labels=current_labels)
        except Exception as e:
            logger.error(f"Failed to update status labels: {e}")
    
    async def get_project_overview(self) -> Dict[str, Any]:
        """Get an overview of all project tasks and their status"""
        
        if not self.repo:
            return {"success": False, "error": "GitHub not available"}
        
        try:
            # Get all AI agent issues
            all_issues = self.repo.get_issues(
                state='all',
                labels=['ai-agent']
            )
            
            overview = {
                "total_tasks": 0,
                "open_tasks": 0,
                "completed_tasks": 0,
                "by_agent": {},
                "by_priority": {"critical": 0, "high": 0, "medium": 0, "low": 0},
                "by_type": {},
                "recent_activity": []
            }
            
            for issue in all_issues:
                overview["total_tasks"] += 1
                
                if issue.state == 'open':
                    overview["open_tasks"] += 1
                else:
                    overview["completed_tasks"] += 1
                
                # Count by agent
                agent_labels = [l.name for l in issue.labels if l.name.startswith('agent-')]
                for agent_label in agent_labels:
                    agent_id = agent_label.replace('agent-', '')
                    overview["by_agent"][agent_id] = overview["by_agent"].get(agent_id, 0) + 1
                
                # Count by priority
                priority_labels = [l.name for l in issue.labels if l.name.startswith('priority-')]
                for priority_label in priority_labels:
                    priority = priority_label.replace('priority-', '')
                    if priority in overview["by_priority"]:
                        overview["by_priority"][priority] += 1
                
                # Count by type
                type_labels = [l.name for l in issue.labels if l.name.startswith('type-')]
                for type_label in type_labels:
                    task_type = type_label.replace('type-', '')
                    overview["by_type"][task_type] = overview["by_type"].get(task_type, 0) + 1
                
                # Recent activity (last 10 issues)
                if len(overview["recent_activity"]) < 10:
                    overview["recent_activity"].append({
                        "issue_number": issue.number,
                        "title": issue.title,
                        "state": issue.state,
                        "updated_at": issue.updated_at.isoformat()
                    })
            
            overview["success"] = True
            return overview
            
        except Exception as e:
            logger.error(f"❌ Failed to get project overview: {e}")
            return {"success": False, "error": str(e)}
    
    async def close_agent_task_issue(
        self,
        issue_number: int,
        completion_comment: str,
        labels_to_add: List[str] = None,
        labels_to_remove: List[str] = None
    ) -> Dict[str, Any]:
        """Close a GitHub issue when a task is completed"""
        try:
            if not self.repo:
                return {"success": False, "error": "GitHub not initialized"}
            
            # Get the issue
            issue = self.repo.get_issue(issue_number)
            
            # Add completion comment
            issue.create_comment(completion_comment)
            
            # Update labels
            current_labels = [label.name for label in issue.labels]
            
            if labels_to_add:
                # Validate and add labels
                for label_name in labels_to_add:
                    if label_name not in current_labels:
                        try:
                            # Check if label exists, create if not
                            try:
                                label = self.repo.get_label(label_name)
                            except GithubException:
                                # Create label if it doesn't exist
                                label = self.repo.create_label(
                                    name=label_name,
                                    color="28a745",  # Green for completion
                                    description=f"Automatically created for {label_name}"
                                )
                            
                            issue.add_to_labels(label)
                            current_labels.append(label_name)
                            
                        except Exception as e:
                            logger.warning(f"Failed to add label {label_name}: {e}")
            
            if labels_to_remove:
                # Remove labels
                for label_name in labels_to_remove:
                    if label_name in current_labels:
                        try:
                            label = self.repo.get_label(label_name)
                            issue.remove_from_labels(label)
                            current_labels.remove(label_name)
                        except Exception as e:
                            logger.warning(f"Failed to remove label {label_name}: {e}")
            
            # Close the issue
            issue.edit(state='closed')
            
            logger.info(f"✅ Successfully closed GitHub issue #{issue_number}")
            
            return {
                "success": True,
                "issue_number": issue_number,
                "issue_url": issue.html_url,
                "labels_added": labels_to_add or [],
                "labels_removed": labels_to_remove or [],
                "closed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to close GitHub issue #{issue_number}: {e}")
            return {"success": False, "error": str(e)}
    
    async def add_comment_to_issue(self, issue_number: int, comment: str) -> Dict[str, Any]:
        """Add a comment to a GitHub issue"""
        try:
            if not self.repo:
                return {"success": False, "error": "GitHub not initialized"}
            
            issue = self.repo.get_issue(issue_number)
            comment_obj = issue.create_comment(comment)
            
            return {
                "success": True,
                "issue_number": issue_number,
                "comment_id": comment_obj.id,
                "comment_url": comment_obj.html_url
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to add comment to issue #{issue_number}: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_issue_labels(
        self,
        issue_number: int,
        labels_to_add: List[str] = None,
        labels_to_remove: List[str] = None
    ) -> Dict[str, Any]:
        """Update labels on a GitHub issue"""
        try:
            if not self.repo:
                return {"success": False, "error": "GitHub not initialized"}
            
            issue = self.repo.get_issue(issue_number)
            current_labels = [label.name for label in issue.labels]
            
            labels_added = []
            labels_removed = []
            
            if labels_to_add:
                for label_name in labels_to_add:
                    if label_name not in current_labels:
                        try:
                            # Check if label exists, create if not
                            try:
                                label = self.repo.get_label(label_name)
                            except GithubException:
                                label = self.repo.create_label(
                                    name=label_name,
                                    color="0052cc",
                                    description=f"Automatically created for {label_name}"
                                )
                            
                            issue.add_to_labels(label)
                            labels_added.append(label_name)
                            
                        except Exception as e:
                            logger.warning(f"Failed to add label {label_name}: {e}")
            
            if labels_to_remove:
                for label_name in labels_to_remove:
                    if label_name in current_labels:
                        try:
                            label = self.repo.get_label(label_name)
                            issue.remove_from_labels(label)
                            labels_removed.append(label_name)
                        except Exception as e:
                            logger.warning(f"Failed to remove label {label_name}: {e}")
            
            return {
                "success": True,
                "issue_number": issue_number,
                "labels_added": labels_added,
                "labels_removed": labels_removed
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to update labels on issue #{issue_number}: {e}")
            return {"success": False, "error": str(e)}

# Global instance
github_project_manager = GitHubProjectManager()