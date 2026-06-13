"""FastAPI application factory and route definitions."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from structlog import get_logger

from echo_chamber.config import settings

logger = get_logger(__name__)


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title="ECHO CHAMBER",
        description="AI Agent Marketing Amplification Engine - Cortex API",
        version="0.1.0",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
    )

    allowed_origins = (
        ["http://localhost:3000", "http://localhost:8000"] if settings.is_development else []
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _register_routes(app)

    return app


def _register_routes(app: FastAPI) -> None:
    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": "0.1.0"}

    @app.get("/")
    async def root() -> dict[str, str]:
        return {
            "service": "ECHO CHAMBER - Cortex",
            "version": "0.1.0",
            "docs": "/docs",
        }

    @app.middleware("http")
    async def request_logging_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        start = time.monotonic()
        response = await call_next(request)
        duration_ms = (time.monotonic() - start) * 1000

        logger.info(
            "request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round(duration_ms, 2),
        )

        return response


app = create_app()
