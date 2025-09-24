from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from .db import init_db
from .routers import health, dashboard, auth, settings, agents, admin_dashboard, zoho_sync
from .logging_config import setup_logging, get_logger
from .utils.error_handling import (
    validation_exception_handler,
    cmp_exception_handler,
    general_exception_handler,
    CMPException
)
from .utils.monitoring import setup_monitoring_middleware, system_health_monitor, contextual_logger
from .utils.zoho_scheduler import zoho_scheduler

logger = get_logger("main")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Company Management Platform (CMP)", 
        version="0.1.0",
        description="Financial management platform with OCR, banking integration, and role-based access control"
    )

    # Add monitoring middleware (must be first to capture all requests)
    setup_monitoring_middleware(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add custom exception handlers
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(CMPException, cmp_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    # Routers
    app.include_router(health.router)
    app.include_router(auth.router)  # Authentication endpoints
    app.include_router(dashboard.router)  # Protected dashboard endpoints
    app.include_router(settings.router)  # Settings and configuration management
    app.include_router(agents.router)  # AI Agents control panels and interactions
    app.include_router(admin_dashboard.router)  # Enhanced admin dashboard with CEO chat
    app.include_router(zoho_sync.router)  # Zoho Books synchronization management

    @app.on_event("startup")
    def _startup():
        setup_logging()
        logger.info("CMP application starting up...")
        
        # Initialize database
        init_db()
        logger.info("Database initialized successfully")
        
        # Start Zoho sync scheduler (5 minute intervals)
        try:
            zoho_scheduler.start_scheduler(sync_interval_seconds=300)
            logger.info("Zoho sync scheduler started successfully")
        except Exception as e:
            logger.error(f"Failed to start Zoho sync scheduler: {e}")
        
        # Log system startup
        contextual_logger.info("Enhanced error handling system activated")
        contextual_logger.info("Performance monitoring system activated")
        contextual_logger.info("System health monitoring initialized")
        
        logger.info("CMP application startup completed successfully")

    return app


app = create_app()
