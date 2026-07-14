from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlviz_core.models import ColumnSchema

from .visual_spec import VisualSpec

if TYPE_CHECKING:
    from ..context import RuntimeContext

_NUMERIC_TYPES = {
    "TINYINT", "SMALLINT", "INTEGER", "INT", "BIGINT",
    "HUGEINT", "FLOAT", "DOUBLE", "DECIMAL", "NUMERIC", "REAL",
}


class VisualSpecBuilder:
    """
    Builds VisualSpec from chart_winner + schema/data.

    Fase 0 interim: mirrors the column-selection convention that
    EChartsRenderer.svelte previously used at runtime ("first col = x,
    last col = y"), but makes it an explicit backend decision so the
    frontend can stop inferring anything.

    The WHAT-chart decision stays with ChartEngine.
    This builder only decides HOW to map columns onto chart axes.
    """

    def build(
        self,
        chart_winner: str,
        schema: list[ColumnSchema],
        data: list[dict[str, Any]],
    ) -> VisualSpec:
        col_names = [c.name for c in schema]
        if not col_names and data:
            col_names = list(data[0].keys())

        if not col_names:
            return VisualSpec(
                chart_type=chart_winner,
                x_field=None,
                y_fields=[],
                orientation="vertical",
                sort_order="none",
                color_field=None,
                stack=False,
                number_format="default",
                tooltip_fields=[],
            )

        if chart_winner == "scatter":
            return self._build_scatter(chart_winner, schema, col_names, data)

        if chart_winner == "table":
            return VisualSpec(
                chart_type="table",
                x_field=None,
                y_fields=col_names,
                orientation="none",
                sort_order="none",
                color_field=None,
                stack=False,
                number_format="default",
                tooltip_fields=[],
            )

        if chart_winner == "kpi":
            y_col = self._first_numeric_col(schema, col_names, data)
            return VisualSpec(
                chart_type="kpi",
                x_field=None,
                y_fields=[y_col],
                orientation="none",
                sort_order="none",
                color_field=None,
                stack=False,
                number_format="default",
                tooltip_fields=[y_col],
            )

        # line, bar, bar_horizontal, pie, histogram — shared convention:
        # x = first column, y = last column (mirrors V0.1 EChartsRenderer)
        x_field = col_names[0]
        y_field = col_names[-1]
        orientation = "horizontal" if chart_winner == "bar_horizontal" else "vertical"
        if chart_winner == "pie":
            orientation = "none"

        tooltip = [x_field, y_field] if x_field != y_field else [x_field]

        return VisualSpec(
            chart_type=chart_winner,
            x_field=x_field,
            y_fields=[y_field],
            orientation=orientation,
            sort_order="none",
            color_field=None,
            stack=False,
            number_format="default",
            tooltip_fields=tooltip,
        )

    def _build_scatter(
        self,
        chart_type: str,
        schema: list[ColumnSchema],
        col_names: list[str],
        data: list[dict[str, Any]],
    ) -> VisualSpec:
        # Mirrors V0.1 scatter logic: first two numeric columns
        numeric_cols = [
            c.name for c in schema
            if c.type.upper().split("(")[0] in _NUMERIC_TYPES
        ]
        if not numeric_cols and data:
            numeric_cols = [
                k for k, v in data[0].items()
                if isinstance(v, (int, float))
            ]

        x_field = numeric_cols[0] if len(numeric_cols) >= 1 else col_names[0]
        y_col = (
            numeric_cols[1] if len(numeric_cols) >= 2
            else (col_names[1] if len(col_names) > 1 else col_names[0])
        )

        return VisualSpec(
            chart_type="scatter",
            x_field=x_field,
            y_fields=[y_col],
            orientation="none",
            sort_order="none",
            color_field=None,
            stack=False,
            number_format="default",
            tooltip_fields=[x_field, y_col],
        )

    def _first_numeric_col(
        self,
        schema: list[ColumnSchema],
        col_names: list[str],
        data: list[dict[str, Any]],
    ) -> str:
        for c in schema:
            if c.type.upper().split("(")[0] in _NUMERIC_TYPES:
                return c.name
        if data:
            for k, v in data[0].items():
                if isinstance(v, (int, float)):
                    return k
        return col_names[0] if col_names else ""

    def run(self, context: RuntimeContext) -> RuntimeContext:
        try:
            context.visual_spec = self.build(
                context.chart_winner,
                context.schema,
                context.data,
            )
        except Exception as e:
            context = context.with_error("VisualSpecBuilder", str(e))
        return context
