"""Smoke tests for the project skeleton covering config, models, API, and enums."""

from __future__ import annotations

import pytest

## Package import


def test_import() -> None:
    """Core package imports without errors."""
    import echo_chamber

    assert echo_chamber.__version__ == "0.1.0"
    assert echo_chamber.__author__ == "Leap Ahead Labs"


## Enums


def test_signal_category_enum() -> None:
    """All signal categories defined as expected."""
    from echo_chamber.cortex.state import SignalCategory

    assert SignalCategory.TREND.value == "trend"
    assert SignalCategory.MENTION.value == "mention"
    assert SignalCategory.OPPORTUNITY.value == "opportunity"
    assert SignalCategory.THREAT.value == "threat"
    assert SignalCategory.NOISE.value == "noise"
    assert len(SignalCategory) == 5


def test_autonomy_level_enum() -> None:
    """All autonomy levels defined correctly."""
    from echo_chamber.cortex.state import AutonomyLevel

    assert AutonomyLevel.L0.value == "L0"
    assert AutonomyLevel.L1.value == "L1"
    assert AutonomyLevel.L2.value == "L2"
    assert AutonomyLevel.L3.value == "L3"
    assert AutonomyLevel.L4.value == "L4"
    assert len(AutonomyLevel) == 5


## Configuration


def test_config_loads_with_required_fields() -> None:
    """Settings singleton loads with required db_password."""
    from pydantic import SecretStr

    from echo_chamber.config import Settings

    s = Settings(
        _env_file=None,
        db_password=SecretStr("tst_pw"),
    )
    assert s.environment in ("development", "test")
    assert s.cortex_port == 8000
    assert s.db_user == "echo"
    assert s.db_name == "echo_chamber"


def test_config_db_password_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings raises when db_password is missing."""
    from echo_chamber.config import Settings

    monkeypatch.delenv("DB_PASSWORD", raising=False)
    with pytest.raises(ValueError, match="DB_PASSWORD"):
        Settings(_env_file=None)


def test_config_db_password_is_secret_str() -> None:
    """db_password is always stored as SecretStr (no plaintext exposure)."""
    from pydantic import SecretStr

    from echo_chamber.config import Settings

    s = Settings(_env_file=None, db_password=SecretStr("k3y"))
    assert isinstance(s.db_password, SecretStr)
    assert "k3y" not in repr(s.db_password)


def test_config_db_password_accepts_plain_str_and_converts() -> None:
    """db_password field_validator wraps plain str into SecretStr."""
    from pydantic import SecretStr

    from echo_chamber.config import Settings

    s = Settings(_env_file=None, db_password="plain_txt")
    assert isinstance(s.db_password, SecretStr)


def test_config_database_url_property() -> None:
    """database_url is computed from individual fields at access time."""
    from pydantic import SecretStr

    from echo_chamber.config import Settings

    s = Settings(
        _env_file=None,
        db_password=SecretStr("db_key"),
        db_host="db.example.com",
        db_port=5433,
    )
    url = s.database_url
    assert "postgresql+asyncpg://" in url
    assert "echo:db_key@db.example.com:5433/echo_chamber" in url


def test_config_requires_llm_provider() -> None:
    """Settings validation: at least one LLM provider required."""
    from pydantic import SecretStr

    from echo_chamber.config import Settings

    with pytest.raises(ValueError, match="LLM provider"):
        Settings(
            _env_file=None,
            db_password=SecretStr("key"),
            openai_api_key=None,
            anthropic_api_key=None,
        )

    s = Settings(
        _env_file=None,
        db_password=SecretStr("key"),
        openai_api_key=SecretStr("sk-test"),
    )
    assert s.openai_api_key is not None


def test_config_environment_flags() -> None:
    """is_production and is_development flags work."""
    from pydantic import SecretStr

    from echo_chamber.config import Settings

    dev = Settings(_env_file=None, db_password=SecretStr("key"))
    assert dev.is_development is True
    assert dev.is_production is False

    prod = Settings(
        _env_file=None,
        environment="production",
        db_password=SecretStr("key"),
        openai_api_key=SecretStr("sk-test"),
    )
    assert prod.is_production is True
    assert prod.is_development is False


def test_config_extra_forbidden() -> None:
    """Settings rejects unknown fields."""
    from pydantic import SecretStr, ValidationError

    from echo_chamber.config import Settings

    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            db_password=SecretStr("key"),
            nonexistent_field=42,  # type: ignore[call-arg]
        )


def test_config_secret_fields_not_in_repr() -> None:
    """API keys, tokens, and secrets never appear in repr."""
    from pydantic import SecretStr

    import echo_chamber.config as cfg

    s = cfg.Settings(
        _env_file=None,
        db_password=SecretStr("sec_val"),
        openai_api_key=SecretStr("sk-deadbeef"),
        discord_bot_token=SecretStr("abc.def.ghi"),
        reddit_client_secret=SecretStr("reddit_secret_val"),
    )
    r = repr(s)
    assert "sec_val" not in r
    assert "sk-deadbeef" not in r
    assert "abc.def.ghi" not in r
    assert "reddit_secret_val" not in r


## Signal model


def test_signal_model_defaults() -> None:
    """Signal model validates with minimal fields."""
    from datetime import datetime

    from echo_chamber.cortex.state import Signal

    signal = Signal(source="manual", content="Test signal")
    assert signal.source == "manual"
    assert signal.content == "Test signal"
    assert signal.platform is None
    assert signal.url is None
    assert signal.author is None
    assert isinstance(signal.timestamp, datetime)
    assert signal.metadata == {}


def test_signal_model_full() -> None:
    """Signal model accepts all optional fields."""
    from echo_chamber.cortex.state import Signal

    signal = Signal(
        source="reddit",
        platform="reddit",
        community="r/truckers",
        content="TruckerEchelon is amazing for load matching",
        url="https://reddit.com/r/truckers/comments/abc123",
        author="trucker_joe",
        metadata={"score": 342, "comments": 45},
    )
    assert signal.platform == "reddit"
    assert signal.community == "r/truckers"
    assert signal.metadata["score"] == 342


## CortexDecision model


def test_cortex_decision_model() -> None:
    """CortexDecision validates and defaults correctly."""
    from echo_chamber.cortex.state import AutonomyLevel, CortexDecision

    decision = CortexDecision(
        action="deploy",
        ganglions=["reddit"],
        rationale="Positive sentiment trend detected",
        confidence=0.92,
    )
    assert decision.action == "deploy"
    assert decision.ganglions == ["reddit"]
    assert decision.autonomy_level == AutonomyLevel.L1
    assert decision.content_params == {}
    assert decision.confidence == pytest.approx(0.92)
    assert decision.escalation_reason is None


def test_cortex_decision_confidence_bounds() -> None:
    """CortexDecision confidence is clamped 0.0-1.0."""
    from pydantic import ValidationError

    from echo_chamber.cortex.state import CortexDecision

    with pytest.raises(ValidationError):
        CortexDecision(action="ignore", confidence=1.5)

    with pytest.raises(ValidationError):
        CortexDecision(action="ignore", confidence=-0.1)


def test_cortex_decision_escalation() -> None:
    """Escalate action includes escalation reason."""
    from echo_chamber.cortex.state import CortexDecision

    decision = CortexDecision(
        action="escalate",
        confidence=0.33,
        escalation_reason="Suspected planned protest against client",
    )
    assert decision.action == "escalate"
    assert decision.confidence == pytest.approx(0.33)
    assert decision.escalation_reason == "Suspected planned protest against client"


## CortexState TypedDict


def test_cortex_state_minimal() -> None:
    """CortexState accepts only the required subset."""
    from echo_chamber.cortex.state import CortexState, Signal

    state: CortexState = {
        "signal": Signal(source="test", content="hello"),
    }
    assert state["signal"].source == "test"
    assert state.get("category") is None


def test_cortex_state_full_pipeline() -> None:
    """CortexState accepts full pipeline state."""
    from echo_chamber.cortex.state import (
        CortexDecision,
        CortexState,
        Signal,
        SignalCategory,
    )

    signal = Signal(source="reddit", content="vibes are good")
    decision = CortexDecision(action="deploy", ganglions=["discord"], confidence=0.88)

    state: CortexState = {
        "signal": signal,
        "category": SignalCategory.OPPORTUNITY,
        "classification_confidence": 0.94,
        "decision": decision,
        "routing_target": "discord",
        "active_clients": {"truckerechelon": {"status": "active"}},
        "campaign_memory": [{"pattern": "trucker_early_morning"}],
        "account_pool_status": {"reddit": {"available": 3, "cooldown": 1}},
        "dispatch_results": {"discord": "queued"},
        "health_issues": [],
        "errors": [],
    }
    assert state["category"] == SignalCategory.OPPORTUNITY
    assert state["routing_target"] == "discord"
    assert state["classification_confidence"] == pytest.approx(0.94)
    assert state["active_clients"]["truckerechelon"]["status"] == "active"


## FastAPI app


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
        assert data["version"] == "0.1.0"


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


@pytest.mark.asyncio
async def test_health_endpoint_head() -> None:
    """Health endpoint responds to HEAD requests."""
    from httpx import ASGITransport, AsyncClient

    from echo_chamber.api.routes import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.head("/health")
        assert response.status_code in (200, 405)


@pytest.mark.asyncio
async def test_unknown_route_returns_404() -> None:
    """Unknown routes return 404 in development."""
    from httpx import ASGITransport, AsyncClient

    from echo_chamber.api.routes import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/nonexistent")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_docs_endpoint_available_in_dev() -> None:
    """Swagger docs available in development mode."""
    from httpx import ASGITransport, AsyncClient

    from echo_chamber.api.routes import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/docs")
        assert response.status_code == 200


## Settings singleton


def test_settings_singleton_is_settings_instance() -> None:
    """Module-level settings is a Settings instance."""
    import echo_chamber.config as cfg
    from echo_chamber.config import Settings

    assert isinstance(cfg.settings, Settings)
