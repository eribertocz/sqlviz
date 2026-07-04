from __future__ import annotations

import warnings

from sqlviz_core.models import ColumnSchema

from .context import RuntimeContext
from .pipeline import RuntimePipeline
from .result import InferenceResult
from .utils.startup_check import validate_rules_on_startup

_pipeline = RuntimePipeline()

_startup_errors = validate_rules_on_startup()
if _startup_errors:
    warnings.warn(
        "sqlviz-inference: rule validation errors on startup:\n"
        + "\n".join(_startup_errors),
        stacklevel=1,
    )


def infer(
    sql: str,
    data: list[dict[str, object]] | None = None,
    schema: list[ColumnSchema] | None = None,
) -> InferenceResult:
    """
    The single public function of the Inference Engine.

    Args:
        sql:    SQL query string to analyze
        data:   Optional — query result rows (list of dicts).
                If not provided, data statistics default to 0.0.
        schema: Optional — column schema (list of ColumnSchema or dicts).
                If not provided, column features default to 0.0.

    Returns:
        InferenceResult — complete inference output

    Example:
        result = infer(
            sql="SELECT month, SUM(revenue) FROM sales GROUP BY month",
        )
        assert result.chart_winner  == "line"
        assert result.intent_winner == "trend"
    """
    context = RuntimeContext(
        sql=sql,
        data=data or [],
        schema=schema or [],
    )
    context = _pipeline.run(context)
    return InferenceResult.from_context(context)
