"""Comprehensive tests for Cortex graph — all code paths."""

from __future__ import annotations

import unittest


class TestSignalIngestAllPaths(unittest.TestCase):
    """All code paths in signal_ingest."""

    def test_ingest_dict_to_signal(self) -> None:
        from echo_chamber.cortex.graph import signal_ingest

        result = signal_ingest({"signal": {"source": "reddit", "content": "test"}})  # type: ignore[typeddict-item]
        self.assertEqual(result["signal"].source, "reddit")

    def test_ingest_signal_model_passthrough(self) -> None:
        from echo_chamber.cortex.graph import signal_ingest
        from echo_chamber.cortex.state import Signal

        sig = Signal(source="rss", content="hello", platform="reddit", community="r/test")
        result = signal_ingest({"signal": sig})
        self.assertEqual(result["signal"].platform, "reddit")

    def test_ingest_none_signal(self) -> None:
        from echo_chamber.cortex.graph import signal_ingest

        result = signal_ingest({})
        self.assertIn("errors", result)
        self.assertIn("no signal", result["errors"][0])

    def test_ingest_invalid_dict(self) -> None:
        from echo_chamber.cortex.graph import signal_ingest

        result = signal_ingest({"signal": {"bad_field": True}})  # type: ignore[typeddict-item]
        self.assertIn("errors", result)
        self.assertIn("invalid signal", result["errors"][0])

    def test_ingest_unexpected_type(self) -> None:
        from echo_chamber.cortex.graph import signal_ingest

        result = signal_ingest({"signal": 12345})  # type: ignore[typeddict-item]
        self.assertIn("errors", result)
        self.assertIn("unexpected signal type", result["errors"][0])

    def test_ingest_with_all_optional_fields(self) -> None:
        from echo_chamber.cortex.graph import signal_ingest

        result = signal_ingest(  # type: ignore[typeddict-item]
            {
                "signal": {
                    "source": "manual",
                    "content": "test",
                    "platform": "discord",
                    "community": "general",
                    "url": "https://example.com",
                    "author": "user1",
                    "metadata": {"key": "val"},
                }
            }
        )
        self.assertEqual(result["signal"].author, "user1")


class TestSignalClassifyAllPaths(unittest.TestCase):
    """All code paths in signal_classify."""

    def test_classify_threat_ban(self) -> None:
        from echo_chamber.cortex.graph import signal_classify
        from echo_chamber.cortex.state import Signal, SignalCategory

        result = signal_classify({"signal": Signal(source="t", content="account ban incoming")})
        self.assertEqual(result["category"], SignalCategory.THREAT)

    def test_classify_threat_lawsuit(self) -> None:
        from echo_chamber.cortex.graph import signal_classify
        from echo_chamber.cortex.state import Signal, SignalCategory

        result = signal_classify({"signal": Signal(source="t", content="lawsuit filed")})
        self.assertEqual(result["category"], SignalCategory.THREAT)

    def test_classify_threat_crisis(self) -> None:
        from echo_chamber.cortex.graph import signal_classify
        from echo_chamber.cortex.state import Signal, SignalCategory

        result = signal_classify({"signal": Signal(source="t", content="pr crisis unfolding")})
        self.assertEqual(result["category"], SignalCategory.THREAT)

    def test_classify_trend_trending(self) -> None:
        from echo_chamber.cortex.graph import signal_classify
        from echo_chamber.cortex.state import Signal, SignalCategory

        result = signal_classify({"signal": Signal(source="t", content="this is trending now")})
        self.assertEqual(result["category"], SignalCategory.TREND)

    def test_classify_trend_viral(self) -> None:
        from echo_chamber.cortex.graph import signal_classify
        from echo_chamber.cortex.state import Signal, SignalCategory

        result = signal_classify({"signal": Signal(source="t", content="going viral on reddit")})
        self.assertEqual(result["category"], SignalCategory.TREND)

    def test_classify_trend_surge(self) -> None:
        from echo_chamber.cortex.graph import signal_classify
        from echo_chamber.cortex.state import Signal, SignalCategory

        result = signal_classify({"signal": Signal(source="t", content="surge in interest")})
        self.assertEqual(result["category"], SignalCategory.TREND)

    def test_classify_mention(self) -> None:
        from echo_chamber.cortex.graph import signal_classify
        from echo_chamber.cortex.state import Signal, SignalCategory

        result = signal_classify(
            {"signal": Signal(source="t", content="people said about the product")}
        )
        self.assertEqual(result["category"], SignalCategory.MENTION)

    def test_classify_mention_talking(self) -> None:
        from echo_chamber.cortex.graph import signal_classify
        from echo_chamber.cortex.state import Signal, SignalCategory

        result = signal_classify({"signal": Signal(source="t", content="talking about truckers")})
        self.assertEqual(result["category"], SignalCategory.MENTION)

    def test_classify_opportunity(self) -> None:
        from echo_chamber.cortex.graph import signal_classify
        from echo_chamber.cortex.state import Signal, SignalCategory

        result = signal_classify(
            {"signal": Signal(source="t", content="big opportunity in market")}
        )
        self.assertEqual(result["category"], SignalCategory.OPPORTUNITY)

    def test_classify_opportunity_gap(self) -> None:
        from echo_chamber.cortex.graph import signal_classify
        from echo_chamber.cortex.state import Signal, SignalCategory

        result = signal_classify({"signal": Signal(source="t", content="gap in coverage")})
        self.assertEqual(result["category"], SignalCategory.OPPORTUNITY)

    def test_classify_noise(self) -> None:
        from echo_chamber.cortex.graph import signal_classify
        from echo_chamber.cortex.state import Signal, SignalCategory

        result = signal_classify({"signal": Signal(source="t", content="random stuff")})
        self.assertEqual(result["category"], SignalCategory.NOISE)
        self.assertEqual(result["classification_confidence"], 0.5)

    def test_classify_no_signal(self) -> None:
        from echo_chamber.cortex.graph import signal_classify

        result = signal_classify({})
        self.assertIn("errors", result)


class TestSignalRouteAllPaths(unittest.TestCase):
    """All code paths in signal_route."""

    def test_route_noise(self) -> None:
        from echo_chamber.cortex.graph import signal_route
        from echo_chamber.cortex.state import SignalCategory

        self.assertEqual(
            signal_route({"category": SignalCategory.NOISE, "classification_confidence": 0.5}),
            "end",
        )

    def test_route_threat(self) -> None:
        from echo_chamber.cortex.graph import signal_route
        from echo_chamber.cortex.state import SignalCategory

        self.assertEqual(
            signal_route({"category": SignalCategory.THREAT, "classification_confidence": 0.8}),
            "escalate",
        )

    def test_route_low_confidence(self) -> None:
        from echo_chamber.cortex.graph import signal_route
        from echo_chamber.cortex.state import SignalCategory

        self.assertEqual(
            signal_route({"category": SignalCategory.TREND, "classification_confidence": 0.3}),
            "escalate",
        )

    def test_route_high_confidence_trend(self) -> None:
        from echo_chamber.cortex.graph import signal_route
        from echo_chamber.cortex.state import SignalCategory

        self.assertEqual(
            signal_route({"category": SignalCategory.TREND, "classification_confidence": 0.9}),
            "decide",
        )

    def test_route_no_category(self) -> None:
        from echo_chamber.cortex.graph import signal_route

        # No category, no confidence → confidence defaults to 0.0 → escalate
        self.assertEqual(signal_route({}), "escalate")

    def test_route_no_confidence(self) -> None:
        from echo_chamber.cortex.graph import signal_route
        from echo_chamber.cortex.state import SignalCategory

        self.assertEqual(signal_route({"category": SignalCategory.TREND}), "escalate")


class TestCortexDecideAllPaths(unittest.TestCase):
    """All code paths in cortex_decide."""

    def test_decide_trend(self) -> None:
        from echo_chamber.cortex.graph import cortex_decide
        from echo_chamber.cortex.state import Signal, SignalCategory

        result = cortex_decide(
            {
                "signal": Signal(source="t", content="trending"),
                "category": SignalCategory.TREND,
                "classification_confidence": 0.8,
            }
        )
        self.assertEqual(result["decision"].action, "deploy")
        self.assertEqual(result["routing_target"], "dispatch")

    def test_decide_opportunity(self) -> None:
        from echo_chamber.cortex.graph import cortex_decide
        from echo_chamber.cortex.state import Signal, SignalCategory

        result = cortex_decide(
            {
                "signal": Signal(source="t", content="opportunity"),
                "category": SignalCategory.OPPORTUNITY,
                "classification_confidence": 0.7,
            }
        )
        self.assertEqual(result["decision"].action, "deploy")

    def test_decide_mention(self) -> None:
        from echo_chamber.cortex.graph import cortex_decide
        from echo_chamber.cortex.state import Signal, SignalCategory

        result = cortex_decide(
            {
                "signal": Signal(source="t", content="mention"),
                "category": SignalCategory.MENTION,
                "classification_confidence": 0.7,
            }
        )
        self.assertEqual(result["decision"].action, "deploy")

    def test_decide_threat_escalates(self) -> None:
        from echo_chamber.cortex.graph import cortex_decide
        from echo_chamber.cortex.state import Signal, SignalCategory

        result = cortex_decide(
            {
                "signal": Signal(source="t", content="threat"),
                "category": SignalCategory.THREAT,
                "classification_confidence": 0.8,
            }
        )
        self.assertEqual(result["decision"].action, "escalate")
        self.assertEqual(result["routing_target"], "escalate")

    def test_decide_noise_escalates(self) -> None:
        from echo_chamber.cortex.graph import cortex_decide
        from echo_chamber.cortex.state import Signal, SignalCategory

        result = cortex_decide(
            {
                "signal": Signal(source="t", content="noise"),
                "category": SignalCategory.NOISE,
                "classification_confidence": 0.5,
            }
        )
        self.assertEqual(result["decision"].action, "escalate")

    def test_decide_missing_signal(self) -> None:
        from echo_chamber.cortex.graph import cortex_decide

        result = cortex_decide({})
        self.assertEqual(result["decision"].action, "escalate")
        self.assertIn("Incomplete state", result["decision"].escalation_reason)

    def test_decide_missing_category(self) -> None:
        from echo_chamber.cortex.graph import cortex_decide
        from echo_chamber.cortex.state import Signal

        result = cortex_decide({"signal": Signal(source="t", content="test")})
        self.assertEqual(result["decision"].action, "escalate")


class TestDispatchAllPaths(unittest.TestCase):
    """All code paths in dispatch."""

    def test_dispatch_with_decision(self) -> None:
        from echo_chamber.cortex.graph import dispatch
        from echo_chamber.cortex.state import AutonomyLevel, CortexDecision, CortexState

        state: CortexState = {
            "decision": CortexDecision(
                action="deploy",
                ganglions=["reddit"],
                autonomy_level=AutonomyLevel.L3,
                confidence=0.9,
            )
        }
        result = dispatch(state)
        self.assertIn("dispatch_results", result)
        self.assertEqual(len(result["dispatch_results"]), 1)
        key = next(iter(result["dispatch_results"].keys()))
        self.assertEqual(result["dispatch_results"][key]["status"], "dispatched")

    def test_dispatch_no_decision(self) -> None:
        from echo_chamber.cortex.graph import dispatch

        result = dispatch({})
        self.assertIn("errors", result)


class TestEscalateAllPaths(unittest.TestCase):
    """All code paths in escalate."""

    def test_escalate_with_decision_and_signal(self) -> None:
        from echo_chamber.cortex.graph import escalate
        from echo_chamber.cortex.state import CortexDecision, Signal, SignalCategory

        result = escalate(
            {
                "signal": Signal(source="t", content="bad"),
                "category": SignalCategory.THREAT,
                "decision": CortexDecision(
                    action="escalate", confidence=0.8, escalation_reason="Threat"
                ),
            }
        )
        self.assertIn("ESCALATION", result["errors"][0])

    def test_escalate_without_decision(self) -> None:
        from echo_chamber.cortex.graph import escalate
        from echo_chamber.cortex.state import Signal, SignalCategory

        result = escalate(
            {
                "signal": Signal(source="t", content="bad"),
                "category": SignalCategory.THREAT,
            }
        )
        self.assertIn("ESCALATION", result["errors"][0])
        self.assertIn("Unknown escalation", result["errors"][0])

    def test_escalate_without_signal(self) -> None:
        from echo_chamber.cortex.graph import escalate
        from echo_chamber.cortex.state import CortexDecision, SignalCategory

        result = escalate(
            {
                "category": SignalCategory.THREAT,
                "decision": CortexDecision(
                    action="escalate", confidence=0.8, escalation_reason="Threat"
                ),
            }
        )
        self.assertIn("ESCALATION", result["errors"][0])

    def test_escalate_empty_state(self) -> None:
        from echo_chamber.cortex.graph import escalate

        result = escalate({})
        self.assertIn("ESCALATION", result["errors"][0])


class TestLearnAllPaths(unittest.TestCase):
    """All code paths in learn."""

    def test_learn_with_dispatches(self) -> None:
        from echo_chamber.cortex.graph import learn

        result = learn({"dispatch_results": {"a": {}, "b": {}}})
        self.assertEqual(result, {})

    def test_learn_empty(self) -> None:
        from echo_chamber.cortex.graph import learn

        result = learn({})
        self.assertEqual(result, {})


class TestHealthCheckAllPaths(unittest.TestCase):
    """All code paths in health_check."""

    def test_health_check(self) -> None:
        from echo_chamber.cortex.graph import health_check

        result = health_check({})
        self.assertEqual(result["health_issues"], [])


class TestBuildGraphAllPaths(unittest.TestCase):
    """Graph construction and route_decision inner function."""

    def test_graph_compiles(self) -> None:
        from echo_chamber.cortex.graph import build_cortex_graph

        graph = build_cortex_graph()
        self.assertIsNotNone(graph)

    def test_route_decision_dispatch(self) -> None:
        from echo_chamber.cortex.graph import build_cortex_graph

        graph = build_cortex_graph()
        result = graph.invoke({"signal": {"source": "t", "content": "trending stuff"}})
        self.assertIn("dispatch_results", result)

    def test_route_decision_escalate(self) -> None:
        from echo_chamber.cortex.graph import build_cortex_graph

        graph = build_cortex_graph()
        result = graph.invoke({"signal": {"source": "t", "content": "threat incoming"}})
        self.assertIn("errors", result)
