"""FeedbackEngine — session-to-session correction propagation (DOC10 §6.14).

Pipeline positions:
  run_consult(context) — after constraint, before readability
                         reads brain.duckdb; sets context.feedback_preferred
  run_apply(context)   — after scoring, before visual_spec_builder
                         no-op: preference is surfaced as suggestion, not forced
  run_persist(context) — step 16, after title
                         logs the inference event to feedback_events

All three methods are no-ops when context.brain_conn is None or when
the fingerprint is "UNKNOWN", ensuring the pipeline degrades gracefully
when brain.duckdb is unavailable.
"""

from __future__ import annotations

from sqlviz_inference.context import RuntimeContext
from sqlviz_inference.utils.sqlviz_logging import get_logger

_log = get_logger("feedback_engine")

_CHART_FIELD = "chart_type"


class FeedbackEngine:

    def run_consult(self, context: RuntimeContext) -> RuntimeContext:
        """Query brain.duckdb for a learned chart preference.

        Sets context.feedback_preferred to the user-preferred chart type if
        a correction for context.fingerprint exists in feedback_patterns.
        The preference is surfaced in the API response as feedback_preferred_chart
        and shown as a ★ suggestion in the Chart Selector — never auto-applied.
        """
        brain = context.brain_conn
        if brain is None or context.fingerprint == "UNKNOWN":
            return context
        try:
            row = brain.execute(
                """
                SELECT user_value FROM feedback_patterns
                WHERE fingerprint = ? AND field_name = 'chart_type'
                """,
                [context.fingerprint],
            ).fetchone()
            if row is not None:
                context.feedback_preferred = row[0]
        except Exception as e:  # noqa: BLE001
            _log.warning("run_consult: %s", e, extra={"trace_id": context.trace_id})
        return context

    def run_apply(self, context: RuntimeContext) -> RuntimeContext:
        """No-op: the engine inference is never overridden automatically.

        The preference in context.feedback_preferred is exposed via
        InferenceResult.feedback_preferred_chart so the Chart Selector can
        display it as a ★ suggestion. The user must choose explicitly.
        """
        return context

    def run_persist(self, context: RuntimeContext) -> RuntimeContext:
        """Log the completed inference event to feedback_events (step 16).

        Records what the engine inferred so the audit trail in brain.duckdb
        is complete. Skips when brain_conn is None or fingerprint is UNKNOWN.
        """
        brain = context.brain_conn
        if brain is None or context.fingerprint == "UNKNOWN":
            return context
        try:
            import uuid
            from datetime import datetime, timezone

            brain.execute(
                """
                INSERT INTO feedback_events
                    (id, fingerprint, field_name, inferred_value, user_value,
                     panel_id, dashboard_id, created_at)
                VALUES (?, ?, 'chart_type', ?, ?, NULL, NULL, ?)
                """,
                [
                    str(uuid.uuid4()),
                    context.fingerprint,
                    context.chart_winner,
                    context.chart_winner,
                    datetime.now(timezone.utc).isoformat(timespec="seconds"),
                ],
            )
        except Exception as e:  # noqa: BLE001
            _log.warning("run_persist: %s", e, extra={"trace_id": context.trace_id})
        return context
