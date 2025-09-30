"""
MCP (Model Context Protocol) Server Integration

This module integrates AI agents with MCP servers to enhance development capabilities
through structured communication with specialized development tools and services.
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

# Use aiohttp for WebSocket communication instead of websockets
# This avoids dependency issues while maintaining functionality

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
        self.connections: Dict[str, aiohttp.ClientWebSocketResponse] = {}
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
        """Connect to a specific MCP server"""
        if server_name not in self.servers:
            return {
                "success": False,
                "error": f"MCP server '{server_name}' not configured"
            }
        
        server = self.servers[server_name]
        
        try:
            # Connect via WebSocket using aiohttp
            session = aiohttp.ClientSession()
            uri = f"{server.url}:{server.port}/ws"
            connection = await session.ws_connect(uri, timeout=10)
            
            # Send handshake
            handshake = {
                "type": "handshake",
                "protocol": "mcp",
                "version": "1.0",
                "client_id": "cmp_ai_agent",
                "timestamp": datetime.now().isoformat()
            }
            
            await connection.send_str(json.dumps(handshake))
            response = await connection.receive()
            
            if response.type == aiohttp.WSMsgType.TEXT:
                response_data = json.loads(response.data)
                
                if response_data.get("status") == "connected":
                    self.connections[server_name] = connection
                    server.active = True
                    
                    logger.info(f"✅ Connected to MCP server: {server_name}")
                    return {
                        "success": True,
                        "server_name": server_name,
                        "server_type": server.type.value,
                        "capabilities": server.capabilities,
                        "connected": True
                    }
                else:
                    await session.close()
                    return {
                        "success": False,
                        "error": f"MCP server handshake failed: {response_data}"
                    }
            else:
                await session.close()
                return {
                    "success": False,
                    "error": "Invalid response from MCP server"
                }
                
        except asyncio.TimeoutError:
            logger.error(f"⏰ Connection to MCP server {server_name} timed out")
            return {
                "success": False,
                "error": f"Connection timeout to {server_name}"
            }
        except Exception as e:
            logger.error(f"❌ Failed to connect to MCP server {server_name}: {e}")
            return {
                "success": False,
                "error": f"Connection failed: {str(e)}"
            }
    
    async def send_request(self, 
                          server_name: str, 
                          operation: str, 
                          parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to an MCP server"""
        if server_name not in self.connections:
            # Try to connect first
            connect_result = await self.connect_to_server(server_name)
            if not connect_result["success"]:
                return connect_result
        
        connection = self.connections[server_name]
        
        try:
            request = {
                "type": "request",
                "operation": operation,
                "parameters": parameters,
                "request_id": f"req_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat()
            }
            
            await connection.send_str(json.dumps(request))
            response = await asyncio.wait_for(connection.receive(), timeout=30)
            
            if response.type == aiohttp.WSMsgType.TEXT:
                response_data = json.loads(response.data)
                
                logger.info(f"✅ MCP request successful: {server_name}.{operation}")
                return {
                    "success": True,
                    "server_name": server_name,
                    "operation": operation,
                    "response": response_data
                }
            else:
                return {
                    "success": False,
                    "error": f"Invalid response type from {server_name}"
                }
            
        except asyncio.TimeoutError:
            logger.error(f"⏰ MCP request timeout: {server_name}.{operation}")
            return {
                "success": False,
                "error": f"Request timeout for {operation} on {server_name}"
            }
        except Exception as e:
            logger.error(f"❌ MCP request failed: {server_name}.{operation} - {e}")
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }
    
    async def execute_filesystem_operation(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute filesystem operations via MCP server"""
        return await self.send_request("filesystem_mcp", operation, kwargs)
    
    async def execute_git_operation(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute git operations via MCP server"""
        return await self.send_request("git_mcp", operation, kwargs)
    
    async def execute_copilot_operation(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute Copilot operations via MCP server"""
        return await self.send_request("copilot_mcp", operation, kwargs)
    
    async def execute_testing_operation(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute testing operations via MCP server"""
        return await self.send_request("testing_mcp", operation, kwargs)
    
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
        
        return await self.execute_copilot_operation("enhance_code", **parameters)
    
    async def generate_tests_via_mcp(self, 
                                    module_path: str, 
                                    test_types: List[str] = None) -> Dict[str, Any]:
        """Generate tests using MCP testing server"""
        if test_types is None:
            test_types = ["unit", "integration"]
        
        parameters = {
            "module_path": module_path,
            "test_types": test_types,
            "coverage_target": 80,
            "framework": "pytest"
        }
        
        return await self.execute_testing_operation("generate_tests", **parameters)
    
    async def run_comprehensive_tests(self, 
                                     test_scope: str = "all") -> Dict[str, Any]:
        """Run comprehensive tests via MCP testing server"""
        parameters = {
            "test_scope": test_scope,
            "generate_coverage": True,
            "run_integration_tests": True,
            "validate_performance": True
        }
        
        return await self.execute_testing_operation("run_comprehensive_tests", **parameters)
    
    async def commit_changes_via_mcp(self, 
                                    commit_message: str, 
                                    files_to_commit: List[str] = None) -> Dict[str, Any]:
        """Commit changes using MCP git server"""
        parameters = {
            "commit_message": commit_message,
            "files": files_to_commit or [],
            "auto_stage": True,
            "verify_tests": True
        }
        
        return await self.execute_git_operation("commit_changes", **parameters)
    
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