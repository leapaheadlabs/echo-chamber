"""FastAPI application factory and route definitions."""

from __future__ import annotations

import time
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from structlog import get_logger

from echo_chamber.config import settings

logger = get_logger(__name__)


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title="ECHO CHAMBER",
        description="AI Agent Marketing Amplification Engine — Cortex API",
        version="0.1.0",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
    )

    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    _register_routes(app)

    return app


def _register_routes(app: FastAPI) -> None:
    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": "0.1.0"}

    @app.get("/")
    async def root() -> dict[str, str]:
        return {
            "service": "ECHO CHAMBER — Cortex",
            "version": "0.1.0",
            "docs": "/docs",
        }

    @app.middleware("http")
    async def request_logging_middleware(
        request: Request,
        call_next: AsyncGenerator,  # type: ignore[type-arg]
    ) -> JSONResponse:
        start = time.monotonic()
        response = await call_next(request)  # type: ignore[arg-type]
        duration_ms = (time.monotonic() - start) * 1000

        logger.info(
            "request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round(duration_ms, 2),
        )

        return response  # type: ignore[return-value]

    # ── Add more routes as the project grows ────────────────────────
    # @app.post("/signal")
    # async def ingest_signal(signal: Signal) -> CortexDecision: ...
    #
    # @app.post("/onboard")
    # async def onboard_client(url: str) -> ClientProfile: ...


app = create_app()
