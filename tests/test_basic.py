"""Basic smoke tests for the project skeleton."""

from __future__ import annotations

import pytest


def test_import() -> None:
    """Core package imports without errors."""
    import echo_chamber

    assert echo_chamber.__version__ == "0.1.0"


def test_config_loads() -> None:
    """Settings singleton loads with defaults (test mode)."""
    from echo_chamber.config import Settings

    settings = Settings(_env_file=None)  # Don't read real .env
    assert settings.environment == "development"  # default; see conftest autouse
    assert settings.cortex_port == 8000


def test_config_requires_llm_provider() -> None:
    """Settings validation: at least one LLM provider required."""
    from pydantic import SecretStr

    from echo_chamber.config import Settings

    # Neither provider → should raise
    with pytest.raises(ValueError, match="LLM provider"):
        Settings(
            _env_file=None,
            openai_api_key=None,
            anthropic_api_key=None,
        )

    # At least one → OK
    settings = Settings(
        _env_file=None,
        openai_api_key=SecretStr("sk-test"),
    )
    assert settings.openai_api_key is not None


def test_signal_model() -> None:
    """Signal model validates correctly."""
    from echo_chamber.cortex.state import Signal

    signal = Signal(source="manual", content="Test signal")
    assert signal.source == "manual"
    assert signal.category is None  # Not yet classified


def test_fastapi_app_creates() -> None:
    """FastAPI app factory returns a valid ASGI app."""
    from echo_chamber.api.routes import create_app

    app = create_app()
    assert app.title == "ECHO CHAMBER"
    assert app.version == "0.1.0"


@pytest.mark.asyncio
async def test_health_endpoint() -> None:
    """Health endpoint returns OK."""
    from httpx import ASGITransport, AsyncClient

    from echo_chamber.api.routes import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_root_endpoint() -> None:
    """Root endpoint returns service info."""
    from httpx import ASGITransport, AsyncClient

    from echo_chamber.api.routes import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "ECHO CHAMBER" in data["service"]
