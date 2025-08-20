from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import init_db
from .routers import health, dashboard


def create_app() -> FastAPI:
    app = FastAPI(title="Company Management Platform (CMP)", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(health.router)
    app.include_router(dashboard.router)

    @app.on_event("startup")
    def _startup():
        init_db()

    return app


app = create_app()
