from __future__ import annotations

from typing import Any

import sqlglot.expressions as exp

from ..context import RuntimeContext
from ..parser.ast_helpers import has_limit, has_order_by_desc

# Map semantic classes to human-readable metric names
METRIC_LABELS = {
    "METRIC_REVENUE": "Revenue",
    "METRIC_COUNT":   "Count",
    "METRIC_PROFIT":  "Profit",
}


class TitleEngine:
    """
    Generates a descriptive title for the panel.
    Uses the intent, the semantic classification of columns,
    and the SQL structure (aggregation, GROUP BY, LIMIT).
    """

    def run(self, context: RuntimeContext) -> RuntimeContext:
        try:
            return self._generate(context)
        except Exception as e:
            return context.with_error("TitleEngine", str(e))

    def _generate(self, context: RuntimeContext) -> RuntimeContext:
        if context.ast is None:
            context.title = ""
            context.title_confidence = 0.0
            return context

        semantic_classes: dict[str, str] = context.score_trace.get(
            "semantic", {}
        ).get("column_classes", {})

        metric_col, metric_label = self._find_metric(context, semantic_classes)
        dimension_col, dimension_label = self._find_dimension(context, semantic_classes)

        title = self._build_title(
            context, metric_col, metric_label, dimension_col, dimension_label
        )

        context.title = title
        context.title_confidence = 0.8 if metric_col else 0.4

        return context

    def _find_metric(
        self,
        context: RuntimeContext,
        semantic_classes: dict[str, str],
    ) -> tuple[str | None, str]:
        """Find the primary metric column and its label."""
        for col_name, sem_class in semantic_classes.items():
            if sem_class in METRIC_LABELS:
                return col_name, METRIC_LABELS[sem_class]

        # Fallback — find any aggregated column in SELECT
        select = context.ast.find(exp.Select)
        if select:
            for expr in select.expressions:
                if isinstance(expr, exp.AggFunc) or expr.find(exp.AggFunc):
                    name = expr.alias_or_name
                    humanized = self._humanize(name) or "Value"
                    return name, humanized

        return None, "Value"

    def _find_dimension(
        self,
        context: RuntimeContext,
        semantic_classes: dict[str, str],
    ) -> tuple[str | None, str]:
        """Find primary dimension from GROUP BY, preferring temporal columns (§16.18)."""
        group = context.ast.find(exp.Group)
        if not group:
            return None, ""

        # GROUP BY ALL (§16.19): derive dimension names from non-aggregated SELECT columns
        if group.args.get("all"):
            col_names = self._select_non_agg_column_names(context.ast)
        else:
            columns = list(group.find_all(exp.Column))
            if not columns:
                return None, ""
            col_names = [c.name for c in columns]

        if not col_names:
            return None, ""

        # Prefer temporal dimension when multiple columns present (§16.18)
        for col in col_names:
            if semantic_classes.get(col) == "TEMPORAL_DIMENSION":
                return col, self._humanize(col)

        return col_names[0], self._humanize(col_names[0])

    def _select_non_agg_column_names(self, ast: exp.Expression) -> list[str]:
        """Return names of non-aggregated SELECT expressions."""
        select = ast.find(exp.Select)
        if not select:
            return []
        names = []
        for expr in select.expressions:
            if not (isinstance(expr, exp.AggFunc) or expr.find(exp.AggFunc)):
                name = expr.alias_or_name
                if name:
                    names.append(name)
        return names

    def _build_title(
        self,
        context: RuntimeContext,
        metric_col: str | None,
        metric_label: str,
        dimension_col: str | None,
        dimension_label: str,
    ) -> str:
        """Build the final title string based on intent."""
        intent = context.intent_winner
        ast = context.ast

        # KPI — single metric, no dimension
        if intent == "kpi" or not dimension_col:
            if context.chart_winner == "table":
                return self._table_title(context)
            return f"Total {metric_label}"

        # Ranking — has LIMIT + ORDER BY DESC
        if has_limit(ast) and has_order_by_desc(ast):
            limit_node = ast.find(exp.Limit)
            n = self._extract_limit_value(limit_node)
            entity = self._pluralize(dimension_label)
            return f"Top {n} {entity} by {metric_label}"

        # Trend, Comparison, Composition — default metric by dimension
        return f"{metric_label} by {dimension_label.lower()}"

    def _table_title(self, context: RuntimeContext) -> str:
        """Generate title for detail/table queries."""
        if context.ast:
            for t in context.ast.find_all(exp.Table):
                if t.name:
                    entity = self._humanize(t.name).rstrip("s")
                    return f"{entity} detail"
        return "Query results"

    def _extract_limit_value(self, limit_node: Any) -> str:
        """Extract the N value from LIMIT N."""
        if limit_node is None:
            return "N"
        try:
            return str(limit_node.expression.this)
        except Exception:
            return "N"

    def _humanize(self, name: str) -> str:
        """Convert snake_case to Title Case."""
        return name.replace("_", " ").title()

    def _pluralize(self, word: str) -> str:
        """Simple English pluralization."""
        word = word.lower()
        if word.endswith(("s", "sh", "ch", "x", "z")):
            return word + "es"
        if word.endswith("y") and len(word) > 1 and word[-2] not in "aeiou":
            return word[:-1] + "ies"
        return word + "s"
