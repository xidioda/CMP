"""
Base MCP Server Implementation

Provides common functionality for all MCP (Model Context Protocol) servers.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import aiohttp
from aiohttp import web
import traceback

logger = logging.getLogger(__name__)

class BaseMCPServer:
    """Base class for all MCP servers providing common functionality"""
    
    def __init__(self, name: str, port: int, description: str):
        self.name = name
        self.port = port
        self.description = description
        self.app = web.Application()
        self.capabilities = {}
        self.tools = {}
        self.setup_routes()
        
    def setup_routes(self):
        """Setup common routes for all MCP servers"""
        self.app.router.add_get('/', self.health_check)
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_get('/capabilities', self.get_capabilities)
        self.app.router.add_post('/execute', self.execute_tool)
        self.app.router.add_get('/tools', self.list_tools)
        
    async def health_check(self, request):
        """Health check endpoint"""
        return web.json_response({
            "status": "healthy",
            "server": self.name,
            "port": self.port,
            "description": self.description,
            "timestamp": datetime.now().isoformat(),
            "capabilities": list(self.capabilities.keys()),
            "tools_count": len(self.tools)
        })
        
    async def get_capabilities(self, request):
        """Return server capabilities"""
        return web.json_response({
            "server": self.name,
            "capabilities": self.capabilities,
            "tools": list(self.tools.keys())
        })
        
    async def list_tools(self, request):
        """List available tools"""
        tools_info = {}
        for tool_name, tool_func in self.tools.items():
            # Get description from stored descriptions or __doc__
            description = "No description"
            if hasattr(self, '_tool_descriptions') and tool_name in self._tool_descriptions:
                description = self._tool_descriptions[tool_name]
            elif hasattr(tool_func, '__doc__') and tool_func.__doc__:
                description = tool_func.__doc__
                
            tools_info[tool_name] = {
                "name": tool_name,
                "description": description,
                "available": True
            }
        return web.json_response({"tools": tools_info})
        
    async def execute_tool(self, request):
        """Execute a tool with given parameters"""
        try:
            data = await request.json()
            tool_name = data.get('tool')
            parameters = data.get('parameters', {})
            
            if tool_name not in self.tools:
                return web.json_response({
                    "success": False,
                    "error": f"Tool '{tool_name}' not found",
                    "available_tools": list(self.tools.keys())
                }, status=400)
                
            # Execute the tool
            tool_func = self.tools[tool_name]
            result = await tool_func(**parameters)
            
            return web.json_response({
                "success": True,
                "tool": tool_name,
                "result": result,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error executing tool: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return web.json_response({
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }, status=500)
            
    def register_tool(self, name: str, func, description: str = None):
        """Register a tool function"""
        self.tools[name] = func
        # Store description separately instead of modifying __doc__
        if not hasattr(self, '_tool_descriptions'):
            self._tool_descriptions = {}
        if description:
            self._tool_descriptions[name] = description
        logger.info(f"Registered tool '{name}' in {self.name}")
        
    def register_capability(self, name: str, description: str, enabled: bool = True):
        """Register a capability"""
        self.capabilities[name] = {
            "description": description,
            "enabled": enabled
        }
        logger.info(f"Registered capability '{name}' in {self.name}")
        
    async def start_server(self):
        """Start the MCP server"""
        logger.info(f"🚀 Starting {self.name} on port {self.port}")
        logger.info(f"📋 Description: {self.description}")
        logger.info(f"🔧 Tools: {list(self.tools.keys())}")
        logger.info(f"⚡ Capabilities: {list(self.capabilities.keys())}")
        
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', self.port)
        await site.start()
        
        logger.info(f"✅ {self.name} running on http://localhost:{self.port}")
        return runner

# Utility functions for common MCP operations
async def execute_shell_command(command: str, cwd: str = None) -> Dict[str, Any]:
    """Execute a shell command safely"""
    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd
        )
        stdout, stderr = await process.communicate()
        
        return {
            "success": process.returncode == 0,
            "return_code": process.returncode,
            "stdout": stdout.decode('utf-8'),
            "stderr": stderr.decode('utf-8'),
            "command": command
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "command": command
        }

async def read_file_safe(file_path: str) -> Dict[str, Any]:
    """Safely read a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {
            "success": True,
            "content": content,
            "file_path": file_path
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "file_path": file_path
        }

async def write_file_safe(file_path: str, content: str) -> Dict[str, Any]:
    """Safely write to a file"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return {
            "success": True,
            "file_path": file_path,
            "bytes_written": len(content.encode('utf-8'))
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "file_path": file_path
        }