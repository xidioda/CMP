from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Form, Request, UploadFile, File, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from ..db import get_db
from ..models import append_ledger_entry, User, UserRole
from ..utils.ocr import ocr_processor
from ..logging_config import get_logger
from .auth import get_current_user

logger = get_logger("dashboard")

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def root_redirect():
    return RedirectResponse(url="/login")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Serve login page for browser access"""
    login_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CMP Login</title>
        <style>
            body { font-family: system-ui, -apple-system, sans-serif; margin: 0; padding: 2rem; background: #f3f4f6; }
            .container { max-width: 400px; margin: 2rem auto; background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            h1 { text-align: center; margin-bottom: 2rem; color: #111827; }
            input { width: 100%; padding: 0.75rem; margin: 0.5rem 0 1rem; border: 1px solid #d1d5db; border-radius: 6px; box-sizing: border-box; }
            button { width: 100%; background: #111827; color: white; padding: 0.75rem; border: none; border-radius: 6px; cursor: pointer; font-size: 1rem; }
            button:hover { background: #374151; }
            .error { color: #dc2626; margin-top: 1rem; }
            .demo-info { background: #ecfdf5; border: 1px solid #10b981; padding: 1rem; border-radius: 6px; margin-bottom: 1rem; font-size: 0.9rem; }
            .success { color: #059669; margin-top: 1rem; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>CMP Dashboard Login</h1>
            <div class="demo-info">
                <strong>Demo Credentials:</strong><br>
                Email: admin@cmp.com<br>
                Password: admin123
            </div>
            <form id="loginForm">
                <input type="email" id="email" placeholder="Email" required value="admin@cmp.com">
                <input type="password" id="password" placeholder="Password" required value="admin123">
                <button type="submit">Login</button>
            </form>
            <div id="error" class="error"></div>
            <div id="success" class="success"></div>
        </div>
        
        <script>
            document.getElementById('loginForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const email = document.getElementById('email').value;
                const password = document.getElementById('password').value;
                const errorDiv = document.getElementById('error');
                const successDiv = document.getElementById('success');
                
                try {
                    const response = await fetch('/auth/login', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                        },
                        body: `username=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`
                    });
                    
                    if (response.ok) {
                        const data = await response.json();
                        successDiv.textContent = 'Login successful! Token: ' + data.access_token.substring(0, 20) + '...';
                        errorDiv.textContent = '';
                        
                        // Show API usage instructions
                        setTimeout(() => {
                            successDiv.innerHTML = `
                                <div>
                                    <strong>Login successful!</strong><br><br>
                                    To access the dashboard via API, use:<br>
                                    <code style="background: #f3f4f6; padding: 0.5rem; display: block; margin: 0.5rem 0;">
                                    curl -H "Authorization: Bearer ${data.access_token}" http://localhost:8000/dashboard/agent-status
                                    </code><br>
                                    Or test the enhanced AI agents:<br>
                                    <code style="background: #f3f4f6; padding: 0.5rem; display: block; margin: 0.5rem 0;">
                                    curl -H "Authorization: Bearer ${data.access_token}" http://localhost:8000/dashboard/agent-status
                                    </code>
                                </div>
                            `;
                        }, 1000);
                        
                    } else {
                        const errorData = await response.json();
                        errorDiv.textContent = errorData.detail || 'Login failed';
                        successDiv.textContent = '';
                    }
                } catch (error) {
                    errorDiv.textContent = 'Login failed: ' + error.message;
                    successDiv.textContent = '';
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=login_html)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request, 
    db=Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    # Get recent ledger entries for display
    from sqlalchemy import select
    from ..models import LedgerEntry
    
    recent_entries = db.execute(
        select(LedgerEntry).order_by(LedgerEntry.id.desc()).limit(5)
    ).scalars().all()
    
    # Check user permissions for different features
    can_upload_invoices = current_user.has_permission(UserRole.ORCHESTRATOR)
    can_add_entries = current_user.has_permission(UserRole.ORCHESTRATOR)
    can_view_agents = current_user.has_permission(UserRole.VIEWER)
    
    # Placeholder lists for approvals/exceptions; will be wired later
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "approvals": [],
            "exceptions": [],
            "recent_entries": recent_entries,
            "current_user": {
                "email": current_user.email,
                "full_name": current_user.full_name,
                "role": current_user.role.value
            },
            "permissions": {
                "can_upload_invoices": can_upload_invoices,
                "can_add_entries": can_add_entries,
                "can_view_agents": can_view_agents
            }
        },
    )


@router.post("/dashboard/realworld", response_class=HTMLResponse)
async def realworld_input(
    request: Request,
    description: str = Form(...),
    amount: float = Form(0.0),
    actor: str = Form("Human:orchestrator"),
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check permission for adding entries
    if not current_user.has_permission(UserRole.ORCHESTRATOR):
        raise HTTPException(status_code=403, detail="Orchestrator access required")
    
    append_ledger_entry(db, actor=f"User:{current_user.email}", action="real_world_event", data={"description": description, "amount": amount})
    logger.info(f"Real-world event recorded by {current_user.email}: {description} ({amount} AED)")
    
    # Get updated recent entries
    from sqlalchemy import select
    from ..models import LedgerEntry
    
    recent_entries = db.execute(
        select(LedgerEntry).order_by(LedgerEntry.id.desc()).limit(5)
    ).scalars().all()
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "approvals": [],
            "exceptions": [],
            "recent_entries": recent_entries,
            "current_user": {
                "email": current_user.email,
                "full_name": current_user.full_name,
                "role": current_user.role.value
            },
            "permissions": {
                "can_upload_invoices": current_user.has_permission(UserRole.ORCHESTRATOR),
                "can_add_entries": current_user.has_permission(UserRole.ORCHESTRATOR),
                "can_view_agents": current_user.has_permission(UserRole.VIEWER)
            },
            "message": "Event recorded to ledger.",
        },
    )


@router.post("/dashboard/upload-invoice", response_class=HTMLResponse)
async def upload_invoice(
    request: Request,
    file: UploadFile = File(...),
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check permission for uploading invoices
    if not current_user.has_permission(UserRole.ORCHESTRATOR):
        raise HTTPException(status_code=403, detail="Orchestrator access required")
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")
    
    # Validate file type
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.pdf', '.tiff', '.bmp'}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    try:
        # Save uploaded file to local storage
        storage_dir = Path("local_storage/invoices")
        storage_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = storage_dir / file.filename
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process with OCR
        ocr_data = await ocr_processor.extract_invoice_data(file_path)
        
        # Log to audit trail
        append_ledger_entry(
            db, 
            actor=f"User:{current_user.email}", 
            action="invoice_uploaded",
            data={
                "filename": file.filename,
                "file_size": len(content),
                "ocr_data": ocr_data
            }
        )
        
        logger.info(f"Invoice uploaded and processed by {current_user.email}: {file.filename}")
        
        # Get updated recent entries
        from sqlalchemy import select
        from ..models import LedgerEntry
        
        recent_entries = db.execute(
            select(LedgerEntry).order_by(LedgerEntry.id.desc()).limit(5)
        ).scalars().all()
        
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "approvals": [],
                "exceptions": [],
                "recent_entries": recent_entries,
                "current_user": {
                    "email": current_user.email,
                    "full_name": current_user.full_name,
                    "role": current_user.role.value
                },
                "permissions": {
                    "can_upload_invoices": current_user.has_permission(UserRole.ORCHESTRATOR),
                    "can_add_entries": current_user.has_permission(UserRole.ORCHESTRATOR),
                    "can_view_agents": current_user.has_permission(UserRole.VIEWER)
                },
                "message": f"Invoice uploaded and processed: {ocr_data.get('invoice_number', 'Unknown')}",
                "ocr_data": ocr_data,
            },
        )
    
    except Exception as e:
        logger.error(f"Error processing uploaded invoice: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@router.get("/dashboard/agent-status")
async def agent_status(current_user: User = Depends(get_current_user)):
    """Get enhanced status of all AI agents with detailed capabilities"""
    # Check permission for viewing agents
    if not current_user.has_permission(UserRole.VIEWER):
        raise HTTPException(status_code=403, detail="Viewer access required")
    
    from ..agents.accountant import accountant
    from ..agents.controller import controller
    from ..agents.director import director
    from ..agents.cfo import cfo
    
    # Get detailed status from each AI agent
    return {
        "agents": {
            "accountant": await accountant.get_status(),
            "controller": await controller.get_status(),
            "director": await director.get_status(),
            "cfo": await cfo.get_status(),
        },
        "ai_platform_summary": {
            "total_agents": 4,
            "ai_enhancement_level": "advanced",
            "capabilities": [
                "Machine Learning Transaction Categorization",
                "Intelligent Document Analysis and OCR",
                "Predictive Financial Modeling and Forecasting",
                "Real-time Anomaly Detection and Fraud Prevention",
                "Automated Compliance Monitoring and Risk Assessment",
                "AI-powered Business Intelligence and Insights"
            ]
        }
    }
