from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..contracts.chart import ChartCandidate as ChartCandidateV2
from ..contracts.chart import ChartScore
from ..utils.yaml_loader import yaml_loader

if TYPE_CHECKING:
    from ..context import RuntimeContext

# Cleveland & McGill / Heer & Bostock perceptual accuracy per chart type
_PERCEPTUAL_ACCURACY: dict[str, float] = {
    "kpi":            0.90,   # single value: no perceptual encoding needed
    "line":           0.95,   # position along common scale (highest precision)
    "bar":            0.90,   # length encoding (second tier)
    "bar_horizontal": 0.90,
    "pie":            0.60,   # angle/area encoding (lower precision)
    "scatter":        0.85,   # 2D position (precise but requires mental correlation)
    "histogram":      0.85,   # length encoding per bin
    "table":          0.80,   # textual: accurate but requires sequential reading
}

# Base cognitive load per chart type (before data-dependent penalties)
_BASE_COGNITIVE_LOAD: dict[str, float] = {
    "kpi":            0.05,
    "line":           0.15,
    "bar":            0.15,
    "bar_horizontal": 0.15,
    "pie":            0.35,
    "scatter":        0.35,
    "histogram":      0.20,
    "table":          0.30,
}

# Base ambiguity per chart type (how unclear the encoding is)
_BASE_AMBIGUITY: dict[str, float] = {
    "kpi":            0.02,
    "line":           0.08,
    "bar":            0.08,
    "bar_horizontal": 0.08,
    "pie":            0.40,   # angle estimation is inherently ambiguous
    "scatter":        0.25,   # requires mental correlation
    "histogram":      0.12,
    "table":          0.05,
}

# Base information density per chart type
_BASE_INFO_DENSITY: dict[str, float] = {
    "kpi":            0.90,   # 1 row shown perfectly — very efficient
    "line":           0.82,
    "bar":            0.75,
    "bar_horizontal": 0.75,
    "pie":            0.60,
    "scatter":        0.82,
    "histogram":      0.70,
    "table":          0.90,   # shows all columns and rows
}


class ScoringModel:
    """
    Replaces afinidad-menos-penalización with explicit 10-dimension scoring.

    Score = semantic_fit        (0.45 — V0.1 affinity, validated signal)
          + task_fit            (0.20 — analytical task alignment)
          + perceptual_accuracy (0.10 — Cleveland & McGill hierarchy)
          + readability         (0.08 — ReadabilityModel legibility_score)
          + information_density (0.06 — data shown per visual unit)
          + business_relevance  (0.06 — common BI usage pattern fit)
          − cognitive_load      (0.02 — mental effort to interpret)
          − visual_clutter      (0.01 — visual noise)
          − ambiguity           (0.01 — perceptual encoding uncertainty)
          − interaction_cost    (0.01 — scrolling / zooming required)

    semantic_fit dominates (0.45) to preserve V0.1 benchmark accuracy.
    Other dimensions provide tie-breaking and generate explanation signals.
    """

    def __init__(self) -> None:
        self._weights: dict[str, Any] | None = None
        self._task_fit: dict[str, Any] | None = None

    @property
    def weights(self) -> dict[str, Any]:
        if self._weights is None:
            self._weights = yaml_loader.load("scoring_weights.yaml")
        return self._weights

    @property
    def task_fit_matrix(self) -> dict[str, Any]:
        if self._task_fit is None:
            self._task_fit = yaml_loader.load("task_fit_matrix.yaml")
        return self._task_fit

    def run(self, context: RuntimeContext) -> RuntimeContext:
        try:
            context.scored_candidates = self._score_all(context)
            self._update_winner(context)
        except Exception as e:
            context.errors.append(f"ScoringModel: {e}")
        return context

    def _score_all(self, context: RuntimeContext) -> list[ChartCandidateV2]:
        eliminated = set()
        if context.constraint_report:
            eliminated = {v.chart_type for v in context.constraint_report.eliminated}

        # Build readability lookup: chart_type → legibility_score
        legibility: dict[str, float] = {}
        if context.readability_result:
            for cr in context.readability_result.by_candidate:
                legibility[cr.chart_type] = cr.legibility_score

        w_pos = self.weights.get("positive", {})
        w_neg = self.weights.get("negative", {})
        intent = context.intent_winner

        # Data stats for data-dependent dimensions
        row_count = (
            context.data_profile.row_count
            if context.data_profile
            else len(context.data)
        )
        cat_cardinality = self._cat_cardinality(context)
        n_series = self._n_series(context)

        scored: list[tuple[float, ChartCandidateV2]] = []

        for cand in context.chart_candidates:
            ct = cand.chart_type
            if ct in eliminated:
                v2 = ChartCandidateV2(
                    chart_type=ct,
                    score=ChartScore(),
                    rank=0,
                    eliminated_by_rule=self._elimination_rule(ct, context),
                )
                scored.append((-1.0, v2))
                continue

            s = self._compute_score(
                chart_type=ct,
                intent=intent,
                semantic_fit=cand.normalized_score,
                legibility=legibility.get(ct, 0.80),
                row_count=row_count,
                cat_cardinality=cat_cardinality,
                n_series=n_series,
            )

            pos = w_pos
            neg = w_neg
            total = (
                pos.get("semantic_fit", 0.45) * s.semantic_fit
                + pos.get("task_fit", 0.20) * s.task_fit
                + pos.get("perceptual_accuracy", 0.10) * s.perceptual_accuracy
                + pos.get("readability", 0.08) * s.readability
                + pos.get("information_density", 0.06) * s.information_density
                + pos.get("business_relevance", 0.06) * s.business_relevance
                - neg.get("cognitive_load", 0.02) * s.cognitive_load
                - neg.get("visual_clutter", 0.01) * s.visual_clutter
                - neg.get("ambiguity", 0.01) * s.ambiguity
                - neg.get("interaction_cost", 0.01) * s.interaction_cost
            )

            v2 = ChartCandidateV2(chart_type=ct, score=s, rank=0)
            scored.append((total, v2))

        # Rank by total score descending (eliminated get -1, sort last)
        scored.sort(key=lambda x: x[0], reverse=True)

        result = []
        rank = 1
        for total, v2 in scored:
            if v2.eliminated_by_rule is None:
                v2.rank = rank
                rank += 1
            result.append(v2)

        return result

    def _compute_score(
        self,
        chart_type: str,
        intent: str,
        semantic_fit: float,
        legibility: float,
        row_count: int,
        cat_cardinality: int,
        n_series: int,
    ) -> ChartScore:
        tf_matrix = self.task_fit_matrix
        task_fit = float(tf_matrix.get(chart_type, {}).get(intent, 0.0))

        perceptual = _PERCEPTUAL_ACCURACY.get(chart_type, 0.80)

        info_density = self._information_density(chart_type, row_count, cat_cardinality)

        business_relevance = min(1.0, task_fit * 0.90 + 0.05)

        cognitive_load = self._cognitive_load(chart_type, cat_cardinality, n_series, row_count)

        visual_clutter = self._visual_clutter(chart_type, cat_cardinality, n_series)

        ambiguity = _BASE_AMBIGUITY.get(chart_type, 0.10)

        interaction_cost = self._interaction_cost(chart_type, row_count, cat_cardinality)

        return ChartScore(
            semantic_fit=round(semantic_fit, 4),
            task_fit=round(task_fit, 4),
            perceptual_accuracy=round(perceptual, 4),
            readability=round(legibility, 4),
            information_density=round(info_density, 4),
            business_relevance=round(business_relevance, 4),
            cognitive_load=round(cognitive_load, 4),
            visual_clutter=round(visual_clutter, 4),
            ambiguity=round(ambiguity, 4),
            interaction_cost=round(interaction_cost, 4),
        )

    def _information_density(self, chart_type: str, row_count: int, cat_cardinality: int) -> float:
        base = _BASE_INFO_DENSITY.get(chart_type, 0.70)
        if chart_type == "kpi":
            return 1.0 if row_count == 1 else 0.60
        if chart_type == "line":
            return min(1.0, base + 0.02 * min(5, (row_count - 4) // 2)) if row_count > 4 else base
        if chart_type == "table":
            return min(1.0, 0.70 + 0.02 * min(10, (row_count - 1)))
        return base

    def _cognitive_load(
        self, chart_type: str, cat_cardinality: int, n_series: int, row_count: int
    ) -> float:
        load = _BASE_COGNITIVE_LOAD.get(chart_type, 0.25)
        if chart_type == "bar":
            load += 0.03 * max(0, cat_cardinality - 5)
        elif chart_type == "bar_horizontal":
            load += 0.02 * max(0, cat_cardinality - 5)
        elif chart_type == "pie":
            load += 0.05 * max(0, cat_cardinality - 2)
        elif chart_type == "line":
            load += 0.05 * max(0, n_series - 1)
        elif chart_type == "table":
            load += 0.03 * max(0, (row_count - 5) // 5)
        return min(0.95, max(0.0, load))

    def _visual_clutter(self, chart_type: str, cat_cardinality: int, n_series: int) -> float:
        if chart_type == "bar":
            return min(0.80, 0.05 + 0.03 * max(0, cat_cardinality - 8))
        if chart_type == "bar_horizontal":
            return min(0.60, 0.05 + 0.02 * max(0, cat_cardinality - 10))
        if chart_type == "pie":
            return min(0.70, 0.05 + 0.10 * max(0, cat_cardinality - 4))
        if chart_type == "line":
            return min(0.60, 0.05 + 0.08 * max(0, n_series - 1))
        if chart_type == "scatter":
            return 0.10
        if chart_type == "table":
            return 0.15
        return 0.05

    def _interaction_cost(self, chart_type: str, row_count: int, cat_cardinality: int) -> float:
        if chart_type == "table":
            return min(0.60, 0.10 + 0.05 * max(0, (row_count - 10) // 5))
        if chart_type in ("bar", "bar_horizontal"):
            return 0.05 if cat_cardinality <= 10 else 0.15
        if chart_type == "scatter":
            return 0.15
        if chart_type == "kpi":
            return 0.00
        return 0.05

    def _update_winner(self, context: RuntimeContext) -> None:
        if not context.scored_candidates:
            return
        # Respect hard architectural fallbacks set by ChartEngine (e.g. percentile override).
        # ConstraintEngine fallbacks are logical eliminations — re-ranking on top is fine.
        if context.fallback_applied and not context.fallback_reason.startswith("ConstraintEngine:"):
            return
        winner = next((c for c in context.scored_candidates if c.rank == 1), None)
        if winner is None:
            return
        if winner.chart_type != context.chart_winner:
            old = context.chart_winner
            context.chart_winner = winner.chart_type
            context.fallback_applied = True
            context.fallback_reason = (
                f"ScoringModel: re-ranked {old} → {winner.chart_type}"
            )

    def _cat_cardinality(self, context: RuntimeContext) -> int:
        if context.data_profile and context.data_profile.column_profiles:
            for cp in context.data_profile.column_profiles:
                if not cp.is_numeric:
                    return max(1, cp.cardinality)
        return max(1, len(context.data)) if context.data else 1

    def _n_series(self, context: RuntimeContext) -> int:
        if context.column_roles:
            return max(1, sum(1 for r in context.column_roles.roles if r.role == "metric"))
        _NUMERIC = frozenset({
            "TINYINT", "SMALLINT", "INTEGER", "INT", "BIGINT",
            "HUGEINT", "FLOAT", "DOUBLE", "DECIMAL", "NUMERIC", "REAL",
        })
        if context.schema:
            return max(1, sum(
                1 for col in context.schema
                if col.type.upper().split("(")[0].strip() in _NUMERIC
                and not col.name.lower().endswith(("_id", "_key"))
                and col.name.lower() != "id"
            ))
        return 1

    def _elimination_rule(self, chart_type: str, context: RuntimeContext) -> str | None:
        if context.constraint_report:
            for v in context.constraint_report.eliminated:
                if v.chart_type == chart_type:
                    return v.rule_name
        return "unknown"
