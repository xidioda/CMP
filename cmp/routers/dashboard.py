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
    """Serve the enhanced AI login page for browser access"""
    return templates.TemplateResponse(request, "login.html")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request) -> Any:
    """Serve the dashboard page - authentication handled by JavaScript"""
    return templates.TemplateResponse(
        "dashboard_dynamic.html",
        {"request": request}
    )


@router.get("/dashboard/data")
async def dashboard_data(
    db=Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get dashboard data with authentication"""
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
    
    return {
        "approvals": [],
        "exceptions": [],
        "recent_entries": [
            {
                "id": entry.id,
                "actor": entry.actor,
                "action": entry.action,
                "timestamp": entry.timestamp.isoformat(),
                "data": entry.data
            } for entry in recent_entries
        ],
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
    }


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
