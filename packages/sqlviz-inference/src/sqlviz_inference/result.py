from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .context import RuntimeContext

if TYPE_CHECKING:
    from .contracts.explanation import Explanation
    from .contracts.layout import DashboardRole, LayoutDeclaration
    from .profile.data_profile import DataProfile
    from .spec.visual_spec import VisualSpec


@dataclass
class InferenceResult:
    """
    The final, complete output of the Inference Engine.
    This is what sqlviz-api and sqlviz-web consume.

    Every field has a mathematical justification (DOC 4).
    Every field is versioned for traceability.
    """

    # ── Versioning ────────────────────────────────────────────
    rules_version: str
    feature_vector_version: str
    engine_version: str

    # ── Intent ────────────────────────────────────────────────
    intent_winner: str
    intent_raw_score: float
    intent_normalized_score: float
    intent_confidence_gap: float
    intent_quality: str
    intent_alternatives: list[dict[str, Any]]

    # ── Chart ─────────────────────────────────────────────────
    chart_winner: str
    chart_raw_score: float
    chart_normalized_score: float
    chart_confidence_gap: float
    chart_quality: str
    chart_alternatives: list[dict[str, Any]]

    # ── Layout ────────────────────────────────────────────────
    col_span: int
    row_span: int
    layout_importance: float
    panel_height_px: int

    # ── KPI Trend (moved out of frontend per §16.6) ───────────
    trend_direction_label: str  # "growing" | "declining" | "flat" | "unknown"

    # ── Filters ───────────────────────────────────────────────
    filter_controls: list[dict[str, Any]]

    # ── Title ─────────────────────────────────────────────────
    title: str
    title_confidence: float

    # ── Fallback ──────────────────────────────────────────────
    fallback_applied: bool
    fallback_reason: str

    # ── Explainability ────────────────────────────────────────
    explanation: list[dict[str, Any]]
    score_trace: dict[str, Any]
    fingerprint: str
    feature_vector: list[float]

    # ── Diagnostics ───────────────────────────────────────────
    errors: list[str]
    elapsed_ms: float

    # ── V0.2 Fase 0 — new contracts (Optional for backwards compat) ───────
    data_profile: DataProfile | None = None
    visual_spec: VisualSpec | None = None

    # ── V0.2 Fase D — layout declaration + dashboard role ─────────────────
    layout_declaration: LayoutDeclaration | None = None
    dashboard_role: DashboardRole | None = None

    # ── V0.2 Fase F — ExplanationEngine V2 ───────────────────────────────
    explanation_v2: Explanation | None = None

    # ── V0.2.2 — FeedbackEngine preferred chart (suggestion, never forced) ──
    feedback_preferred_chart: str | None = None
    # Engine's pure winner before any panel-level chart_override is applied.
    # Stable across re-executes for same SQL/data; used for fixed list ordering in UI.
    chart_engine_winner: str | None = None

    @classmethod
    def from_context(cls, context: RuntimeContext) -> InferenceResult:
        """Build the final result from a fully-processed RuntimeContext."""

        intent_alternatives = [
            {
                "intent": s.intent,
                "raw_score": round(s.raw_score, 4),
            }
            for s in context.intent_scores[1:3]
            if s.raw_score > 0.0
        ]

        filter_controls_dict: list[dict[str, Any]] = [
            {
                "variable": fc.variable,
                "label": fc.label,
                "control_type": fc.control_type,
                "column_name": fc.column_name,
                "column_type": fc.column_type,
                "scope": fc.scope,
            }
            for fc in context.filter_controls
        ]

        # trend_direction_label computed here (backend), not in frontend (§16.6).
        fv = context.feature_vector
        strength = fv[28] if len(fv) > 28 else 0.0
        direction = fv[38] if len(fv) > 38 else 0.5
        if strength <= 0.5:
            trend_direction_label = "unknown"
        elif direction > 0.65:
            trend_direction_label = "growing"
        elif direction < 0.35:
            trend_direction_label = "declining"
        else:
            trend_direction_label = "flat"

        return cls(
            rules_version=context.rules_version,
            feature_vector_version=context.feature_vector_version,
            engine_version=context.engine_version,

            intent_winner=context.intent_winner,
            intent_raw_score=context.intent_raw_score,
            intent_normalized_score=context.intent_normalized_score,
            intent_confidence_gap=context.intent_confidence_gap,
            intent_quality=context.intent_quality,
            intent_alternatives=intent_alternatives,

            chart_winner=context.chart_winner,
            chart_raw_score=context.chart_raw_score,
            chart_normalized_score=context.chart_normalized_score,
            chart_confidence_gap=context.chart_confidence_gap,
            chart_quality=context.chart_quality,
            chart_alternatives=context.chart_alternatives,

            col_span=context.col_span,
            row_span=context.row_span,
            layout_importance=context.layout_importance,
            panel_height_px=context.panel_height_px,
            trend_direction_label=trend_direction_label,

            filter_controls=filter_controls_dict,

            title=context.title,
            title_confidence=context.title_confidence,

            fallback_applied=context.fallback_applied,
            fallback_reason=context.fallback_reason,

            explanation=context.explanation,
            score_trace=context.score_trace,
            fingerprint=context.fingerprint,
            feature_vector=context.feature_vector,

            errors=context.errors,
            elapsed_ms=float(
                context.score_trace.get("pipeline", {}).get("elapsed_ms", 0.0)
            ),

            data_profile=context.data_profile,
            visual_spec=context.visual_spec,

            layout_declaration=context.layout_declaration,
            dashboard_role=context.dashboard_role,

            explanation_v2=context.explanation_v2,

            feedback_preferred_chart=context.feedback_preferred,
            chart_engine_winner=context.chart_engine_winner or context.chart_winner,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for JSON API responses."""
        from dataclasses import asdict
        return asdict(self)
