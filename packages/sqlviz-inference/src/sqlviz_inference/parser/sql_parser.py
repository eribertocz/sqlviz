from __future__ import annotations

import sqlglot.expressions as exp

from ..context import RuntimeContext
from ..utils.sqlviz_logging import get_logger
from .ast_helpers import (
    count_group_by_columns,
    count_select_columns,
    has_aggregation,
    has_avg,
    has_case_when,
    has_count,
    has_cte,
    has_distinct,
    has_group_by,
    has_join,
    has_limit,
    has_order_by,
    has_order_by_desc,
    has_partition_by,
    has_subquery,
    has_sum,
    has_where,
    has_window_function,
    parse_sql,
)
from .fingerprint import generate_fingerprint

_log = get_logger("sql_parser")


class SQLParser:
    """
    Parses SQL and extracts AST, fingerprint, and SQL features (dims 0-17).
    Fails gracefully — unparseable SQL yields UNKNOWN fingerprint and zero
    feature vector with a logged error.
    """

    def run(self, context: RuntimeContext) -> RuntimeContext:
        try:
            return self._parse(context)
        except Exception as e:
            _log.warning("%s", e, extra={"trace_id": context.trace_id})
            return context.with_error("SQLParser", str(e))

    def _parse(self, context: RuntimeContext) -> RuntimeContext:
        sql = context.sql.strip()
        ast = parse_sql(sql)

        if ast is None:
            context.fingerprint = "UNKNOWN"
            context.sql_features = [0.0] * 18
            return context.with_error("SQLParser", "unparseable SQL")

        context.ast = ast
        context.fingerprint = generate_fingerprint(ast)
        context.sql_features = self._extract_sql_features(ast)

        fv = context.feature_vector
        for i, val in enumerate(context.sql_features):
            fv[i] = val
        context.feature_vector = fv

        return context

    def _extract_sql_features(self, ast: exp.Expression) -> list[float]:
        """Extract dims 0-17 of the feature vector. All values in [0.0, 1.0]."""
        group_count = count_group_by_columns(ast)
        select_count = count_select_columns(ast)

        return [
            1.0 if has_group_by(ast) else 0.0,        # dim 0
            1.0 if has_order_by(ast) else 0.0,         # dim 1
            1.0 if has_order_by_desc(ast) else 0.0,    # dim 2
            1.0 if has_limit(ast) else 0.0,            # dim 3
            1.0 if has_aggregation(ast) else 0.0,      # dim 4
            1.0 if has_sum(ast) else 0.0,              # dim 5
            1.0 if has_count(ast) else 0.0,            # dim 6
            1.0 if has_avg(ast) else 0.0,              # dim 7
            1.0 if has_window_function(ast) else 0.0,  # dim 8
            1.0 if has_cte(ast) else 0.0,              # dim 9
            1.0 if has_join(ast) else 0.0,             # dim 10
            1.0 if has_where(ast) else 0.0,            # dim 11
            min(group_count / 5.0, 1.0),               # dim 12
            min(select_count / 10.0, 1.0),             # dim 13
            1.0 if has_subquery(ast) else 0.0,         # dim 14
            1.0 if has_partition_by(ast) else 0.0,     # dim 15
            1.0 if has_case_when(ast) else 0.0,        # dim 16
            1.0 if has_distinct(ast) else 0.0,         # dim 17
        ]
