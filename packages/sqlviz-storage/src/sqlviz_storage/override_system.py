"""OverrideSystem — persists user corrections to the panels table.

Invariant (DOC10 §6.14):
  inferred_* fields are NEVER overwritten once set.
  selected_* holds the active value (= inferred until user overrides).
  *_user_override is NULL until the user explicitly corrects a field.

The module also writes the correction to brain.duckdb so that future
inference on the same SQL fingerprint returns the user-preferred chart.
"""

from __future__ import annotations

from datetime import datetime, timezone

import duckdb

from .brain_db import log_feedback_event, record_chart_override, record_layout_override

_VALID_FIELDS = frozenset({"chart_type", "col_span", "height_px"})


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


def apply_override(
    conn: duckdb.DuckDBPyConnection,
    brain_conn: duckdb.DuckDBPyConnection,
    panel_id: str,
    field_name: str,
    user_value: str,
) -> None:
    """Apply a user override for a single field on a panel.

    Updates selected_* and *_user_override.  Never touches inferred_*.
    Persists the pattern to brain.duckdb for future inference consultation.

    Args:
        conn:       Open .sqlviz project connection.
        brain_conn: Open brain.duckdb connection.
        panel_id:   The panel being corrected.
        field_name: "chart_type" | "col_span" | "height_px"
        user_value: The value the user wants (always passed as str; cast here).

    Raises:
        ValueError: Unknown field_name.
        LookupError: Panel not found.
    """
    if field_name not in _VALID_FIELDS:
        raise ValueError(f"Unknown override field: {field_name!r}")

    row = conn.execute(
        """
        SELECT fingerprint,
               inferred_chart_type, inferred_col_span, inferred_height_px,
               dashboard_id
        FROM panels WHERE id = ?
        """,
        [panel_id],
    ).fetchone()
    if row is None:
        raise LookupError(f"Panel not found: {panel_id!r}")

    fingerprint, inferred_chart, inferred_col, inferred_h, dashboard_id = row

    now = _now()

    if field_name == "chart_type":
        conn.execute(
            """
            UPDATE panels SET
                selected_chart_type = ?,
                chart_user_override = ?,
                updated_at          = ?
            WHERE id = ?
            """,
            [user_value, user_value, now, panel_id],
        )
        if fingerprint:
            record_chart_override(
                brain_conn,
                fingerprint,
                inferred_chart or user_value,
                user_value,
            )
            _log_event(
                brain_conn,
                fingerprint=fingerprint,
                field_name="chart_type",
                inferred_value=inferred_chart or user_value,
                user_value=user_value,
                panel_id=panel_id,
                dashboard_id=dashboard_id,
            )

    elif field_name == "col_span":
        v = int(user_value)
        conn.execute(
            """
            UPDATE panels SET
                selected_col_span      = ?,
                col_span_user_override = ?,
                updated_at             = ?
            WHERE id = ?
            """,
            [v, v, now, panel_id],
        )
        if fingerprint:
            record_layout_override(brain_conn, fingerprint, v, None)
            _log_event(
                brain_conn,
                fingerprint=fingerprint,
                field_name="col_span",
                inferred_value=str(inferred_col) if inferred_col is not None else "",
                user_value=str(v),
                panel_id=panel_id,
                dashboard_id=dashboard_id,
            )

    elif field_name == "height_px":
        v = int(user_value)
        conn.execute(
            """
            UPDATE panels SET
                selected_height_px   = ?,
                height_user_override = ?,
                updated_at           = ?
            WHERE id = ?
            """,
            [v, v, now, panel_id],
        )
        if fingerprint:
            record_layout_override(brain_conn, fingerprint, None, v)
            _log_event(
                brain_conn,
                fingerprint=fingerprint,
                field_name="height_px",
                inferred_value=str(inferred_h) if inferred_h is not None else "",
                user_value=str(v),
                panel_id=panel_id,
                dashboard_id=dashboard_id,
            )


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
