#!/usr/bin/env python3
"""
Minimal test server for AI Agent Control Panels
"""

import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape
import uvicorn
import os

# Create FastAPI app
app = FastAPI(title="CMP - AI Agent Control Panels Test")

# Setup Jinja2 templates
template_env = Environment(
    loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "cmp", "templates")),
    autoescape=select_autoescape(['html', 'xml'])
)

# Mock AI agents registry
AGENTS = {
    "accountant": {
        "name": "AI Accountant",
        "description": "Transaction processing and bookkeeping specialist",
        "status": "active",
        "color": "green"
    },
    "cfo": {
        "name": "AI CFO", 
        "description": "Financial strategy and analysis expert",
        "status": "active",
        "color": "blue"
    },
    "controller": {
        "name": "AI Controller",
        "description": "Risk management and compliance specialist", 
        "status": "active",
        "color": "orange"
    },
    "director": {
        "name": "AI Director",
        "description": "Executive oversight and decision making",
        "status": "active", 
        "color": "purple"
    }
}

@app.get("/", response_class=HTMLResponse)
async def root():
    """Redirect to agents overview"""
    return """
    <html>
        <head><title>CMP - AI Agent Control Panels</title></head>
        <body style="font-family: system-ui; margin: 2rem;">
            <h1>🤖 CMP - AI Agent Control Panels</h1>
            <p>Welcome to the Company Management Platform Agent Control Panels!</p>
            <div style="margin: 2rem 0;">
                <a href="/agents/" style="background: #111; color: white; padding: 1rem 2rem; text-decoration: none; border-radius: 6px; font-weight: bold;">View All Agents →</a>
            </div>
        </body>
    </html>
    """

@app.get("/agents/", response_class=HTMLResponse) 
async def agents_overview():
    """Agents overview page"""
    template = template_env.get_template("agents_overview.html")
    return template.render(agents=AGENTS)

@app.get("/agents/{agent_id}", response_class=HTMLResponse)
async def agent_control_panel(agent_id: str):
    """Individual agent control panel"""
    if agent_id not in AGENTS:
        return HTMLResponse("<h1>Agent not found</h1>", status_code=404)
    
    agent = AGENTS[agent_id]
    template = template_env.get_template(f"agent_{agent_id}.html")
    return template.render(agent=agent, agent_id=agent_id)

@app.post("/agents/{agent_id}/chat")
async def agent_chat(agent_id: str, request: Request):
    """Handle agent chat interactions"""
    if agent_id not in AGENTS:
        return {"error": "Agent not found"}
    
    form_data = await request.form()
    message = form_data.get("message", "")
    
    # Mock response based on agent type
    responses = {
        "accountant": f"As your AI Accountant, I can help with: {message}. Let me process this transaction and update the ledger.",
        "cfo": f"From a strategic financial perspective regarding: {message}. I recommend analyzing the cash flow impact and ROI.",
        "controller": f"For compliance and risk management regarding: {message}. I'll review this against our control framework.",
        "director": f"As your AI Director, considering: {message}. Let me evaluate the strategic implications and resource allocation."
    }
    
    return {
        "response": responses.get(agent_id, "I'm processing your request..."),
        "timestamp": "2024-01-17 15:30:00",
        "agent": AGENTS[agent_id]["name"]
    }

@app.post("/agents/{agent_id}/task")
async def assign_agent_task(agent_id: str, request: Request):
    """Handle task assignments"""
    if agent_id not in AGENTS:
        return {"error": "Agent not found"}
    
    form_data = await request.form()
    task_type = form_data.get("task_type", "")
    
    return {
        "status": "success", 
        "message": f"Task '{task_type}' assigned to {AGENTS[agent_id]['name']}",
        "task_id": f"TASK_{agent_id.upper()}_{asyncio.get_event_loop().time():.0f}"
    }

if __name__ == "__main__":
    print("🚀 Starting CMP AI Agent Control Panels Test Server...")
    print("📋 Available Agents:")
    for agent_id, agent in AGENTS.items():
        print(f"   • {agent['name']} - {agent['description']}")
    print("\n🌐 Server will be available at: http://localhost:8000")
    print("📱 Agent Overview: http://localhost:8000/agents/")
    print("\n" + "="*50)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")