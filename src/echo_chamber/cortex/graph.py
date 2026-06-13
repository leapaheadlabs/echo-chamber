"""Cortex StateGraph — central nervous system.

SPEC.md FR-CX-001 through FR-CX-007.
8 nodes: signal_ingest → classify → route → decide → dispatch → escalate → learn → health_check.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import structlog
from langgraph.graph import END, StateGraph

from echo_chamber.cortex.state import (
    AutonomyLevel,
    CortexDecision,
    CortexState,
    Signal,
    SignalCategory,
)

logger = structlog.get_logger(__name__)


# ── Nodes ──────────────────────────────────────────────────────────────


def signal_ingest(state: CortexState) -> dict[str, Any]:
    """Normalize inbound signal to Signal model. FR-CX-001."""
    raw = state.get("signal")
    if raw is None:
        return {"errors": ["signal_ingest: no signal in state"]}

    if isinstance(raw, Signal):
        signal = raw
    elif isinstance(raw, dict):
        try:
            signal = Signal(**raw)
        except Exception as exc:
            return {"errors": [f"signal_ingest: invalid signal: {exc}"]}
    else:
        return {"errors": [f"signal_ingest: unexpected signal type: {type(raw)}"]}

    logger.info(
        "signal_ingested",
        source=signal.source,
        platform=signal.platform,
        community=signal.community,
    )
    return {"signal": signal}


def signal_classify(state: CortexState) -> dict[str, Any]:
    """Classify signal as trend/mention/opportunity/threat/noise. FR-CX-002.

    Stub: classifies based on simple keyword heuristics.
    LLM classifier wiring tracked in TASK-007.
    """
    signal = state.get("signal")
    if signal is None:
        return {"errors": ["signal_classify: no signal in state"]}

    content = signal.content.lower()

    # Stub classification — keyword heuristics for now
    if any(word in content for word in ["threat", "ban", "lawsuit", "legal", "crisis"]):
        category = SignalCategory.THREAT
        confidence = 0.8
    elif any(word in content for word in ["trend", "trending", "viral", "surge"]):
        category = SignalCategory.TREND
        confidence = 0.7
    elif any(word in content for word in ["mention", "said about", "talking about"]):
        category = SignalCategory.MENTION
        confidence = 0.7
    elif any(word in content for word in ["opportunity", "chance", "gap", "untapped"]):
        category = SignalCategory.OPPORTUNITY
        confidence = 0.7
    else:
        category = SignalCategory.NOISE
        confidence = 0.5

    logger.info(
        "signal_classified",
        category=category.value,
        confidence=confidence,
    )
    return {"category": category, "classification_confidence": confidence}


def signal_route(state: CortexState) -> str:
    """Route signal based on classification. FR-CX-003.

    No LLM — pure conditional edge logic.
    Returns next node name.
    """
    category = state.get("category")
    confidence = state.get("classification_confidence", 0.0)

    if category == SignalCategory.NOISE:
        return "end"
    if category == SignalCategory.THREAT:
        return "escalate"
    if confidence < 0.6:
        return "escalate"
    return "decide"


def cortex_decide(state: CortexState) -> dict[str, Any]:
    """Produce CortexDecision from classified signal + context. FR-CX-004.

    Stub: produces a decision based on category.
    LLM decision engine wiring tracked in TASK-008.
    """
    signal = state.get("signal")
    category = state.get("category")
    confidence = state.get("classification_confidence", 0.0)

    if signal is None or category is None:
        return {
            "decision": CortexDecision(
                action="escalate",
                confidence=0.0,
                rationale="Missing signal or classification",
                escalation_reason="Incomplete state",
            ),
            "routing_target": "escalate",
        }

    # Stub decision logic
    if category == SignalCategory.TREND:
        decision = CortexDecision(
            action="deploy",
            ganglions=["reddit"],
            autonomy_level=AutonomyLevel.L3,
            confidence=confidence,
            rationale=f"Trend detected: {signal.content[:100]}",
        )
        routing = "dispatch"
    elif category == SignalCategory.OPPORTUNITY:
        decision = CortexDecision(
            action="deploy",
            ganglions=["reddit"],
            autonomy_level=AutonomyLevel.L2,
            confidence=confidence,
            rationale=f"Opportunity detected: {signal.content[:100]}",
        )
        routing = "dispatch"
    elif category == SignalCategory.MENTION:
        decision = CortexDecision(
            action="deploy",
            ganglions=["reddit"],
            autonomy_level=AutonomyLevel.L2,
            confidence=confidence,
            rationale=f"Mention detected: {signal.content[:100]}",
        )
        routing = "dispatch"
    else:
        decision = CortexDecision(
            action="escalate",
            confidence=confidence,
            rationale=f"Unhandled category: {category.value}",
            escalation_reason=f"Category {category.value} needs human review",
        )
        routing = "escalate"

    logger.info(
        "cortex_decision",
        action=decision.action,
        ganglions=decision.ganglions,
        autonomy_level=decision.autonomy_level.value,
        confidence=decision.confidence,
    )
    return {"decision": decision, "routing_target": routing}


def dispatch(state: CortexState) -> dict[str, Any]:
    """Forward CortexDecision to target ganglion(s). FR-CX-005.

    Stub: logs the dispatch.
    Ganglion sub-graph dispatch tracked in TASK-012+.
    """
    decision = state.get("decision")
    if decision is None:
        return {"errors": ["dispatch: no decision in state"]}

    dispatch_id = str(uuid.uuid4())
    logger.info(
        "dispatch_sent",
        dispatch_id=dispatch_id,
        action=decision.action,
        ganglions=decision.ganglions,
        autonomy_level=decision.autonomy_level.value,
    )

    return {
        "dispatch_results": {
            dispatch_id: {
                "ganglions": decision.ganglions,
                "action": decision.action,
                "status": "dispatched",
                "dispatched_at": datetime.now(UTC).isoformat(),
            }
        }
    }


def escalate(state: CortexState) -> dict[str, Any]:
    """Queue for human Commander review. FR-CX-005.

    Stub: logs the escalation.
    Discord notification wiring tracked in TASK-009.
    """
    decision = state.get("decision")
    signal = state.get("signal")
    category = state.get("category")

    escalation_reason = decision.escalation_reason if decision else "Unknown escalation"

    logger.warning(
        "escalation_queued",
        category=category.value if category else "unknown",
        reason=escalation_reason,
        signal_content=signal.content[:200] if signal else "no signal",
    )

    return {"errors": [f"ESCALATION: {escalation_reason}"]}


def learn(state: CortexState) -> dict[str, Any]:
    """Extract lessons from completed deployments. FR-CX-006.

    Stub: logs completion.
    LLM lesson extraction tracked in TASK-019.
    """
    dispatch_results = state.get("dispatch_results", {})
    logger.info(
        "learn_complete",
        dispatch_count=len(dispatch_results),
    )
    return {}


def health_check(state: CortexState) -> dict[str, Any]:
    """Periodic account pool + API health scan. FR-CX-007.

    Stub: returns empty issues.
    Account health scanner tracked in TASK-010.
    """
    logger.info("health_check_complete")
    return {"health_issues": []}


# ── Graph Construction ──────────────────────────────────────────────────


def build_cortex_graph() -> Any:
    """Build and compile the Cortex StateGraph.

    Returns a compiled graph ready for invocation.
    """
    graph: StateGraph[CortexState, None, CortexState, CortexState] = StateGraph(CortexState)

    # Add nodes
    graph.add_node("signal_ingest", signal_ingest)
    graph.add_node("signal_classify", signal_classify)
    graph.add_node("decide", cortex_decide)
    graph.add_node("dispatch", dispatch)
    graph.add_node("escalate", escalate)
    graph.add_node("learn", learn)
    graph.add_node("health_check", health_check)

    # Entry point
    graph.set_entry_point("signal_ingest")

    # Edges
    graph.add_edge("signal_ingest", "signal_classify")

    # Conditional routing after classification
    graph.add_conditional_edges(
        "signal_classify",
        signal_route,
        {
            "decide": "decide",
            "escalate": "escalate",
            "end": END,
        },
    )

    # After decide → dispatch or escalate
    def route_decision(state: CortexState) -> str:
        routing = state.get("routing_target", "escalate")
        if routing == "dispatch":
            return "dispatch"
        return "escalate"

    graph.add_conditional_edges(
        "decide",
        route_decision,
        {
            "dispatch": "dispatch",
            "escalate": "escalate",
        },
    )

    # After dispatch → learn
    graph.add_edge("dispatch", "learn")
    graph.add_edge("learn", END)
    graph.add_edge("escalate", END)
    graph.add_edge("health_check", END)

    return graph.compile()
