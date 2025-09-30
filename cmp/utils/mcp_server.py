"""
Model Context Protocol (MCP) Server for AI Agent Tool Access

Provides AI agents with real tool capabilities:
- VS Code integration (file operations, copilot, extensions)
- Terminal command execution  
- N8N workflow management
- GitHub API operations
- File system operations
- Process management
- Advanced Learning (Web search, YouTube transcripts, MCP discovery)
"""

import asyncio
import json
import subprocess
import os
import requests
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import tempfile
import sys
import urllib.parse
import re
import yt_dlp
import openai
from bs4 import BeautifulSoup
import time

logger = logging.getLogger(__name__)

class MCPServer:
    """Model Context Protocol server for AI agent tool access with advanced learning capabilities"""
    
    def __init__(self, workspace_path: str = "/Users/xidioda/Projects/CMP"):
        self.workspace_path = Path(workspace_path)
        self.vscode_cli = "code"  # VS Code CLI command
        self.n8n_base_url = "http://localhost:5678"
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.active_processes = {}
        
    # VS Code Integration Tools
    
    async def vscode_open_file(self, file_path: str, line_number: Optional[int] = None) -> Dict[str, Any]:
        """Open file in VS Code"""
        try:
            full_path = self.workspace_path / file_path
            command = [self.vscode_cli, str(full_path)]
            
            if line_number:
                command.extend(["-g", f"{line_number}"])
            
            result = subprocess.run(command, capture_output=True, text=True)
            
            return {
                "success": result.returncode == 0,
                "message": f"Opened {file_path} in VS Code",
                "error": result.stderr if result.returncode != 0 else None
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def vscode_run_command(self, command: str, args: Optional[List] = None) -> Dict[str, Any]:
        """Execute VS Code command via CLI"""
        try:
            cmd_parts = [self.vscode_cli]
            
            if command == "install-extension":
                cmd_parts.extend(["--install-extension", args[0] if args else ""])
            elif command == "list-extensions":
                cmd_parts.append("--list-extensions")
            elif command == "open-workspace":
                cmd_parts.extend(["--folder-uri", str(self.workspace_path)])
            elif command == "new-file":
                cmd_parts.extend(["--new-window", "--file-uri", args[0] if args else ""])
                
            result = subprocess.run(cmd_parts, capture_output=True, text=True)
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def vscode_create_file_with_content(self, file_path: str, content: str, 
                                            use_copilot: bool = True) -> Dict[str, Any]:
        """Create file with content and optionally trigger Copilot suggestions"""
        try:
            full_path = self.workspace_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write initial content
            with open(full_path, 'w') as f:
                f.write(content)
            
            # Open in VS Code
            await self.vscode_open_file(file_path)
            
            # Add Copilot prompt if enabled
            if use_copilot:
                copilot_prompt = f"\n\n# TODO: Use GitHub Copilot to enhance this file\n# Created by AI Agent at {datetime.now().isoformat()}\n"
                with open(full_path, 'a') as f:
                    f.write(copilot_prompt)
            
            return {
                "success": True,
                "message": f"Created {file_path} with Copilot integration",
                "file_path": str(full_path)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Terminal Operations
    
    async def terminal_execute(self, command: str, background: bool = False, timeout: int = 30) -> Dict[str, Any]:
        """Execute command in terminal"""
        try:
            if background:
                # Start background process
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=str(self.workspace_path)
                )
                
                # Store process for monitoring
                process_id = f"proc_{len(self.active_processes)}"
                self.active_processes[process_id] = process
                
                return {
                    "success": True,
                    "message": f"Started background process: {command}",
                    "process_id": process_id
                }
            else:
                # Execute and wait for completion
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=str(self.workspace_path),
                    timeout=timeout
                )
                
                return {
                    "success": result.returncode == 0,
                    "output": result.stdout,
                    "error": result.stderr,
                    "return_code": result.returncode
                }
                
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def terminal_get_process_status(self, process_id: str) -> Dict[str, Any]:
        if process_id not in self.active_processes:
            return {"success": False, "error": "Process not found"}
            
        process = self.active_processes[process_id]
        poll_result = process.poll()
        
        if poll_result is None:
            # Process still running
            return {
                "success": True,
                "status": "running",
                "pid": process.pid,
                "process_id": process_id
            }
        else:
            # Process completed
            stdout, stderr = process.communicate()
            del self.active_processes[process_id]
            
            return {
                "success": True,
                "status": "completed",
                "return_code": poll_result,
                "output": stdout.decode() if stdout else "",
                "error": stderr.decode() if stderr else ""
            }
            
    # N8N Integration
    
    async def n8n_install_and_setup(self) -> Dict[str, Any]:
        """Install and setup N8N locally"""
        try:
            # Check if N8N is already installed
            check_result = await self.terminal_execute("which n8n", timeout=10)
            
            if check_result["success"]:
                return {"success": True, "message": "N8N already installed", "path": check_result["output"].strip()}
            
            # Install N8N globally
            install_result = await self.terminal_execute("npm install -g n8n", timeout=120)
            
            if install_result["success"]:
                return {"success": True, "message": "N8N installed successfully"}
            else:
                return {"success": False, "error": f"Failed to install N8N: {install_result['error']}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def n8n_create_workflow(self, workflow_name: str, workflow_config: Dict) -> Dict[str, Any]:
        """Create N8N workflow"""
        try:
            # N8N API endpoint for creating workflows
            url = f"{self.n8n_base_url}/rest/workflows"
            
            workflow_data = {
                "name": workflow_name,
                "nodes": workflow_config.get("nodes", []),
                "connections": workflow_config.get("connections", {}),
                "active": workflow_config.get("active", True)
            }
            
            response = requests.post(url, json=workflow_data)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": f"Created workflow: {workflow_name}",
                    "workflow_id": response.json().get("id")
                }
            else:
                return {"success": False, "error": f"Failed to create workflow: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def n8n_trigger_workflow(self, workflow_id: str, trigger_data: Dict = None) -> Dict[str, Any]:
        """Trigger N8N workflow execution"""
        try:
            url = f"{self.n8n_base_url}/rest/workflows/{workflow_id}/execute"
            
            response = requests.post(url, json=trigger_data or {})
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": f"Triggered workflow: {workflow_id}",
                    "execution_id": response.json().get("id")
                }
            else:
                return {"success": False, "error": f"Failed to trigger workflow: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # GitHub Integration
    
    async def github_create_issue(self, repo: str, title: str, body: str, labels: List[str] = None) -> Dict[str, Any]:
        """Create GitHub issue"""
        try:
            if not self.github_token:
                return {"success": False, "error": "GitHub token not configured"}
            
            url = f"https://api.github.com/repos/{repo}/issues"
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            data = {
                "title": title,
                "body": body,
                "labels": labels or []
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 201:
                issue_data = response.json()
                return {
                    "success": True,
                    "message": f"Created issue: {title}",
                    "issue_url": issue_data["html_url"],
                    "issue_number": issue_data["number"]
                }
            else:
                return {"success": False, "error": f"Failed to create issue: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def github_create_pull_request(self, repo: str, title: str, head: str, base: str, body: str = "") -> Dict[str, Any]:
        """Create GitHub pull request"""
        try:
            if not self.github_token:
                return {"success": False, "error": "GitHub token not configured"}
            
            url = f"https://api.github.com/repos/{repo}/pulls"
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            data = {
                "title": title,
                "head": head,
                "base": base,
                "body": body
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 201:
                pr_data = response.json()
                return {
                    "success": True,
                    "message": f"Created PR: {title}",
                    "pr_url": pr_data["html_url"],
                    "pr_number": pr_data["number"]
                }
            else:
                return {"success": False, "error": f"Failed to create PR: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Project Management
    
    async def create_project_structure(self, project_name: str, project_type: str = "python") -> Dict[str, Any]:
        """Create project structure based on type"""
        try:
            project_path = self.workspace_path / "projects" / project_name
            project_path.mkdir(parents=True, exist_ok=True)
            
            files_created = []
            
            if project_type == "python":
                # Create Python project structure
                (project_path / "__init__.py").touch()
                (project_path / "main.py").write_text("#!/usr/bin/env python3\n\ndef main():\n    print(f'Hello from {project_name}!')\n\nif __name__ == '__main__':\n    main()\n")
                (project_path / "requirements.txt").write_text("# Add your dependencies here\n")
                (project_path / "README.md").write_text(f"# {project_name}\n\nDescription of your project.\n")
                files_created = ["__init__.py", "main.py", "requirements.txt", "README.md"]
                
            elif project_type == "node":
                # Create Node.js project structure  
                package_json = {
                    "name": project_name,
                    "version": "1.0.0",
                    "description": "",
                    "main": "index.js",
                    "scripts": {"start": "node index.js"},
                    "dependencies": {}
                }
                (project_path / "package.json").write_text(json.dumps(package_json, indent=2))
                (project_path / "index.js").write_text(f"console.log('Hello from {project_name}!');\n")
                (project_path / "README.md").write_text(f"# {project_name}\n\nDescription of your project.\n")
                files_created = ["package.json", "index.js", "README.md"]
            
            return {
                "success": True,
                "message": f"Created {project_type} project: {project_name}",
                "project_path": str(project_path),
                "files_created": files_created,
                "project_type": project_type
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Advanced Learning and Automation Tools
    
    async def web_search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Search the web using DuckDuckGo"""
        try:
            url = f"https://duckduckgo.com/html/?q={query}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = []
            for result in soup.find_all('a', {'class': 'result__a'})[:max_results]:
                title = result.get_text(strip=True)
                href = result.get('href')
                if href and title:
                    results.append({"title": title, "url": href})
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "count": len(results)
            }
        except Exception as e:
            return {"success": False, "error": str(e), "query": query}
    
    async def youtube_get_transcript(self, video_url: str, language: str = 'en') -> Dict[str, Any]:
        """Get transcript from YouTube video for learning purposes"""
        try:
            # Extract video ID from URL
            if 'youtube.com/watch?v=' in video_url:
                video_id = video_url.split('watch?v=')[1].split('&')[0]
            elif 'youtu.be/' in video_url:
                video_id = video_url.split('youtu.be/')[1].split('?')[0]
            else:
                return {"success": False, "error": "Invalid YouTube URL"}
            
            # Get video info using yt-dlp
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                title = info.get('title', 'Unknown')
                duration = info.get('duration', 0)
            
            # Get transcript
            try:
                from youtube_transcript_api import YouTubeTranscriptApi
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
                full_transcript = ' '.join([item['text'] for item in transcript_list])
                
                return {
                    "success": True,
                    "video_id": video_id,
                    "title": title,
                    "duration": duration,
                    "transcript": full_transcript,
                    "language": language,
                    "transcript_length": len(full_transcript)
                }
            except Exception as transcript_error:
                return {
                    "success": False,
                    "error": f"Could not get transcript: {str(transcript_error)}",
                    "video_id": video_id,
                    "title": title
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def discover_mcp_servers(self, search_term: str = "mcp-server", max_results: int = 10) -> Dict[str, Any]:
        """Discover new MCP servers from GitHub"""
        try:
            if not self.github_token:
                return {"success": False, "error": "GitHub token not configured"}
            
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # Search GitHub repositories
            search_url = f"https://api.github.com/search/repositories?q={search_term}+language:python+OR+language:typescript&sort=stars&order=desc&per_page={max_results}"
            response = requests.get(search_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                servers = []
                
                for repo in data.get('items', []):
                    servers.append({
                        'name': repo['name'],
                        'full_name': repo['full_name'],
                        'description': repo.get('description', ''),
                        'stars': repo.get('stargazers_count', 0),
                        'language': repo.get('language', 'Unknown'),
                        'clone_url': repo['clone_url'],
                        'updated_at': repo['updated_at']
                    })
                
                return {
                    "success": True,
                    "search_term": search_term,
                    "servers": servers,
                    "total_found": data.get('total_count', 0)
                }
            else:
                return {"success": False, "error": f"GitHub API error: {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def install_mcp_server(self, repo_url: str, server_name: str) -> Dict[str, Any]:
        """Install a new MCP server from GitHub repository"""
        try:
            install_path = self.workspace_path / "local_storage" / "mcp_servers" / server_name
            install_path.mkdir(parents=True, exist_ok=True)
            
            # Clone the repository
            clone_cmd = f"git clone {repo_url} {install_path}"
            result = subprocess.run(clone_cmd.split(), capture_output=True, text=True, cwd=str(install_path.parent))
            
            if result.returncode != 0:
                return {"success": False, "error": f"Failed to clone repository: {result.stderr}"}
            
            # Check for package.json or requirements.txt and install dependencies
            package_json = install_path / "package.json"
            requirements_txt = install_path / "requirements.txt"
            pyproject_toml = install_path / "pyproject.toml"
            
            install_commands = []
            
            if package_json.exists():
                install_commands.append(f"cd {install_path} && npm install")
            
            if requirements_txt.exists():
                install_commands.append(f"cd {install_path} && pip install -r requirements.txt")
            elif pyproject_toml.exists():
                install_commands.append(f"cd {install_path} && pip install -e .")
            
            # Execute installation commands
            for cmd in install_commands:
                install_result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if install_result.returncode != 0:
                    return {
                        "success": False,
                        "error": f"Failed to install dependencies: {install_result.stderr}",
                        "install_path": str(install_path)
                    }
            
            return {
                "success": True,
                "message": f"Successfully installed MCP server: {server_name}",
                "install_path": str(install_path),
                "dependencies_installed": len(install_commands) > 0
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def setup_real_n8n_server(self) -> Dict[str, Any]:
        """Setup a real N8N server instance"""
        try:
            # Check if N8N is already running
            try:
                response = requests.get("http://localhost:5678/rest/active", timeout=5)
                if response.status_code == 200:
                    return {
                        "success": True,
                        "message": "N8N server is already running on localhost:5678",
                        "status": "already_running"
                    }
            except:
                pass  # N8N not running, continue with setup
            
            # Install N8N globally if not installed
            check_cmd = subprocess.run(["which", "n8n"], capture_output=True)
            if check_cmd.returncode != 0:
                # Install N8N
                install_result = subprocess.run(["npm", "install", "-g", "n8n"], 
                                              capture_output=True, text=True)
                if install_result.returncode != 0:
                    return {
                        "success": False,
                        "error": f"Failed to install N8N: {install_result.stderr}"
                    }
            
            # Create N8N data directory
            n8n_data_dir = self.workspace_path / "local_storage" / "n8n_data"
            n8n_data_dir.mkdir(parents=True, exist_ok=True)
            
            # Set N8N environment variables and start server
            env = os.environ.copy()
            env.update({
                "N8N_USER_FOLDER": str(n8n_data_dir),
                "N8N_PORT": "5678",
                "N8N_PROTOCOL": "http",
                "N8N_HOST": "localhost",
                "WEBHOOK_URL": "http://localhost:5678/",
            })
            
            # Start N8N in background
            process = subprocess.Popen(
                ["n8n", "start"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(n8n_data_dir)
            )
            
            # Store process for monitoring
            self.active_processes["n8n_server"] = process
            
            # Wait a moment and check if it started successfully
            time.sleep(3)
            try:
                response = requests.get("http://localhost:5678/rest/active", timeout=10)
                if response.status_code == 200:
                    return {
                        "success": True,
                        "message": "N8N server started successfully on localhost:5678",
                        "status": "started",
                        "data_directory": str(n8n_data_dir),
                        "process_id": process.pid,
                        "url": "http://localhost:5678"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"N8N server started but not responding properly (status: {response.status_code})"
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"N8N server started but connection failed: {str(e)}"
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}

# Global MCP server instance
mcp_server = MCPServer()

# Tool registry for agents with advanced learning capabilities
AGENT_TOOLS = {
    # VS Code Integration
    "vscode_open_file": mcp_server.vscode_open_file,
    "vscode_run_command": mcp_server.vscode_run_command,
    "vscode_create_file_with_content": mcp_server.vscode_create_file_with_content,
    
    # Terminal Operations
    "terminal_execute": mcp_server.terminal_execute,
    "terminal_get_process_status": mcp_server.terminal_get_process_status,
    
    # N8N Automation
    "n8n_install_and_setup": mcp_server.n8n_install_and_setup,
    "n8n_create_workflow": mcp_server.n8n_create_workflow,
    "n8n_trigger_workflow": mcp_server.n8n_trigger_workflow,
    "setup_real_n8n_server": mcp_server.setup_real_n8n_server,
    
    # GitHub Integration
    "github_create_issue": mcp_server.github_create_issue,
    "github_create_pull_request": mcp_server.github_create_pull_request,
    
    # Project Management
    "create_project_structure": mcp_server.create_project_structure,
    
    # Advanced Learning and Automation
    "web_search": mcp_server.web_search,
    "youtube_get_transcript": mcp_server.youtube_get_transcript,
    "discover_mcp_servers": mcp_server.discover_mcp_servers,
    "install_mcp_server": mcp_server.install_mcp_server,
}