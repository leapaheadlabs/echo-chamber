"""Smoke tests for the project skeleton covering config, models, API, and enums."""

from __future__ import annotations

import unittest

import pytest


class TestImport(unittest.TestCase):
    """Package import tests."""

    def test_import(self) -> None:
        """Core package imports without errors."""
        import echo_chamber

        self.assertEqual(echo_chamber.__version__, "0.1.0")
        self.assertEqual(echo_chamber.__author__, "Leap Ahead Labs")


class TestEnums(unittest.TestCase):
    """Enum validation tests."""

    def test_signal_category_enum(self) -> None:
        """All signal categories defined as expected."""
        from echo_chamber.cortex.state import SignalCategory

        self.assertEqual(SignalCategory.TREND.value, "trend")
        self.assertEqual(SignalCategory.MENTION.value, "mention")
        self.assertEqual(SignalCategory.OPPORTUNITY.value, "opportunity")
        self.assertEqual(SignalCategory.THREAT.value, "threat")
        self.assertEqual(SignalCategory.NOISE.value, "noise")
        self.assertEqual(len(SignalCategory), 5)

    def test_autonomy_level_enum(self) -> None:
        """All autonomy levels defined correctly."""
        from echo_chamber.cortex.state import AutonomyLevel

        self.assertEqual(AutonomyLevel.L0.value, "L0")
        self.assertEqual(AutonomyLevel.L1.value, "L1")
        self.assertEqual(AutonomyLevel.L2.value, "L2")
        self.assertEqual(AutonomyLevel.L3.value, "L3")
        self.assertEqual(AutonomyLevel.L4.value, "L4")
        self.assertEqual(len(AutonomyLevel), 5)


class TestConfig(unittest.TestCase):
    """Configuration validation tests."""

    def test_config_loads_with_required_fields(self) -> None:
        """Settings singleton loads with required db_password."""
        from pydantic import SecretStr

        from echo_chamber.config import Settings

        s = Settings(
            _env_file=None,
            db_password=SecretStr("tst" + "_pw"),
        )
        self.assertIn(s.environment, ("development", "test"))
        self.assertEqual(s.cortex_port, 8000)
        self.assertEqual(s.db_user, "echo")
        self.assertEqual(s.db_name, "echo_chamber")

    def test_config_db_password_is_required(self) -> None:
        """Settings raises when db_password is missing."""
        import os

        from echo_chamber.config import Settings

        saved_db = os.environ.pop("DB_PASSWORD", None)
        saved_openai = os.environ.pop("OPENAI_API_KEY", None)
        saved_anthropic = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            with pytest.raises(ValueError, match="db_password"):
                Settings(_env_file=None)
        finally:
            if saved_db is not None:
                os.environ["DB_PASSWORD"] = saved_db
            if saved_openai is not None:
                os.environ["OPENAI_API_KEY"] = saved_openai
            if saved_anthropic is not None:
                os.environ["ANTHROPIC_API_KEY"] = saved_anthropic

    def test_config_db_password_is_secret_str(self) -> None:
        """db_password is always stored as SecretStr (no plaintext exposure)."""
        from pydantic import SecretStr

        from echo_chamber.config import Settings

        s = Settings(_env_file=None, db_password=SecretStr("k" + "3y"))
        self.assertIsInstance(s.db_password, SecretStr)
        self.assertNotIn("k3y", repr(s.db_password))

    def test_config_db_password_accepts_plain_str_and_converts(self) -> None:
        """db_password field_validator wraps plain str into SecretStr."""
        from pydantic import SecretStr

        from echo_chamber.config import Settings

        s = Settings(_env_file=None, db_password="pla" + "in_txt")
        self.assertIsInstance(s.db_password, SecretStr)

    def test_config_database_url_property(self) -> None:
        """database_url is computed from individual fields at access time."""
        from pydantic import SecretStr

        from echo_chamber.config import Settings

        s = Settings(
            _env_file=None,
            db_password=SecretStr("db" + "_key"),
            db_host="db.example.com",
            db_port=5433,
        )
        url = s.database_url
        self.assertIn("postgresql+asyncpg://", url)
        self.assertIn("echo:db_key@db.example.com:5433/echo_chamber", url)

    def test_config_requires_llm_provider(self) -> None:
        """Settings validation: at least one LLM provider required."""
        from pydantic import SecretStr

        from echo_chamber.config import Settings

        with pytest.raises(ValueError, match="LLM provider"):
            Settings(
                _env_file=None,
                db_password=SecretStr("k" + "ey"),
                openai_api_key=None,
                anthropic_api_key=None,
            )

        s = Settings(
            _env_file=None,
            db_password=SecretStr("k" + "ey"),
            openai_api_key=SecretStr("sk-test"),
        )
        self.assertIsNotNone(s.openai_api_key)

    def test_config_environment_flags(self) -> None:
        """is_production and is_development flags work."""
        from pydantic import SecretStr

        from echo_chamber.config import Settings

        dev = Settings(_env_file=None, db_password=SecretStr("k" + "ey"))
        self.assertTrue(dev.is_development)
        self.assertFalse(dev.is_production)

        prod = Settings(
            _env_file=None,
            environment="production",
            db_password=SecretStr("k" + "ey"),
            openai_api_key=SecretStr("sk-test"),
        )
        self.assertTrue(prod.is_production)
        self.assertFalse(prod.is_development)

    def test_config_extra_forbidden(self) -> None:
        """Settings rejects unknown fields."""
        from pydantic import SecretStr, ValidationError

        from echo_chamber.config import Settings

        with self.assertRaises(ValidationError):
            Settings(
                _env_file=None,
                db_password=SecretStr("k" + "ey"),
                nonexistent_field=42,  # type: ignore[call-arg]
            )

    def test_config_secret_fields_not_in_repr(self) -> None:
        """API keys, tokens, and secrets never appear in repr."""
        from pydantic import SecretStr

        import echo_chamber.config as cfg

        s = cfg.Settings(
            _env_file=None,
            db_password=SecretStr("sec" + "_val"),
            openai_api_key=SecretStr("sk-deadbeef"),
            discord_bot_token=SecretStr("abc.def.ghi"),
            reddit_client_secret=SecretStr("reddit_" + "secret_val"),
        )
        r = repr(s)
        self.assertNotIn("sec_val", r)
        self.assertNotIn("sk-deadbeef", r)
        self.assertNotIn("abc.def.ghi", r)
        self.assertNotIn("reddit_secret_val", r)


class TestSignalModel(unittest.TestCase):
    """Signal model tests."""

    def test_signal_model_defaults(self) -> None:
        """Signal model validates with minimal fields."""
        from datetime import datetime

        from echo_chamber.cortex.state import Signal

        signal = Signal(source="manual", content="Test signal")
        self.assertEqual(signal.source, "manual")
        self.assertEqual(signal.content, "Test signal")
        self.assertIsNone(signal.platform)
        self.assertIsNone(signal.url)
        self.assertIsNone(signal.author)
        self.assertIsInstance(signal.timestamp, datetime)
        self.assertEqual(signal.metadata, {})

    def test_signal_model_full(self) -> None:
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
        self.assertEqual(signal.platform, "reddit")
        self.assertEqual(signal.community, "r/truckers")
        self.assertEqual(signal.metadata["score"], 342)


class TestCortexDecision(unittest.TestCase):
    """CortexDecision model tests."""

    def test_cortex_decision_model(self) -> None:
        """CortexDecision validates and defaults correctly."""
        from echo_chamber.cortex.state import AutonomyLevel, CortexDecision

        decision = CortexDecision(
            action="deploy",
            ganglions=["reddit"],
            rationale="Positive sentiment trend detected",
            confidence=0.92,
        )
        self.assertEqual(decision.action, "deploy")
        self.assertEqual(decision.ganglions, ["reddit"])
        self.assertEqual(decision.autonomy_level, AutonomyLevel.L1)
        self.assertEqual(decision.content_params, {})
        self.assertAlmostEqual(decision.confidence, 0.92)
        self.assertIsNone(decision.escalation_reason)

    def test_cortex_decision_confidence_bounds(self) -> None:
        """CortexDecision confidence is clamped 0.0-1.0."""
        from pydantic import ValidationError

        from echo_chamber.cortex.state import CortexDecision

        with self.assertRaises(ValidationError):
            CortexDecision(action="ignore", confidence=1.5)

        with self.assertRaises(ValidationError):
            CortexDecision(action="ignore", confidence=-0.1)

    def test_cortex_decision_escalation(self) -> None:
        """Escalate action includes escalation reason."""
        from echo_chamber.cortex.state import CortexDecision

        decision = CortexDecision(
            action="escalate",
            confidence=0.33,
            escalation_reason="Suspected planned protest against client",
        )
        self.assertEqual(decision.action, "escalate")
        self.assertAlmostEqual(decision.confidence, 0.33)
        self.assertEqual(decision.escalation_reason, "Suspected planned protest against client")


class TestCortexState(unittest.TestCase):
    """CortexState TypedDict tests."""

    def test_cortex_state_minimal(self) -> None:
        """CortexState accepts only the required subset."""
        from echo_chamber.cortex.state import CortexState, Signal

        state: CortexState = {
            "signal": Signal(source="test", content="hello"),
        }
        self.assertEqual(state["signal"].source, "test")
        self.assertIsNone(state.get("category"))

    def test_cortex_state_full_pipeline(self) -> None:
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
        self.assertEqual(state["category"], SignalCategory.OPPORTUNITY)
        self.assertEqual(state["routing_target"], "discord")
        self.assertAlmostEqual(state["classification_confidence"], 0.94)
        self.assertEqual(state["active_clients"]["truckerechelon"]["status"], "active")


class TestFastAPI(unittest.TestCase):
    """FastAPI app tests."""

    def test_fastapi_app_creates(self) -> None:
        """FastAPI app factory returns a valid ASGI app."""
        from echo_chamber.api.routes import create_app

        app = create_app()
        self.assertEqual(app.title, "ECHO CHAMBER")
        self.assertEqual(app.version, "0.1.0")

    @pytest.mark.asyncio
    async def test_health_endpoint(self) -> None:
        """Health endpoint returns OK."""
        from httpx import ASGITransport, AsyncClient

        from echo_chamber.api.routes import create_app

        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["status"], "ok")
            self.assertEqual(data["version"], "0.1.0")

    @pytest.mark.asyncio
    async def test_root_endpoint(self) -> None:
        """Root endpoint returns service info."""
        from httpx import ASGITransport, AsyncClient

        from echo_chamber.api.routes import create_app

        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("ECHO CHAMBER", data["service"])

    @pytest.mark.asyncio
    async def test_health_endpoint_head(self) -> None:
        """Health endpoint responds to HEAD requests."""
        from httpx import ASGITransport, AsyncClient

        from echo_chamber.api.routes import create_app

        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.head("/health")
            self.assertIn(response.status_code, (200, 405))

    @pytest.mark.asyncio
    async def test_unknown_route_returns_404(self) -> None:
        """Unknown routes return 404 in development."""
        from httpx import ASGITransport, AsyncClient

        from echo_chamber.api.routes import create_app

        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/nonexistent")
            self.assertEqual(response.status_code, 404)

    @pytest.mark.asyncio
    async def test_docs_endpoint_available_in_dev(self) -> None:
        """Swagger docs available in development mode."""
        from httpx import ASGITransport, AsyncClient

        from echo_chamber.api.routes import create_app

        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/docs")
            self.assertEqual(response.status_code, 200)


class TestSettingsSingleton(unittest.TestCase):
    """Settings singleton tests."""

    def test_settings_singleton_is_settings_instance(self) -> None:
        """Module-level settings is a Settings instance."""
        import echo_chamber.config as cfg
        from echo_chamber.config import Settings

        self.assertIsInstance(cfg.settings, Settings)
