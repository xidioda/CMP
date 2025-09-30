"""
MCP (Model Context Protocol) Server Integration

This module integrates AI agents with MCP servers to enhance development capabilities
through HTTP REST API communication with specialized development tools and services.
"""

import asyncio
import json
import logging
import aiohttp
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class MCPServerType(Enum):
    """Types of MCP servers available"""
    FILESYSTEM = "filesystem"
    GIT = "git"
    DATABASE = "database"
    API = "api"
    COPILOT = "copilot"
    TESTING = "testing"

@dataclass
class MCPServer:
    """Represents an MCP server configuration"""
    name: str
    type: MCPServerType
    url: str
    port: int
    capabilities: List[str]
    active: bool = False

class MCPServerIntegration:
    """Integrates AI agents with MCP servers for enhanced development capabilities"""
    
    def __init__(self):
        self.servers: Dict[str, MCPServer] = {}
        self.active_servers: Dict[str, bool] = {}
        self.load_server_configs()
    
    def load_server_configs(self):
        """Load MCP server configurations"""
        # Default MCP server configurations
        default_servers = [
            MCPServer(
                name="filesystem_mcp",
                type=MCPServerType.FILESYSTEM,
                url="ws://localhost",
                port=8001,
                capabilities=["read_file", "write_file", "list_directory", "file_operations"]
            ),
            MCPServer(
                name="git_mcp", 
                type=MCPServerType.GIT,
                url="ws://localhost",
                port=8002,
                capabilities=["git_status", "git_commit", "git_push", "git_branch", "git_merge"]
            ),
            MCPServer(
                name="database_mcp",
                type=MCPServerType.DATABASE,
                url="ws://localhost", 
                port=8003,
                capabilities=["query_database", "update_schema", "backup_data", "migration"]
            ),
            MCPServer(
                name="copilot_mcp",
                type=MCPServerType.COPILOT,
                url="ws://localhost",
                port=8004,
                capabilities=["code_generation", "code_review", "refactoring", "documentation"]
            ),
            MCPServer(
                name="testing_mcp",
                type=MCPServerType.TESTING,
                url="ws://localhost",
                port=8005,
                capabilities=["run_tests", "generate_tests", "coverage_analysis", "test_reporting"]
            )
        ]
        
        for server in default_servers:
            self.servers[server.name] = server
    
    async def connect_to_server(self, server_name: str) -> Dict[str, Any]:
        """Connect to a specific MCP server via HTTP"""
        if server_name not in self.servers:
            return {
                "success": False,
                "error": f"MCP server '{server_name}' not configured"
            }
        
        server = self.servers[server_name]
        
        try:
            # Connect via HTTP REST API
            async with aiohttp.ClientSession() as session:
                uri = f"http://localhost:{server.port}/health"
                async with session.get(uri, timeout=5) as response:
                    if response.status == 200:
                        health_data = await response.json()
                        server.active = True
                        self.active_servers[server_name] = True
                        
                        logger.info(f"✅ Connected to MCP server {server_name} on port {server.port}")
                        return {
                            "success": True,
                            "server": server_name,
                            "health": health_data,
                            "uri": uri
                        }
                    else:
                        raise Exception(f"HTTP {response.status}")
        except Exception as e:
            server.active = False
            self.active_servers[server_name] = False
            logger.error(f"❌ Failed to connect to MCP server {server_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "server": server_name
            }

    async def execute_tool(self, server_name: str, tool_name: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a tool on an MCP server via HTTP"""
        if server_name not in self.servers:
            return {
                "success": False,
                "error": f"MCP server '{server_name}' not configured"
            }
        
        server = self.servers[server_name]
        if parameters is None:
            parameters = {}
        
        try:
            async with aiohttp.ClientSession() as session:
                uri = f"http://localhost:{server.port}/execute"
                payload = {
                    "tool": tool_name,
                    "parameters": parameters
                }
                
                async with session.post(uri, json=payload, timeout=30) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {error_text}",
                            "server": server_name,
                            "tool": tool_name
                        }
        except Exception as e:
            logger.error(f"❌ Failed to execute tool {tool_name} on {server_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "server": server_name,
                "tool": tool_name
            }
        except Exception as e:
            logger.error(f"❌ Failed to execute tool {tool_name} on {server_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "server": server_name,
                "tool": tool_name
            }

    async def get_server_capabilities(self, server_name: str) -> Dict[str, Any]:
        """Get capabilities from an MCP server"""
        if server_name not in self.servers:
            return {
                "success": False,
                "error": f"MCP server '{server_name}' not configured"
            }
        
        server = self.servers[server_name]
        
        try:
            async with aiohttp.ClientSession() as session:
                uri = f"http://localhost:{server.port}/capabilities"
                async with session.get(uri, timeout=10) as response:
                    if response.status == 200:
                        capabilities = await response.json()
                        return {
                            "success": True,
                            "server": server_name,
                            "capabilities": capabilities
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {error_text}",
                            "server": server_name
                        }
        except Exception as e:
            logger.error(f"❌ Failed to get capabilities from {server_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "server": server_name
            }

    async def list_tools(self, server_name: str) -> Dict[str, Any]:
        """List available tools from an MCP server"""
        if server_name not in self.servers:
            return {
                "success": False,
                "error": f"MCP server '{server_name}' not configured"
            }
        
        server = self.servers[server_name]
        
        try:
            async with aiohttp.ClientSession() as session:
                uri = f"http://localhost:{server.port}/tools"
                async with session.get(uri, timeout=10) as response:
                    if response.status == 200:
                        tools = await response.json()
                        return {
                            "success": True,
                            "server": server_name,
                            "tools": tools
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {error_text}",
                            "server": server_name
                        }
        except Exception as e:
            logger.error(f"❌ Failed to list tools from {server_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "server": server_name
            }
    async def execute_filesystem_operation(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute filesystem operations via MCP server"""
        return await self.execute_tool("filesystem_mcp", operation, kwargs)
    
    async def execute_git_operation(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute git operations via MCP server"""
        return await self.execute_tool("git_mcp", operation, kwargs)
    
    async def execute_copilot_operation(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute Copilot operations via MCP server"""
        return await self.execute_tool("copilot_mcp", operation, kwargs)
    
    async def execute_testing_operation(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute testing operations via MCP server"""
        return await self.execute_tool("testing_mcp", operation, kwargs)
    
    async def enhance_code_with_copilot(self, 
                                       file_path: str, 
                                       enhancement_type: str = "optimization") -> Dict[str, Any]:
        """Use MCP Copilot server to enhance code"""
        parameters = {
            "file_path": file_path,
            "enhancement_type": enhancement_type,
            "preserve_functionality": True,
            "add_documentation": True,
            "improve_error_handling": True
        }
        
        if enhancement_type == "code_review":
            return await self.execute_tool("copilot_mcp", "code_review", {"file_path": file_path})
        elif enhancement_type == "refactoring":
            return await self.execute_tool("copilot_mcp", "suggest_refactoring", {"file_path": file_path})
        elif enhancement_type == "bug_detection":
            return await self.execute_tool("copilot_mcp", "detect_bugs", {"file_path": file_path})
        else:
            return await self.execute_tool("copilot_mcp", "analyze_code", {"file_path": file_path})
    
    async def generate_tests_via_mcp(self, 
                                    module_path: str, 
                                    test_types: List[str] = None) -> Dict[str, Any]:
        """Generate tests using MCP testing server"""
        parameters = {"file_path": module_path}
        return await self.execute_tool("testing_mcp", "discover_tests", parameters)
    
    async def run_comprehensive_tests(self, 
                                     test_scope: str = "all") -> Dict[str, Any]:
        """Run comprehensive tests via MCP testing server"""
        if test_scope == "all":
            return await self.execute_tool("testing_mcp", "run_tests", {})
        else:
            return await self.execute_tool("testing_mcp", "run_specific_test", {"test_path": test_scope})
    
    async def commit_changes_via_mcp(self, 
                                    commit_message: str, 
                                    files_to_commit: List[str] = None) -> Dict[str, Any]:
        """Commit changes using MCP git server"""
        # First add files
        if files_to_commit:
            add_result = await self.execute_tool("git_mcp", "git_add", {"files": files_to_commit})
        else:
            add_result = await self.execute_tool("git_mcp", "git_add", {})
        
        if add_result.get("success"):
            # Then commit
            return await self.execute_tool("git_mcp", "git_commit", {
                "message": commit_message,
                "author": "AI Agent"
            })
        else:
            return add_result
    
    async def check_all_server_status(self) -> Dict[str, Any]:
        """Check status of all configured MCP servers"""
        server_status = {}
        
        for server_name, server in self.servers.items():
            try:
                # Try a simple ping request
                result = await self.send_request(server_name, "ping", {})
                server_status[server_name] = {
                    "active": result["success"],
                    "type": server.type.value,
                    "capabilities": server.capabilities,
                    "url": f"{server.url}:{server.port}"
                }
            except Exception as e:
                server_status[server_name] = {
                    "active": False,
                    "error": str(e),
                    "type": server.type.value
                }
        
        return {
            "success": True,
            "servers": server_status,
            "total_servers": len(self.servers),
            "active_servers": sum(1 for status in server_status.values() if status.get("active"))
        }
    
    async def setup_mcp_development_environment(self) -> Dict[str, Any]:
        """Set up complete MCP development environment"""
        setup_results = []
        
        # Connect to all servers
        for server_name in self.servers.keys():
            result = await self.connect_to_server(server_name)
            setup_results.append({
                "server": server_name,
                "connected": result["success"],
                "details": result
            })
        
        active_servers = [r for r in setup_results if r["connected"]]
        
        logger.info(f"✅ MCP Environment Setup: {len(active_servers)}/{len(self.servers)} servers connected")
        
        return {
            "success": len(active_servers) > 0,
            "setup_results": setup_results,
            "active_servers": len(active_servers),
            "total_servers": len(self.servers),
            "environment_ready": len(active_servers) >= 3  # Need at least 3 servers for basic functionality
        }
    
    async def disconnect_all_servers(self):
        """Disconnect from all MCP servers"""
        for server_name, connection in self.connections.items():
            try:
                await connection.close()
                self.servers[server_name].active = False
                logger.info(f"✅ Disconnected from MCP server: {server_name}")
            except Exception as e:
                logger.error(f"❌ Error disconnecting from {server_name}: {e}")
        
        self.connections.clear()

# Global instance
mcp_integration = MCPServerIntegration()