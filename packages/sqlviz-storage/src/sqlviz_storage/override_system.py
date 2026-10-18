"""OverrideSystem — persists user corrections to the panels table.

Invariant (DOC10 §6.14):
  inferred_* stores the latest successful inference; overrides never modify it.
  selected_* holds the active value (= inferred until user overrides).
  *_user_override is NULL until the user explicitly corrects a field.

The module also writes the correction to brain.duckdb so that future
inference on the same SQL fingerprint returns the user-preferred chart.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime, timezone

import duckdb
from sqlviz_core.models.panel_overrides import valid_dimension, validate_override
from sqlviz_core.models.panels import Panel

from .brain_db import log_feedback_event, record_chart_override, record_layout_override
from .panel_repository import PanelNotFound, PanelRepository
from .transactions import project_transaction

_log = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def store_inference(
    conn: duckdb.DuckDBPyConnection,
    panel_id: str,
    fingerprint: str,
    chart_type: str,
    col_span: int,
    height_px: int,
    intent_type: str | None = None,
) -> None:
    """Write inferred values to panels after a successful execute.

    Writes inferred_* and initialises selected_* to the same value.
    Never overwrites existing user overrides (selected_* retains user_value
    if chart_user_override / *_user_override is already set).

    This is a metadata write primitive, not transaction ownership. When the
    inference was computed earlier, use inference_publication with its captured
    SQL/chart choice to guard this write and related classification atomically.

    intent_type (optional): result.intent_winner — stored in inferred_intent_type
    for use by DashboardClassifier.  Pass None (default) to skip the column
    (backwards-compatible with callers that don't supply it).
    """
    if intent_type is not None:
        conn.execute(
            """
            UPDATE panels SET
                fingerprint            = ?,
                inferred_chart_type    = ?,
                inferred_intent_type   = ?,
                inferred_col_span      = ?,
                inferred_height_px     = ?,
                selected_chart_type    = COALESCE(chart_user_override,    ?),
                selected_col_span      = COALESCE(col_span_user_override, ?),
                selected_height_px     = COALESCE(height_user_override,   ?),
                updated_at             = ?
            WHERE id = ?
            """,
            [
                fingerprint, chart_type, intent_type,
                col_span, height_px,
                chart_type, col_span, height_px,
                _now(), panel_id,
            ],
        )
    else:
        conn.execute(
            """
            UPDATE panels SET
                fingerprint         = ?,
                inferred_chart_type = ?,
                inferred_col_span   = ?,
                inferred_height_px  = ?,
                selected_chart_type = COALESCE(chart_user_override,    ?),
                selected_col_span   = COALESCE(col_span_user_override, ?),
                selected_height_px  = COALESCE(height_user_override,   ?),
                updated_at          = ?
            WHERE id = ?
            """,
            [
                fingerprint, chart_type,
                col_span, height_px,
                chart_type, col_span, height_px,
                _now(), panel_id,
            ],
        )


def clear_override(
    conn: duckdb.DuckDBPyConnection,
    panel_id: str,
    field_name: str,
) -> Panel:
    """Drop a user override, returning the field to whatever inference says.

    This is what "reset to auto" means: the override column goes back to NULL so
    the panel follows the engine again, including when new data makes the engine
    choose differently. Writing the currently-inferred value instead would
    freeze the panel at today's number while still looking automatic.

    inferred_* is untouched, and nothing is written to the brain — the user is
    withdrawing a correction, not making one.

    Raises:
        ValueError: Unknown field_name.
        LookupError: Panel not found.
    """
    try:
        return PanelRepository(conn).set_override(panel_id, field_name, None)
    except PanelNotFound as exc:
        raise LookupError("Panel not found") from exc


def apply_layout_overrides(
    inference_dict: dict[str, object],
    col_span: int | None,
    height_px: int | None,
) -> dict[str, object]:
    """Overlay persisted size overrides onto an inference_result dict.

    The size the user picked has to ride along on the inference_result, because
    that is the only thing the layout is composed from — both for the admin app
    and for a shared link. Without this the columns were written and then never
    read, so every re-run silently reverted to the inferred size.
    """
    if valid_dimension("col_span", col_span):
        inference_dict["col_span"] = col_span
    if valid_dimension("height_px", height_px):
        inference_dict["panel_height_px"] = height_px
    return inference_dict


def apply_override(
    conn: duckdb.DuckDBPyConnection,
    brain_conn: duckdb.DuckDBPyConnection | Callable[[], duckdb.DuckDBPyConnection],
    panel_id: str,
    field_name: str,
    user_value: str,
) -> Panel:
    """Save the authoritative project override, then attempt optional learning.

    Validation precedes every side effect. The repository commits the project
    update and confirmed snapshot before optional learning. Brain patterns and
    their event use a separate cursor/transaction;
    failure there is logged without falsely reporting a failed project save.
    There is no atomic transaction spanning the two database files.
    """
    value = validate_override(field_name, user_value)
    try:
        saved = PanelRepository(conn).set_override(panel_id, field_name, user_value)
    except PanelNotFound as exc:
        raise LookupError("Panel not found") from exc
    fingerprint = saved.fingerprint
    if not fingerprint or fingerprint == "UNKNOWN":
        return saved
    inferred = {
        "chart_type": saved.inferred_chart_type, "col_span": saved.inferred_col_span,
        "height_px": saved.inferred_height_px,
    }[field_name]
    try:
        brain = brain_conn() if callable(brain_conn) else brain_conn
        with brain.cursor() as learning:
            with project_transaction(learning):
                if field_name == "chart_type":
                    record_chart_override(
                        learning, fingerprint, str(inferred or value), str(value),
                    )
                else:
                    dimension = int(user_value)
                    record_layout_override(
                        learning, fingerprint,
                        dimension if field_name == "col_span" else None,
                        dimension if field_name == "height_px" else None,
                    )
                _log_event(
                    learning, fingerprint=fingerprint, field_name=field_name,
                    inferred_value=str(inferred) if inferred is not None else "",
                    user_value=str(value), panel_id=panel_id, dashboard_id=saved.dashboard_id,
                )
    except Exception:  # learning is optional; never hide a project write failure
        # Avoid logging raw SQL, data or database paths from an exception.
        _log.warning("Panel override saved; optional learning was not recorded")
    return saved


def _log_event(
    brain_conn: duckdb.DuckDBPyConnection,
    *,
    fingerprint: str,
    field_name: str,
    inferred_value: str,
    user_value: str,
    panel_id: str | None,
    dashboard_id: str | None,
) -> None:
    from sqlviz_inference.contracts.feedback import FeedbackEvent  # lazy import

    log_feedback_event(
        brain_conn,
        FeedbackEvent(
            fingerprint=fingerprint,
            field_name=field_name,
            inferred_value=inferred_value,
            user_value=user_value,
            panel_id=panel_id,
            dashboard_id=dashboard_id,
        ),
    )
