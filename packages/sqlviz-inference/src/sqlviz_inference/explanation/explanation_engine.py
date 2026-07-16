"""ExplanationEngine V2 — analyst-language explanations (DOC10 §6.16).

Consumes ConstraintReport + scored ChartCandidates + IntentResult to produce
a structured Explanation with:
  - reason_main:   the primary reason for the chosen chart
  - reason_secondary: supporting context
  - alternatives_considered: other candidates that were scored (not eliminated)
  - alternatives_rejected:  candidates hard-eliminated by ConstraintEngine + why
  - full_text:     assembled Spanish explanation ready to display

Templates are loaded from rules/explanation_templates.yaml via the global
yaml_loader singleton — YAML-configurable, no LLM, no runtime generation.

Pipeline position: step 15, after TitleEngine, before FeedbackEngine.run_persist.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from ..contracts.explanation import Explanation
from ..utils.sqlviz_logging import get_logger
from ..utils.yaml_loader import yaml_loader

_log = get_logger("explanation_engine")

if TYPE_CHECKING:
    from ..context import RuntimeContext

_TEMPLATE_FILE = "explanation_templates.yaml"


class ExplanationEngine:

    def __init__(self) -> None:
        self._templates: dict[str, Any] | None = None

    @property
    def templates(self) -> dict[str, Any]:
        if self._templates is None:
            self._templates = yaml_loader.load(_TEMPLATE_FILE)
        return self._templates

    # ── Public pipeline interface ─────────────────────────────────────────────

    def run(self, context: RuntimeContext) -> RuntimeContext:
        """Build Explanation from pipeline context and store in context.explanation_v2."""
        try:
            context.explanation_v2 = self._build(context)
        except Exception as e:  # noqa: BLE001
            _log.warning("%s", e, extra={"trace_id": context.trace_id})
            context.errors.append(f"ExplanationEngine: {e}")
            context.explanation_v2 = self._fallback(context)
        return context

    # ── Core logic ────────────────────────────────────────────────────────────

    def _build(self, context: RuntimeContext) -> Explanation:
        intent = context.intent_winner
        chart = context.chart_winner
        tmpl = self._template_for(intent, chart)
        fallback = self._intent_fallback(intent)
        display = self.templates.get("chart_display_names", {})

        reason_main = tmpl.get("reason_main") or fallback.get("reason_main") or (
            f"es el tipo de gráfico más apropiado para la intención '{intent}'"
        )
        reason_secondary = tmpl.get("reason_secondary") or fallback.get("reason_secondary") or ""

        # Alternatives considered: top-2 scored candidates (rank ≥ 2)
        alternatives_considered = self._scored_alternatives(context, chart)

        # Alternatives rejected: hard-eliminated by ConstraintEngine
        alternatives_rejected = self._eliminated_alternatives(context, chart, tmpl, display)

        # Assemble full_text
        chart_display = display.get(chart, chart)
        full_text = self._assemble(
            chart_display=chart_display,
            reason_main=reason_main,
            reason_secondary=reason_secondary,
            alternatives_considered=alternatives_considered,
            alternatives_rejected=alternatives_rejected,
            display=display,
        )

        return Explanation(
            chart_winner=chart,
            intent=intent,
            reason_main=reason_main,
            reason_secondary=reason_secondary,
            alternatives_considered=alternatives_considered,
            alternatives_rejected=alternatives_rejected,
            full_text=full_text,
        )

    def _template_for(self, intent: str, chart: str) -> dict[str, Any]:
        key = f"{intent}_{chart}"
        intent_chart = cast(dict[str, Any], self.templates.get("intent_chart", {}))
        return cast(dict[str, Any], intent_chart.get(key, {}))

    def _intent_fallback(self, intent: str) -> dict[str, Any]:
        fallbacks = cast(dict[str, Any], self.templates.get("intent_fallback", {}))
        return cast(dict[str, Any], fallbacks.get(intent, {}))

    def _scored_alternatives(
        self, context: RuntimeContext, winner: str
    ) -> list[str]:
        """Return up to 2 chart types that were scored (rank ≥ 2), highest-ranked first."""
        candidates = context.scored_candidates or []
        # Filter: not the winner, not eliminated (rank > 0), sort by rank ascending
        eligible = [
            c for c in candidates
            if c.chart_type != winner and c.rank > 0
        ]
        eligible.sort(key=lambda c: c.rank)
        return [c.chart_type for c in eligible[:2]]

    def _eliminated_alternatives(
        self,
        context: RuntimeContext,
        winner: str,
        tmpl: dict[str, Any],
        display: dict[str, str],
    ) -> list[dict[str, str]]:
        """Collect hard-eliminated candidates with their rejection reasons."""
        if not context.constraint_report:
            return []
        result = []
        seen: set[str] = set()
        for v in context.constraint_report.eliminated:
            ct = v.chart_type
            if ct == winner or ct in seen:
                continue
            seen.add(ct)
            reject_key = f"reject_{ct}"
            reason = tmpl.get(reject_key) or v.reason
            result.append({"chart": ct, "reason": reason})
        return result

    def _assemble(
        self,
        chart_display: str,
        reason_main: str,
        reason_secondary: str,
        alternatives_considered: list[str],
        alternatives_rejected: list[dict[str, str]],
        display: dict[str, str],
    ) -> str:
        parts: list[str] = [f"Elegí {chart_display} porque {reason_main}."]
        if reason_secondary:
            parts.append(reason_secondary + ".")
        for alt in alternatives_rejected[:2]:
            alt_name = display.get(alt["chart"], alt["chart"])
            parts.append(f"Consideré {alt_name} pero {alt['reason']}.")
        if alternatives_considered:
            alt_names = [display.get(a, a) for a in alternatives_considered[:2]]
            parts.append(
                "Otras alternativas evaluadas: " + ", ".join(alt_names) + "."
            )
        return " ".join(parts)

    # ── Fallback when template or pipeline data is incomplete ─────────────────

    def _fallback(self, context: RuntimeContext) -> Explanation:
        chart = context.chart_winner
        intent = context.intent_winner
        display = self.templates.get("chart_display_names", {})
        chart_display = display.get(chart, chart)
        reason = f"es el tipo de gráfico más apropiado para la intención '{intent}'"
        return Explanation(
            chart_winner=chart,
            intent=intent,
            reason_main=reason,
            reason_secondary="",
            alternatives_considered=[],
            alternatives_rejected=[],
            full_text=f"Elegí {chart_display} porque {reason}.",
        )
