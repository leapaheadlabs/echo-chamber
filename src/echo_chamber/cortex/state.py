"""Cortex StateGraph state definition.

Implements CortexState from SPEC.md FR-CX-001.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, NotRequired

from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class SignalCategory(StrEnum):
    TREND = "trend"
    MENTION = "mention"
    OPPORTUNITY = "opportunity"
    THREAT = "threat"
    NOISE = "noise"


class AutonomyLevel(StrEnum):
    L0 = "L0"  # Commander-only
    L1 = "L1"  # Review then post
    L2 = "L2"  # Batch approve
    L3 = "L3"  # Auto-deploy with kill window
    L4 = "L4"  # Full auto


class Signal(BaseModel):
    """Normalised signal ingested by Cortex."""

    source: str  # e.g., "reddit", "rss", "manual"
    platform: str | None = None
    community: str | None = None
    content: str
    url: str | None = None
    author: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CortexDecision(BaseModel):
    """Decision produced by the Cortex decide node."""

    action: str  # "deploy", "escalate", "ignore", "learn"
    ganglions: list[str] = Field(default_factory=list)
    autonomy_level: AutonomyLevel = AutonomyLevel.L1
    content_params: dict[str, Any] = Field(default_factory=dict)
    rationale: str = ""
    confidence: float = Field(ge=0.0, le=1.0)
    escalation_reason: str | None = None


class CortexState(TypedDict, total=False):
    """Full Cortex StateGraph state (SPEC.md FR-CX-001)."""

    # ── Input ─────────────────────────────────────────────────────
    signal: Signal

    # ── Classification ────────────────────────────────────────────
    category: SignalCategory
    classification_confidence: float

    # ── Decision ──────────────────────────────────────────────────
    decision: CortexDecision
    routing_target: str  # ganglion name or "escalate"

    # ── Context (assembled by decide node) ────────────────────────
    active_clients: NotRequired[dict[str, dict[str, Any]]]
    campaign_memory: NotRequired[list[dict[str, Any]]]
    account_pool_status: NotRequired[dict[str, Any]]

    # ── Dispatch ──────────────────────────────────────────────────
    dispatch_results: NotRequired[dict[str, Any]]

    # ── Health ────────────────────────────────────────────────────
    health_issues: NotRequired[list[str]]

    # ── Errors ────────────────────────────────────────────────────
    errors: NotRequired[list[str]]
