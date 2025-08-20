from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Form, Request, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from ..db import get_db
from ..models import append_ledger_entry
from ..utils.ocr import ocr_processor
from ..logging_config import get_logger

logger = get_logger("dashboard")

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def root_redirect():
    return RedirectResponse(url="/dashboard")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, db=Depends(get_db)) -> Any:
    # Get recent ledger entries for display
    from sqlalchemy import select
    from ..models import LedgerEntry
    
    recent_entries = db.execute(
        select(LedgerEntry).order_by(LedgerEntry.id.desc()).limit(5)
    ).scalars().all()
    
    # Placeholder lists for approvals/exceptions; will be wired later
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "approvals": [],
            "exceptions": [],
            "recent_entries": recent_entries,
        },
    )


@router.post("/dashboard/realworld", response_class=HTMLResponse)
async def realworld_input(
    request: Request,
    description: str = Form(...),
    amount: float = Form(0.0),
    actor: str = Form("Human:orchestrator"),
    db=Depends(get_db),
):
    append_ledger_entry(db, actor=actor, action="real_world_event", data={"description": description, "amount": amount})
    logger.info(f"Real-world event recorded: {description} ({amount} AED)")
    
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
            "message": "Event recorded to ledger.",
        },
    )


@router.post("/dashboard/upload-invoice", response_class=HTMLResponse)
async def upload_invoice(
    request: Request,
    file: UploadFile = File(...),
    db=Depends(get_db),
):
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
            actor="Human:orchestrator", 
            action="invoice_uploaded",
            data={
                "filename": file.filename,
                "file_size": len(content),
                "ocr_data": ocr_data
            }
        )
        
        logger.info(f"Invoice uploaded and processed: {file.filename}")
        
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
                "message": f"Invoice uploaded and processed: {ocr_data.get('invoice_number', 'Unknown')}",
                "ocr_data": ocr_data,
            },
        )
    
    except Exception as e:
        logger.error(f"Error processing uploaded invoice: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@router.get("/dashboard/agent-status")
async def agent_status():
    """Get status of all AI agents"""
    from ..agents.accountant import accountant
    from ..agents.controller import controller
    from ..agents.director import director
    from ..agents.cfo import cfo
    
    return {
        "agents": {
            "accountant": {"name": accountant.name, "status": "ready"},
            "controller": {"name": controller.name, "status": "ready"},
            "director": {"name": director.name, "status": "ready"},
            "cfo": {"name": cfo.name, "status": "ready"},
        }
    }
