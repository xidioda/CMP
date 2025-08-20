from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from ..db import get_db
from ..models import append_ledger_entry

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def root_redirect():
    return RedirectResponse(url="/dashboard")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request) -> Any:
    # Placeholder lists for approvals/exceptions; will be wired later
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "approvals": [],
            "exceptions": [],
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
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "approvals": [],
            "exceptions": [],
            "message": "Event recorded to ledger.",
        },
    )
