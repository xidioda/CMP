from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import init_db
from .routers import health, dashboard, auth
from .logging_config import setup_logging, get_logger

logger = get_logger("main")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Company Management Platform (CMP)", 
        version="0.1.0",
        description="Financial management platform with OCR, banking integration, and role-based access control"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(health.router)
    app.include_router(auth.router)  # Authentication endpoints
    app.include_router(dashboard.router)  # Protected dashboard endpoints

    @app.on_event("startup")
    def _startup():
        setup_logging()
        logger.info("CMP application starting up...")
        init_db()
        logger.info("Database initialized successfully")

    return app


app = create_app()
