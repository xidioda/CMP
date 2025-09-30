#!/usr/bin/env python3
"""
Git MCP Server (Port 8002)

Provides Git operations for autonomous AI agents including repository management,
commit operations, branch management, and repository analysis.
"""

import os
import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, List
import sys

# Add mcp_servers to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from base_mcp_server import BaseMCPServer, execute_shell_command

logger = logging.getLogger(__name__)

class GitMCPServer(BaseMCPServer):
    """MCP Server for Git operations"""
    
    def __init__(self):
        super().__init__(
            name="git_mcp",
            port=8002,
            description="Git repository operations for autonomous development"
        )
        self.workspace_root = "/Users/xidioda/Projects/CMP"
        self.setup_git_tools()
        self.setup_git_capabilities()
        
    def setup_git_capabilities(self):
        """Register Git capabilities"""
        self.register_capability("repository_status", "Check repository status and changes")
        self.register_capability("commit_operations", "Create commits with proper messages")
        self.register_capability("branch_management", "Create, switch, and manage branches")
        self.register_capability("remote_operations", "Push, pull, and sync with remote")
        self.register_capability("history_analysis", "Analyze commit history and changes")
        
    def setup_git_tools(self):
        """Register Git tools"""
        self.register_tool("git_status", self.git_status, "Get repository status")
        self.register_tool("git_add", self.git_add, "Stage files for commit")
        self.register_tool("git_commit", self.git_commit, "Create a commit")
        self.register_tool("git_push", self.git_push, "Push changes to remote")
        self.register_tool("git_pull", self.git_pull, "Pull changes from remote")
        self.register_tool("git_log", self.git_log, "Get commit history")
        self.register_tool("git_diff", self.git_diff, "Show differences")
        self.register_tool("git_branch", self.git_branch, "Branch operations")
        self.register_tool("git_stash", self.git_stash, "Stash operations")
        self.register_tool("analyze_changes", self.analyze_changes, "Analyze uncommitted changes")
        
    async def git_status(self) -> Dict[str, Any]:
        """Get Git repository status"""
        result = await execute_shell_command("git status --porcelain", self.workspace_root)
        if not result["success"]:
            return result
            
        # Parse status output
        lines = result["stdout"].strip().split('\n') if result["stdout"].strip() else []
        changes = {
            "modified": [],
            "added": [],
            "deleted": [],
            "untracked": []
        }
        
        for line in lines:
            if len(line) >= 3:
                status = line[:2]
                filename = line[3:]
                
                if status.startswith('M'):
                    changes["modified"].append(filename)
                elif status.startswith('A'):
                    changes["added"].append(filename)
                elif status.startswith('D'):
                    changes["deleted"].append(filename)
                elif status.startswith('??'):
                    changes["untracked"].append(filename)
                    
        # Get current branch
        branch_result = await execute_shell_command("git branch --show-current", self.workspace_root)
        current_branch = branch_result["stdout"].strip() if branch_result["success"] else "unknown"
        
        return {
            "success": True,
            "changes": changes,
            "current_branch": current_branch,
            "has_changes": any(changes.values())
        }
        
    async def git_add(self, files: List[str] = None) -> Dict[str, Any]:
        """Stage files for commit"""
        if files is None:
            command = "git add ."
        else:
            files_str = " ".join(f'"{f}"' for f in files)
            command = f"git add {files_str}"
            
        result = await execute_shell_command(command, self.workspace_root)
        return result
        
    async def git_commit(self, message: str, author: str = None) -> Dict[str, Any]:
        """Create a commit"""
        if not message:
            return {"success": False, "error": "Commit message is required"}
            
        command = f'git commit -m "{message}"'
        if author:
            command = f'git -c user.name="{author}" -c user.email="ai@cmp.dev" {command}'
            
        result = await execute_shell_command(command, self.workspace_root)
        return result
        
    async def git_push(self, remote: str = "origin", branch: str = None) -> Dict[str, Any]:
        """Push changes to remote"""
        if branch is None:
            # Get current branch
            branch_result = await execute_shell_command("git branch --show-current", self.workspace_root)
            branch = branch_result["stdout"].strip() if branch_result["success"] else "main"
            
        command = f"git push {remote} {branch}"
        result = await execute_shell_command(command, self.workspace_root)
        return result
        
    async def git_pull(self, remote: str = "origin", branch: str = None) -> Dict[str, Any]:
        """Pull changes from remote"""
        if branch is None:
            command = f"git pull {remote}"
        else:
            command = f"git pull {remote} {branch}"
            
        result = await execute_shell_command(command, self.workspace_root)
        return result
        
    async def git_log(self, count: int = 10, format: str = "oneline") -> Dict[str, Any]:
        """Get commit history"""
        if format == "oneline":
            command = f"git log --oneline -n {count}"
        elif format == "full":
            command = f"git log --pretty=fuller -n {count}"
        else:
            command = f"git log -n {count}"
            
        result = await execute_shell_command(command, self.workspace_root)
        
        if result["success"] and result["stdout"]:
            commits = []
            for line in result["stdout"].strip().split('\n'):
                if line.strip():
                    commits.append(line.strip())
            result["commits"] = commits
            
        return result
        
    async def git_diff(self, file: str = None, staged: bool = False) -> Dict[str, Any]:
        """Show differences"""
        command = "git diff"
        if staged:
            command += " --staged"
        if file:
            command += f' "{file}"'
            
        result = await execute_shell_command(command, self.workspace_root)
        return result
        
    async def git_branch(self, action: str = "list", branch_name: str = None) -> Dict[str, Any]:
        """Branch operations"""
        if action == "list":
            result = await execute_shell_command("git branch", self.workspace_root)
        elif action == "create" and branch_name:
            result = await execute_shell_command(f"git branch {branch_name}", self.workspace_root)
        elif action == "switch" and branch_name:
            result = await execute_shell_command(f"git checkout {branch_name}", self.workspace_root)
        elif action == "delete" and branch_name:
            result = await execute_shell_command(f"git branch -d {branch_name}", self.workspace_root)
        else:
            return {"success": False, "error": "Invalid branch action or missing branch name"}
            
        return result
        
    async def git_stash(self, action: str = "save", message: str = None) -> Dict[str, Any]:
        """Stash operations"""
        if action == "save":
            command = "git stash"
            if message:
                command += f' push -m "{message}"'
        elif action == "pop":
            command = "git stash pop"
        elif action == "list":
            command = "git stash list"
        elif action == "clear":
            command = "git stash clear"
        else:
            return {"success": False, "error": "Invalid stash action"}
            
        result = await execute_shell_command(command, self.workspace_root)
        return result
        
    async def analyze_changes(self) -> Dict[str, Any]:
        """Analyze uncommitted changes in detail"""
        try:
            # Get status
            status = await self.git_status()
            if not status["success"]:
                return status
                
            # Get diff for modified files
            diff_result = await self.git_diff()
            
            # Analyze each modified file
            file_analysis = {}
            for filename in status["changes"]["modified"]:
                file_diff = await self.git_diff(file=filename)
                if file_diff["success"]:
                    lines = file_diff["stdout"].split('\n')
                    additions = sum(1 for line in lines if line.startswith('+') and not line.startswith('+++'))
                    deletions = sum(1 for line in lines if line.startswith('-') and not line.startswith('---'))
                    
                    file_analysis[filename] = {
                        "additions": additions,
                        "deletions": deletions,
                        "net_change": additions - deletions
                    }
                    
            return {
                "success": True,
                "status": status["changes"],
                "file_analysis": file_analysis,
                "total_changes": sum(fa["additions"] + fa["deletions"] for fa in file_analysis.values()),
                "diff_summary": diff_result["stdout"][:1000] if diff_result["success"] else None
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

async def main():
    """Start the Git MCP Server"""
    server = GitMCPServer()
    runner = await server.start_server()
    
    try:
        # Keep server running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down Git MCP Server...")
        await runner.cleanup()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())