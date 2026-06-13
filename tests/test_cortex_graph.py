"""Tests for Cortex StateGraph — TASK-006."""

from __future__ import annotations

import unittest


class TestCortexGraph(unittest.TestCase):
    """Cortex StateGraph construction and invocation tests."""

    def test_build_cortex_graph_compiles(self) -> None:
        """Graph builds without error."""
        from echo_chamber.cortex.graph import build_cortex_graph

        graph = build_cortex_graph()
        self.assertIsNotNone(graph)

    def test_signal_ingest_normalizes_dict(self) -> None:
        """signal_ingest converts dict to Signal model."""
        from echo_chamber.cortex.graph import signal_ingest
        from echo_chamber.cortex.state import CortexState

        state: CortexState = {"signal": {"source": "manual", "content": "test signal"}}  # type: ignore[typeddict-item]
        result = signal_ingest(state)
        self.assertIn("signal", result)
        self.assertEqual(result["signal"].source, "manual")
        self.assertEqual(result["signal"].content, "test signal")

    def test_signal_ingest_passes_signal_model(self) -> None:
        """signal_ingest passes through Signal model unchanged."""
        from echo_chamber.cortex.graph import signal_ingest
        from echo_chamber.cortex.state import CortexState, Signal

        signal = Signal(source="reddit", content="hello")
        state: CortexState = {"signal": signal}
        result = signal_ingest(state)
        self.assertEqual(result["signal"].source, "reddit")

    def test_signal_ingest_handles_missing_signal(self) -> None:
        """signal_ingest returns error when signal is missing."""
        from echo_chamber.cortex.graph import signal_ingest

        result = signal_ingest({})  # type: ignore[arg-type]
        self.assertIn("errors", result)

    def test_signal_classify_threat(self) -> None:
        """Threat keywords classify as THREAT."""
        from echo_chamber.cortex.graph import signal_classify
        from echo_chamber.cortex.state import CortexState, Signal, SignalCategory

        state: CortexState = {
            "signal": Signal(source="test", content="legal threat against the product")
        }
        result = signal_classify(state)
        self.assertEqual(result["category"], SignalCategory.THREAT)

    def test_signal_classify_trend(self) -> None:
        """Trend keywords classify as TREND."""
        from echo_chamber.cortex.graph import signal_classify
        from echo_chamber.cortex.state import CortexState, Signal, SignalCategory

        state: CortexState = {
            "signal": Signal(source="test", content="this is trending in r/truckers")
        }
        result = signal_classify(state)
        self.assertEqual(result["category"], SignalCategory.TREND)

    def test_signal_classify_noise(self) -> None:
        """Generic content classifies as NOISE."""
        from echo_chamber.cortex.graph import signal_classify
        from echo_chamber.cortex.state import CortexState, Signal, SignalCategory

        state: CortexState = {"signal": Signal(source="test", content="random unrelated content")}
        result = signal_classify(state)
        self.assertEqual(result["category"], SignalCategory.NOISE)

    def test_signal_route_noise_goes_to_end(self) -> None:
        """NOISE signals route to END."""
        from echo_chamber.cortex.graph import signal_route
        from echo_chamber.cortex.state import CortexState, SignalCategory

        state: CortexState = {"category": SignalCategory.NOISE, "classification_confidence": 0.5}
        result = signal_route(state)
        self.assertEqual(result, "end")

    def test_signal_route_threat_goes_to_escalate(self) -> None:
        """THREAT signals route to escalate."""
        from echo_chamber.cortex.graph import signal_route
        from echo_chamber.cortex.state import CortexState, SignalCategory

        state: CortexState = {"category": SignalCategory.THREAT, "classification_confidence": 0.8}
        result = signal_route(state)
        self.assertEqual(result, "escalate")

    def test_signal_route_low_confidence_goes_to_escalate(self) -> None:
        """Low confidence signals route to escalate."""
        from echo_chamber.cortex.graph import signal_route
        from echo_chamber.cortex.state import CortexState, SignalCategory

        state: CortexState = {"category": SignalCategory.TREND, "classification_confidence": 0.4}
        result = signal_route(state)
        self.assertEqual(result, "escalate")

    def test_signal_route_trend_goes_to_decide(self) -> None:
        """TREND with good confidence routes to decide."""
        from echo_chamber.cortex.graph import signal_route
        from echo_chamber.cortex.state import CortexState, SignalCategory

        state: CortexState = {"category": SignalCategory.TREND, "classification_confidence": 0.8}
        result = signal_route(state)
        self.assertEqual(result, "decide")

    def test_cortex_decide_trend_produces_deploy(self) -> None:
        """TREND signal produces deploy decision."""
        from echo_chamber.cortex.graph import cortex_decide
        from echo_chamber.cortex.state import CortexState, Signal, SignalCategory

        state: CortexState = {
            "signal": Signal(source="test", content="trucker IFTA complaints trending"),
            "category": SignalCategory.TREND,
            "classification_confidence": 0.8,
        }
        result = cortex_decide(state)
        self.assertIn("decision", result)
        self.assertEqual(result["decision"].action, "deploy")
        self.assertIn("reddit", result["decision"].ganglions)

    def test_cortex_decide_missing_state_escalates(self) -> None:
        """Missing signal/classification produces escalate decision."""
        from echo_chamber.cortex.graph import cortex_decide

        result = cortex_decide({})  # type: ignore[arg-type]
        self.assertEqual(result["decision"].action, "escalate")
        self.assertEqual(result["routing_target"], "escalate")

    def test_dispatch_logs_result(self) -> None:
        """dispatch produces dispatch_results."""
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

    def test_escalate_produces_error_entry(self) -> None:
        """escalate adds escalation to errors for Commander visibility."""
        from echo_chamber.cortex.graph import escalate
        from echo_chamber.cortex.state import CortexDecision, CortexState, Signal, SignalCategory

        state: CortexState = {
            "signal": Signal(source="test", content="bad things happening"),
            "category": SignalCategory.THREAT,
            "decision": CortexDecision(
                action="escalate",
                confidence=0.8,
                escalation_reason="Threat detected",
            ),
        }
        result = escalate(state)
        self.assertIn("errors", result)
        self.assertTrue(any("ESCALATION" in e for e in result["errors"]))


class TestCortexGraphInvocation(unittest.TestCase):
    """Full graph invocation tests — end-to-end pipeline."""

    def test_full_pipeline_trend_to_dispatch(self) -> None:
        """TREND signal flows through: ingest → classify → decide → dispatch → learn."""
        from echo_chamber.cortex.graph import build_cortex_graph

        graph = build_cortex_graph()
        result = graph.invoke(
            {"signal": {"source": "manual", "content": "IFTA complaints trending in r/truckers"}}
        )
        self.assertIn("decision", result)
        self.assertEqual(result["decision"].action, "deploy")
        self.assertIn("dispatch_results", result)

    def test_full_pipeline_noise_ends_early(self) -> None:
        """NOISE signal flows through: ingest → classify → END."""
        from echo_chamber.cortex.graph import build_cortex_graph

        graph = build_cortex_graph()
        result = graph.invoke({"signal": {"source": "manual", "content": "random unrelated noise"}})
        self.assertEqual(result.get("category").value, "noise")
        self.assertNotIn("decision", result)

    def test_full_pipeline_threat_escalates(self) -> None:
        """THREAT signal flows through: ingest → classify → escalate."""
        from echo_chamber.cortex.graph import build_cortex_graph

        graph = build_cortex_graph()
        result = graph.invoke(
            {"signal": {"source": "manual", "content": "legal threat against client"}}
        )
        self.assertEqual(result.get("category").value, "threat")
        self.assertIn("errors", result)
