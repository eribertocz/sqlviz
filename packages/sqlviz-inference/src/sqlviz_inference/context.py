from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from sqlviz_core.models import ColumnSchema


@dataclass
class IntentScore:
    intent: str
    raw_score: float
    normalized_score: float
    signals: dict[str, float] = field(default_factory=dict)


@dataclass
class ChartCandidate:
    chart_type: str
    affinity_score: float
    penalty_total: float
    final_score: float
    normalized_score: float
    penalties_applied: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class FilterControl:
    variable: str
    label: str
    control_type: str
    column_name: str
    column_type: str
    cardinality: int = 0
    scope: str = "global"


@dataclass
class RuntimeContext:
    """
    Carrier of all inference data using field-owned mutation (DOC5 §16.1).
    Flows through every module in the pipeline. Modules write ONLY to the
    fields they own (DOC5 §3.4) and never reconstruct a new instance.
    """

    # ── Input ──────────────────────────────────────────────────────────────
    sql: str
    data: list[dict[str, Any]] = field(default_factory=list)
    schema: list[ColumnSchema] = field(default_factory=list)

    # ── Parser output ───────────────────────────────────────────────────────
    ast: Any = None
    fingerprint: str = "UNKNOWN"
    sql_features: list[float] = field(default_factory=list)

    # ── Feature Engine output ───────────────────────────────────────────────
    feature_vector: list[float] = field(default_factory=lambda: [0.0] * 39)

    # ── Intent Engine output ────────────────────────────────────────────────
    intent_scores: list[IntentScore] = field(default_factory=list)
    intent_winner: str = "detail"
    intent_raw_score: float = 0.0
    intent_normalized_score: float = 0.0
    intent_confidence_gap: float = 0.0
    intent_quality: str = "low"

    # ── Chart Engine output ─────────────────────────────────────────────────
    chart_candidates: list[ChartCandidate] = field(default_factory=list)
    chart_winner: str = "table"
    chart_raw_score: float = 0.0
    chart_normalized_score: float = 0.0
    chart_confidence_gap: float = 0.0
    chart_quality: str = "low"
    chart_alternatives: list[dict[str, Any]] = field(default_factory=list)
    fallback_applied: bool = False
    fallback_reason: str = ""

    # ── Layout Engine output ────────────────────────────────────────────────
    col_span: int = 12
    row_span: int = 1
    layout_importance: float = 0.0
    panel_height_px: int = 360

    # ── Filter Engine output ────────────────────────────────────────────────
    filter_controls: list[FilterControl] = field(default_factory=list)

    # ── Title Engine output ─────────────────────────────────────────────────
    title: str = ""
    title_confidence: float = 0.0

    # ── Explainability ──────────────────────────────────────────────────────
    explanation: list[dict[str, Any]] = field(default_factory=list)
    score_trace: dict[str, Any] = field(default_factory=dict)

    # ── Error tracking ──────────────────────────────────────────────────────
    errors: list[str] = field(default_factory=list)

    # ── Versioning ──────────────────────────────────────────────────────────
    rules_version: str = "v0.1.0"
    feature_vector_version: str = "v0"
    engine_version: str = "sqlviz-inference-0.1.0"

    def with_error(self, module: str, error: str) -> RuntimeContext:
        new_errors = self.errors + [f"{module}: {error}"]
        return replace(self, errors=new_errors)

    @property
    def has_data(self) -> bool:
        return len(self.data) > 0

    @property
    def has_schema(self) -> bool:
        return len(self.schema) > 0

    @property
    def row_count(self) -> int:
        return len(self.data)

    @property
    def col_count(self) -> int:
        return len(self.data[0]) if self.data else 0
