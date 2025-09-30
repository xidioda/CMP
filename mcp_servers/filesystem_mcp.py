#!/usr/bin/env python3
"""
Filesystem MCP Server (Port 8001)

Provides filesystem operations for autonomous AI agents including file reading,
writing, directory operations, and file system analysis.
"""

import os
import asyncio
import logging
import json
from pathlib import Path
from typing import Dict, Any, List
import sys

# Add mcp_servers to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from base_mcp_server import BaseMCPServer, read_file_safe, write_file_safe

logger = logging.getLogger(__name__)

class FilesystemMCPServer(BaseMCPServer):
    """MCP Server for filesystem operations"""
    
    def __init__(self):
        super().__init__(
            name="filesystem_mcp",
            port=8001,
            description="Filesystem operations for autonomous development"
        )
        self.workspace_root = "/Users/xidioda/Projects/CMP"
        self.setup_filesystem_tools()
        self.setup_filesystem_capabilities()
        
    def setup_filesystem_capabilities(self):
        """Register filesystem capabilities"""
        self.register_capability("file_reading", "Read files safely with encoding detection")
        self.register_capability("file_writing", "Write files with backup and validation")
        self.register_capability("directory_operations", "Create, list, and manage directories")
        self.register_capability("file_analysis", "Analyze file structure and dependencies")
        self.register_capability("code_search", "Search through codebase for patterns")
        
    def setup_filesystem_tools(self):
        """Register filesystem tools"""
        self.register_tool("read_file", self.read_file, "Read a file from the filesystem")
        self.register_tool("write_file", self.write_file, "Write content to a file")
        self.register_tool("list_directory", self.list_directory, "List directory contents")
        self.register_tool("create_directory", self.create_directory, "Create a directory")
        self.register_tool("file_exists", self.file_exists, "Check if file exists")
        self.register_tool("get_file_info", self.get_file_info, "Get file metadata")
        self.register_tool("search_files", self.search_files, "Search for files by pattern")
        self.register_tool("analyze_codebase", self.analyze_codebase, "Analyze codebase structure")
        
    async def read_file(self, file_path: str, max_size: int = 1024*1024) -> Dict[str, Any]:
        """Read a file with size limits"""
        try:
            # Ensure path is within workspace
            full_path = os.path.join(self.workspace_root, file_path.lstrip('/'))
            if not full_path.startswith(self.workspace_root):
                return {"success": False, "error": "Path outside workspace"}
                
            if not os.path.exists(full_path):
                return {"success": False, "error": "File not found"}
                
            file_size = os.path.getsize(full_path)
            if file_size > max_size:
                return {"success": False, "error": f"File too large: {file_size} bytes"}
                
            return await read_file_safe(full_path)
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    async def write_file(self, file_path: str, content: str, backup: bool = True) -> Dict[str, Any]:
        """Write content to a file with optional backup"""
        try:
            # Ensure path is within workspace
            full_path = os.path.join(self.workspace_root, file_path.lstrip('/'))
            if not full_path.startswith(self.workspace_root):
                return {"success": False, "error": "Path outside workspace"}
                
            # Create backup if file exists
            if backup and os.path.exists(full_path):
                backup_path = f"{full_path}.backup"
                with open(full_path, 'r') as src, open(backup_path, 'w') as dst:
                    dst.write(src.read())
                    
            # Ensure directory exists
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            return await write_file_safe(full_path, content)
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    async def list_directory(self, dir_path: str = ".") -> Dict[str, Any]:
        """List directory contents"""
        try:
            full_path = os.path.join(self.workspace_root, dir_path.lstrip('/'))
            if not full_path.startswith(self.workspace_root):
                return {"success": False, "error": "Path outside workspace"}
                
            if not os.path.exists(full_path):
                return {"success": False, "error": "Directory not found"}
                
            items = []
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                items.append({
                    "name": item,
                    "type": "directory" if os.path.isdir(item_path) else "file",
                    "size": os.path.getsize(item_path) if os.path.isfile(item_path) else None
                })
                
            return {"success": True, "items": items, "path": dir_path}
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    async def create_directory(self, dir_path: str) -> Dict[str, Any]:
        """Create a directory"""
        try:
            full_path = os.path.join(self.workspace_root, dir_path.lstrip('/'))
            if not full_path.startswith(self.workspace_root):
                return {"success": False, "error": "Path outside workspace"}
                
            os.makedirs(full_path, exist_ok=True)
            return {"success": True, "path": dir_path}
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    async def file_exists(self, file_path: str) -> Dict[str, Any]:
        """Check if file exists"""
        try:
            full_path = os.path.join(self.workspace_root, file_path.lstrip('/'))
            if not full_path.startswith(self.workspace_root):
                return {"success": False, "error": "Path outside workspace"}
                
            exists = os.path.exists(full_path)
            return {"success": True, "exists": exists, "path": file_path}
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    async def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get file metadata"""
        try:
            full_path = os.path.join(self.workspace_root, file_path.lstrip('/'))
            if not full_path.startswith(self.workspace_root):
                return {"success": False, "error": "Path outside workspace"}
                
            if not os.path.exists(full_path):
                return {"success": False, "error": "File not found"}
                
            stat = os.stat(full_path)
            return {
                "success": True,
                "path": file_path,
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "is_file": os.path.isfile(full_path),
                "is_directory": os.path.isdir(full_path)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    async def search_files(self, pattern: str, directory: str = ".") -> Dict[str, Any]:
        """Search for files matching a pattern"""
        try:
            full_path = os.path.join(self.workspace_root, directory.lstrip('/'))
            if not full_path.startswith(self.workspace_root):
                return {"success": False, "error": "Path outside workspace"}
                
            matches = []
            for root, dirs, files in os.walk(full_path):
                for file in files:
                    if pattern.lower() in file.lower():
                        rel_path = os.path.relpath(os.path.join(root, file), self.workspace_root)
                        matches.append(rel_path)
                        
            return {"success": True, "matches": matches, "pattern": pattern}
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    async def analyze_codebase(self, directory: str = ".") -> Dict[str, Any]:
        """Analyze codebase structure"""
        try:
            full_path = os.path.join(self.workspace_root, directory.lstrip('/'))
            if not full_path.startswith(self.workspace_root):
                return {"success": False, "error": "Path outside workspace"}
                
            analysis = {
                "total_files": 0,
                "file_types": {},
                "directories": [],
                "large_files": [],
                "python_modules": []
            }
            
            for root, dirs, files in os.walk(full_path):
                analysis["directories"].extend([os.path.relpath(os.path.join(root, d), self.workspace_root) for d in dirs])
                
                for file in files:
                    analysis["total_files"] += 1
                    file_path = os.path.join(root, file)
                    ext = os.path.splitext(file)[1].lower()
                    
                    if ext not in analysis["file_types"]:
                        analysis["file_types"][ext] = 0
                    analysis["file_types"][ext] += 1
                    
                    # Check for large files
                    size = os.path.getsize(file_path)
                    if size > 100 * 1024:  # > 100KB
                        rel_path = os.path.relpath(file_path, self.workspace_root)
                        analysis["large_files"].append({"path": rel_path, "size": size})
                        
                    # Track Python modules
                    if ext == ".py":
                        rel_path = os.path.relpath(file_path, self.workspace_root)
                        analysis["python_modules"].append(rel_path)
                        
            return {"success": True, "analysis": analysis}
        except Exception as e:
            return {"success": False, "error": str(e)}

async def main():
    """Start the Filesystem MCP Server"""
    server = FilesystemMCPServer()
    runner = await server.start_server()
    
    try:
        # Keep server running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down Filesystem MCP Server...")
        await runner.cleanup()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())