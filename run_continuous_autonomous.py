#!/usr/bin/env python3
"""
Continuous Autonomous Organization Runner

This script starts the autonomous scheduler and runs all AI agents continuously
in the background, performing real development work automatically.
"""

import asyncio
import logging
import sys
import os

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cmp.utils.autonomous_scheduler import autonomous_scheduler
from cmp.agents.autonomous_developer import AutonomousDeveloperAgent
from cmp.agents.lead_developer import LeadDeveloperAgent
from cmp.agents.n8n_manager import N8NWorkflowManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/autonomous_continuous.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Start continuous autonomous operation with all AI agents"""
    logger.info("🚀 Starting Continuous Autonomous AI Organization")
    logger.info("💡 All agents will perform REAL development work using N8N and MCP servers")
    
    try:
        # Initialize and register AI agents
        autonomous_dev = AutonomousDeveloperAgent()
        lead_dev = LeadDeveloperAgent()
        n8n_manager = N8NWorkflowManager()
        
        # Register agents with the scheduler
        autonomous_scheduler.register_agent("autonomous_developer", autonomous_dev)
        autonomous_scheduler.register_agent("lead_developer", lead_dev)
        autonomous_scheduler.register_agent("n8n_manager", n8n_manager)
        
        logger.info("✅ Registered 3 AI agents for continuous autonomous operation")
        logger.info("⏰ Agents will execute real tasks every 5 minutes")
        logger.info("🔧 Tasks will use N8N workflows and MCP servers for real work")
        logger.info("📊 Monitor progress in logs/autonomous_continuous.log and local_storage/execution_log.json")
        
        # Start the continuous scheduler
        await autonomous_scheduler.start_scheduler()
        
    except KeyboardInterrupt:
        logger.info("🛑 Stopping continuous autonomous operation...")
        autonomous_scheduler.stop_scheduler()
    except Exception as e:
        logger.error(f"💥 Error in continuous autonomous operation: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    print("=" * 80)
    print("🤖 CMP CONTINUOUS AUTONOMOUS AI ORGANIZATION")
    print("=" * 80)
    print("🎯 Starting continuous autonomous operation...")
    print("💻 AI agents will perform REAL development work")
    print("🔧 Using N8N workflows and MCP servers")
    print("📊 Monitor in logs and local_storage/execution_log.json")
    print("🛑 Press Ctrl+C to stop")
    print("=" * 80)
    
    asyncio.run(main())