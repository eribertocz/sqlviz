from __future__ import annotations

import re

from sqlviz_core.models import ColumnSchema

from ..context import FilterControl, RuntimeContext
from ..utils.sqlviz_logging import get_logger

_log = get_logger("filter_engine")

VARIABLE_PATTERN = re.compile(r"\$(\w+)")

DATE_TYPES = {
    "DATE", "TIMESTAMP", "TIMESTAMP WITH TIME ZONE",
    "TIMESTAMP_S", "TIMESTAMP_MS", "TIMESTAMP_NS",
}
NUMERIC_TYPES = {
    "TINYINT", "SMALLINT", "INTEGER", "INT", "BIGINT",
    "HUGEINT", "FLOAT", "DOUBLE", "DECIMAL", "NUMERIC", "REAL",
}
BOOLEAN_TYPES = {"BOOLEAN", "BOOL"}


class FilterEngine:
    """
    Detects $variable placeholders in SQL and infers
    the appropriate control type for each one.

    Strategy:
    1. Find all $variable occurrences in the raw SQL
    2. For each variable, find the column it compares against
    3. Determine control type from column type + SQL operator
    """

    def run(self, context: RuntimeContext) -> RuntimeContext:
        try:
            return self._detect_filters(context)
        except Exception as e:
            _log.warning("%s", e, extra={"trace_id": context.trace_id})
            return context.with_error("FilterEngine", str(e))

    def _detect_filters(self, context: RuntimeContext) -> RuntimeContext:
        sql = context.sql
        variables = set(VARIABLE_PATTERN.findall(sql))

        if not variables:
            context.filter_controls = []
            return context

        schema_map: dict[str, ColumnSchema] = {
            col.name.lower(): col for col in context.schema
        }
        controls = []

        for var_name in variables:
            control = self._infer_control(var_name, sql, schema_map)
            if control:
                controls.append(control)

        context.filter_controls = controls
        return context

    def _infer_control(
        self,
        var_name: str,
        sql: str,
        schema_map: dict[str, ColumnSchema],
    ) -> FilterControl | None:
        column_name = self._find_associated_column(var_name, sql)
        if not column_name:
            return None

        column = schema_map.get(column_name.lower())
        column_type = column.type.upper().split("(")[0] if column else "VARCHAR"

        operator_context = self._get_operator_context(var_name, sql)

        control_type = self._classify_control(column_type, operator_context)

        return FilterControl(
            variable=var_name,
            label=self._humanize(column_name),
            control_type=control_type,
            column_name=column_name,
            column_type=column_type,
            scope="global",
        )

    def _find_associated_column(self, var_name: str, sql: str) -> str | None:
        """Find the column compared against $var_name."""
        # Pattern: column_name [operator] $var_name
        pattern = re.compile(
            r"(\w+)\s*(?:=|>=|<=|>|<|!=)\s*\$" + re.escape(var_name)
        )
        match = pattern.search(sql)
        if match:
            return match.group(1)

        # Pattern: $var_name [operator] column_name (reversed)
        pattern_reversed = re.compile(
            r"\$" + re.escape(var_name) + r"\s*(?:=|>=|<=|>|<|!=)\s*(\w+)"
        )
        match = pattern_reversed.search(sql)
        if match:
            return match.group(1)

        # Pattern: column = ANY($var)
        pattern_any = re.compile(
            r"(\w+)\s*=\s*ANY\(\$" + re.escape(var_name) + r"\)",
            re.IGNORECASE,
        )
        match = pattern_any.search(sql)
        if match:
            return match.group(1)

        # Pattern: column ILIKE ... $var
        pattern_like = re.compile(
            r"(\w+)\s+I?LIKE\s+.*\$" + re.escape(var_name),
            re.IGNORECASE,
        )
        match = pattern_like.search(sql)
        if match:
            return match.group(1)

        return None

    def _get_operator_context(self, var_name: str, sql: str) -> str:
        """Determine how the variable is used: equality | range_candidate | multi | search."""
        sql_upper = sql.upper()
        var_upper = f"${var_name}".upper()

        if f"ANY({var_upper})" in sql_upper or f"IN ({var_upper})" in sql_upper:
            return "multi"

        if "ILIKE" in sql_upper or "LIKE" in sql_upper:
            idx = sql_upper.find(var_upper)
            like_idx = sql_upper.find("LIKE")
            if idx != -1 and like_idx != -1 and abs(idx - like_idx) < 50:
                return "search"

        if ">=" in sql or "<=" in sql:
            return "range_candidate"

        return "equality"

    def _classify_control(self, column_type: str, operator_context: str) -> str:
        """
        Classify the control type based on column type and operator.

        §16.12: DATE and NUMERIC types always return their base control type
        ("date_picker" / "numeric") regardless of operator_context. Range
        detection (date_range_picker / range_slider) is handled exclusively
        by pair_range_filters when two same-column controls are present.
        """
        if column_type in BOOLEAN_TYPES:
            return "toggle"

        if column_type in DATE_TYPES:
            return "date_picker"

        if column_type in NUMERIC_TYPES:
            return "numeric"

        # VARCHAR / STRING types
        if operator_context == "multi":
            return "multiselect"
        if operator_context == "search":
            return "search"

        return "dropdown"

    def _humanize(self, name: str) -> str:
        """Convert snake_case to Title Case for display."""
        return name.replace("_", " ").title()
