from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..contracts.constraint import ConstraintReport, ConstraintViolation
from ..parser.ast_helpers import get_column_names_from_select, has_group_by
from ..semantic.fuzzy_match import match_column_name
from ..utils.sqlviz_logging import get_logger
from ..utils.yaml_loader import yaml_loader

_log = get_logger("constraint_engine")

if TYPE_CHECKING:
    from ..context import RuntimeContext

_NUMERIC_TYPES = frozenset({
    "TINYINT", "SMALLINT", "INTEGER", "INT", "BIGINT",
    "HUGEINT", "FLOAT", "DOUBLE", "DECIMAL", "NUMERIC", "REAL",
})

_TEMPORAL_TYPES = frozenset({
    "DATE", "TIMESTAMP", "TIMESTAMP_TZ", "TIMESTAMPTZ", "TIME", "INTERVAL",
})

_ID_SUFFIXES = ("_id", "_key")
_ID_EXACT = frozenset({"id", "pk"})

_BIN_INDICATORS = frozenset({
    "bucket", "bin", "rango", "range", "interval", "bracket",
    "cubo", "canasta", "tramo",
})

_PIE_CARDINALITY_THRESHOLD = 7
_HAS_CASE_WHEN_INDEX = 16   # feature_vector_v0.yaml dim 16


def _is_id_col(name: str) -> bool:
    nl = name.lower()
    if nl in _ID_EXACT:
        return True
    return any(nl.endswith(s) for s in _ID_SUFFIXES)


class ConstraintEngine:
    """
    Hard rules eliminate chart candidates that are definitively incorrect.
    Soft rules (from constraint_rules.yaml) penalize without eliminating.
    All decisions are recorded in ConstraintReport for the ExplanationEngine.

    Hard rules (6):
    1. kpi_single_row      — kpi requires exactly 1 data row
    2. line_no_temporal    — line requires at least 1 temporal column
    3. pie_high_cardinality — pie rejected when categorical cardinality > 7
    4. scatter_insufficient_metrics — scatter requires ≥ 2 non-id numeric columns
    5. histogram_grouped_no_bins — histogram requires non-aggregated data
    6. funnel_no_stage_semantics — funnel requires CASE WHEN (future-proof)
    """

    def __init__(self) -> None:
        self._soft_rules: list[dict[str, Any]] | None = None
        self._dictionary: dict[str, Any] | None = None

    @property
    def soft_rules(self) -> list[dict[str, Any]]:
        if self._soft_rules is None:
            config = yaml_loader.load("constraint_rules.yaml")
            self._soft_rules = config.get("soft_rules", [])
        return self._soft_rules

    @property
    def dictionary(self) -> dict[str, Any]:
        if self._dictionary is None:
            self._dictionary = yaml_loader.load("semantic_dictionary.yaml")
        return self._dictionary

    def run(self, context: RuntimeContext) -> RuntimeContext:
        try:
            context.constraint_report = self._evaluate(context)
        except Exception as e:
            _log.warning("%s", e, extra={"trace_id": context.trace_id})
            context.errors.append(f"ConstraintEngine: {e}")
        return context

    def _evaluate(self, context: RuntimeContext) -> ConstraintReport:
        eliminated: list[ConstraintViolation] = []
        penalized: list[ConstraintViolation] = []
        rules_checked = 0

        chart_types = {c.chart_type for c in context.chart_candidates}

        # ── Rule 1: KPI requires single row ────────────────────────────────
        rules_checked += 1
        if "kpi" in chart_types:
            row_count = (
                context.data_profile.row_count
                if context.data_profile
                else len(context.data)
            )
            if row_count > 1:
                eliminated.append(ConstraintViolation(
                    chart_type="kpi",
                    rule_name="kpi_single_row",
                    rule_type="hard",
                    reason=f"kpi requires exactly 1 data row; got {row_count}",
                ))

        # ── Rule 2: Line requires temporal column ───────────────────────────
        rules_checked += 1
        if "line" in chart_types:
            if not self._has_temporal_column(context):
                eliminated.append(ConstraintViolation(
                    chart_type="line",
                    rule_name="line_no_temporal",
                    rule_type="hard",
                    reason=(
                        "line requires at least one temporal column"
                        " (DATE/TIMESTAMP type or temporal name)"
                    ),
                ))

        # ── Rule 3: Pie rejected for high cardinality ───────────────────────
        rules_checked += 1
        if "pie" in chart_types:
            cat_cardinality = self._categorical_cardinality(context)
            if cat_cardinality is not None and cat_cardinality > _PIE_CARDINALITY_THRESHOLD:
                eliminated.append(ConstraintViolation(
                    chart_type="pie",
                    rule_name="pie_high_cardinality",
                    rule_type="hard",
                    reason=(
                        f"pie requires ≤{_PIE_CARDINALITY_THRESHOLD} distinct categories; "
                        f"detected {cat_cardinality}"
                    ),
                ))

        # ── Rule 4: Scatter requires ≥ 2 non-id numeric columns ─────────────
        rules_checked += 1
        if "scatter" in chart_types:
            if self._count_metric_columns(context) < 2:
                eliminated.append(ConstraintViolation(
                    chart_type="scatter",
                    rule_name="scatter_insufficient_metrics",
                    rule_type="hard",
                    reason="scatter requires ≥ 2 non-id numeric columns",
                ))

        # ── Rule 5: Histogram requires non-aggregated data ──────────────────
        rules_checked += 1
        if "histogram" in chart_types:
            has_gb = has_group_by(context.ast) if context.ast is not None else False
            if has_gb and not self._has_bin_column(context):
                eliminated.append(ConstraintViolation(
                    chart_type="histogram",
                    rule_name="histogram_grouped_no_bins",
                    rule_type="hard",
                    reason=(
                        "histogram requires raw un-aggregated data;"
                        " GROUP BY detected without explicit bin column"
                    ),
                ))

        # ── Rule 6: Funnel requires CASE WHEN stage semantics (future-proof) ─
        rules_checked += 1
        if "funnel" in chart_types:
            fv = context.feature_vector
            has_case_when = (
                len(fv) > _HAS_CASE_WHEN_INDEX and fv[_HAS_CASE_WHEN_INDEX] > 0
            )
            if not has_case_when:
                eliminated.append(ConstraintViolation(
                    chart_type="funnel",
                    rule_name="funnel_no_stage_semantics",
                    rule_type="hard",
                    reason="funnel requires CASE WHEN stage classification in SQL",
                ))

        # ── Soft rules from YAML ────────────────────────────────────────────
        for soft_rule in self.soft_rules:
            rules_checked += 1
            target = soft_rule.get("chart_type", "")
            if target in chart_types:
                condition = soft_rule.get("condition", {})
                if self._check_soft_condition(condition, context):
                    penalized.append(ConstraintViolation(
                        chart_type=target,
                        rule_name=soft_rule.get("name", "unknown_soft"),
                        rule_type="soft",
                        reason=soft_rule.get("reason", ""),
                        penalty=float(soft_rule.get("penalty", 0.0)),
                    ))

        # ── Update winner if it was eliminated ──────────────────────────────
        eliminated_types = {v.chart_type for v in eliminated}
        if context.chart_winner in eliminated_types:
            remaining = [
                c for c in context.chart_candidates
                if c.chart_type not in eliminated_types
            ]
            old_winner = context.chart_winner
            triggering_rule = next(
                (v.rule_name for v in eliminated if v.chart_type == old_winner), "unknown"
            )
            if remaining:
                best = remaining[0]
                context.chart_winner = best.chart_type
                context.chart_raw_score = best.final_score
                context.chart_normalized_score = best.normalized_score
            else:
                context.chart_winner = "table"
            context.fallback_applied = True
            context.fallback_reason = (
                f"ConstraintEngine: {old_winner} eliminated by {triggering_rule}"
            )

        return ConstraintReport(
            eliminated=eliminated,
            penalized=penalized,
            rules_checked=rules_checked,
        )

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _has_temporal_column(self, context: RuntimeContext) -> bool:
        # Use column_roles when populated from actual schema columns
        if context.column_roles is not None and context.column_roles.roles:
            return any(r.role == "time" for r in context.column_roles.roles)
        # Fallback: check schema directly
        for col in context.schema:
            norm_type = col.type.upper().split("(")[0].strip()
            if norm_type in _TEMPORAL_TYPES:
                return True
            if match_column_name(col.name, self.dictionary) == "TEMPORAL_DIMENSION":
                return True
        # Final fallback: check column names from AST SELECT list when schema is absent
        if not context.schema and context.ast is not None:
            for col_name in get_column_names_from_select(context.ast):
                if match_column_name(col_name, self.dictionary) == "TEMPORAL_DIMENSION":
                    return True
        return False

    def _categorical_cardinality(self, context: RuntimeContext) -> int | None:
        if context.data_profile and context.data_profile.column_profiles:
            for cp in context.data_profile.column_profiles:
                if not cp.is_numeric:
                    return cp.cardinality
        # Fallback: count distinct values in data for first non-numeric column
        for col in context.schema:
            norm_type = col.type.upper().split("(")[0].strip()
            if norm_type not in _NUMERIC_TYPES and context.data:
                return len({row.get(col.name) for row in context.data})
        return None

    def _count_metric_columns(self, context: RuntimeContext) -> int:
        if context.column_roles is not None:
            return sum(1 for r in context.column_roles.roles if r.role == "metric")
        # Fallback: count non-id numeric columns from schema
        return sum(
            1
            for col in context.schema
            if col.type.upper().split("(")[0].strip() in _NUMERIC_TYPES
            and not _is_id_col(col.name)
        )

    def _has_bin_column(self, context: RuntimeContext) -> bool:
        return any(
            indicator in col.name.lower()
            for col in context.schema
            for indicator in _BIN_INDICATORS
        )

    def _check_soft_condition(self, condition: dict[str, Any], context: RuntimeContext) -> bool:
        cond_type = condition.get("type")
        if cond_type == "cardinality_range":
            lo = condition.get("min", 0)
            hi = condition.get("max", 9999)
            card = self._categorical_cardinality(context)
            if card is None:
                return False
            return bool(lo <= card <= hi)
        return False
