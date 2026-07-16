from __future__ import annotations

import warnings
from typing import Any

from sqlviz_core.models import ColumnSchema
from sqlviz_core.version import __version__  # noqa: F401

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
    brain_conn: Any = None,
    chart_override: str | None = None,
) -> InferenceResult:
    """
    The single public function of the Inference Engine.

    Args:
        sql:        SQL query string to analyze
        data:       Optional — query result rows (list of dicts).
        schema:     Optional — column schema (list of ColumnSchema).
        brain_conn: Optional — open brain.duckdb connection for learned
                    override consultation (Fase E, DOC10 §6.14).

    Returns:
        InferenceResult — complete inference output
    """
    context = RuntimeContext(
        sql=sql,
        data=data or [],
        schema=schema or [],
        brain_conn=brain_conn,
        chart_override=chart_override,
    )
    context = _pipeline.run(context)
    return InferenceResult.from_context(context)
