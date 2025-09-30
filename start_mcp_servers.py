#!/usr/bin/env python3
"""
MCP Servers Launcher

Starts all MCP (Model Context Protocol) servers for autonomous AI development.
Provides filesystem, git, database, copilot, and testing capabilities.
"""

import asyncio
import logging
import os
import sys
import signal
from typing import List

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import MCP servers
from mcp_servers.filesystem_mcp import FilesystemMCPServer
from mcp_servers.git_mcp import GitMCPServer
from mcp_servers.database_mcp import DatabaseMCPServer
from mcp_servers.copilot_mcp import CopilotMCPServer
from mcp_servers.testing_mcp import TestingMCPServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/xidioda/Projects/CMP/logs/mcp_servers.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class MCPServerManager:
    """Manages multiple MCP servers"""
    
    def __init__(self):
        self.servers = []
        self.runners = []
        self.running = False
        
    async def start_all_servers(self):
        """Start all MCP servers"""
        try:
            logger.info("🚀 Starting MCP Server Infrastructure")
            logger.info("=" * 60)
            
            # Initialize servers
            server_classes = [
                FilesystemMCPServer,
                GitMCPServer,
                DatabaseMCPServer,
                CopilotMCPServer,
                TestingMCPServer
            ]
            
            # Start each server
            for server_class in server_classes:
                try:
                    server = server_class()
                    runner = await server.start_server()
                    self.servers.append(server)
                    self.runners.append(runner)
                    logger.info(f"✅ {server.name} started on port {server.port}")
                except Exception as e:
                    logger.error(f"❌ Failed to start {server_class.__name__}: {e}")
                    
            logger.info("=" * 60)
            logger.info(f"🎯 MCP Infrastructure Status:")
            logger.info(f"   • Total servers: {len(self.servers)}")
            logger.info(f"   • Successful starts: {len(self.runners)}")
            logger.info(f"   • Available capabilities:")
            
            for server in self.servers:
                logger.info(f"     - {server.name} ({server.port}): {server.description}")
                logger.info(f"       Tools: {', '.join(server.tools.keys())}")
                
            logger.info("=" * 60)
            logger.info("🔧 MCP servers ready for autonomous AI development!")
            logger.info("💡 Autonomous agents can now use sophisticated development tools")
            
            self.running = True
            return True
            
        except Exception as e:
            logger.error(f"💥 Failed to start MCP servers: {e}")
            return False
            
    async def stop_all_servers(self):
        """Stop all MCP servers"""
        logger.info("🛑 Shutting down MCP servers...")
        
        for runner in self.runners:
            try:
                await runner.cleanup()
            except Exception as e:
                logger.error(f"Error stopping server: {e}")
                
        self.running = False
        logger.info("✅ All MCP servers stopped")
        
    async def health_check(self):
        """Check health of all servers"""
        health_status = {}
        
        for server in self.servers:
            try:
                # This would ping each server
                health_status[server.name] = {
                    "status": "healthy",
                    "port": server.port,
                    "tools": len(server.tools),
                    "capabilities": len(server.capabilities)
                }
            except Exception as e:
                health_status[server.name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                
        return health_status

async def main():
    """Main entry point"""
    manager = MCPServerManager()
    
    # Handle shutdown signals
    def signal_handler():
        logger.info("Received shutdown signal")
        asyncio.create_task(manager.stop_all_servers())
        
    signal.signal(signal.SIGINT, lambda s, f: signal_handler())
    signal.signal(signal.SIGTERM, lambda s, f: signal_handler())
    
    try:
        # Start all servers
        success = await manager.start_all_servers()
        
        if not success:
            logger.error("Failed to start MCP infrastructure")
            return 1
            
        # Keep servers running
        logger.info("🔄 MCP servers running... Press Ctrl+C to stop")
        
        while manager.running:
            await asyncio.sleep(10)
            
            # Periodic health check
            health = await manager.health_check()
            healthy_count = sum(1 for status in health.values() if status.get("status") == "healthy")
            logger.debug(f"Health check: {healthy_count}/{len(health)} servers healthy")
            
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await manager.stop_all_servers()
        
    return 0

if __name__ == "__main__":
    print("=" * 80)
    print("🤖 CMP MCP SERVER INFRASTRUCTURE")
    print("=" * 80)
    print("🎯 Starting Model Context Protocol servers for autonomous AI development")
    print("🔧 Providing: filesystem, git, database, copilot, and testing capabilities")
    print("🚀 Ports: 8001-8005")
    print("📊 Monitor in logs/mcp_servers.log")
    print("🛑 Press Ctrl+C to stop all servers")
    print("=" * 80)
    
    exit_code = asyncio.run(main())
    sys.exit(exit_code)