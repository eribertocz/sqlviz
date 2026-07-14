"""FeedbackEngine — session-to-session correction propagation (DOC10 §6.14).

Pipeline positions:
  run_consult(context) — after constraint, before readability
                         reads brain.duckdb; sets context.feedback_override
  run_apply(context)   — after scoring, before visual_spec_builder
                         forces chart_winner when an override is known
  run_persist(context) — step 16, after title
                         logs the inference event to feedback_events

All three methods are no-ops when context.brain_conn is None or when
the fingerprint is "UNKNOWN", ensuring the pipeline degrades gracefully
when brain.duckdb is unavailable.
"""

from __future__ import annotations

from sqlviz_inference.context import RuntimeContext

_CHART_FIELD = "chart_type"


class FeedbackEngine:

    def run_consult(self, context: RuntimeContext) -> RuntimeContext:
        """Query brain.duckdb for a learned chart override.

        Sets context.feedback_override to the user-preferred chart type if
        a correction for context.fingerprint exists in feedback_patterns.
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
                context.feedback_override = row[0]
        except Exception:  # noqa: BLE001
            pass
        return context

    def run_apply(self, context: RuntimeContext) -> RuntimeContext:
        """Force chart_winner to the known override (if valid for this query).

        Guards against stale overrides by requiring the override chart type
        to appear among the current candidates.  If no candidates exist the
        override is applied unconditionally (graceful handling of edge cases).
        """
        override = context.feedback_override
        if override is None or override == context.chart_winner:
            return context

        candidate_types: set[str] = set()
        if context.scored_candidates:
            candidate_types |= {c.chart_type for c in context.scored_candidates}
        if context.chart_candidates:
            candidate_types |= {c.chart_type for c in context.chart_candidates}

        if not candidate_types or override in candidate_types:
            context.chart_winner = override
        return context

    def run_persist(self, context: RuntimeContext) -> RuntimeContext:
        """Log the completed inference event to feedback_events (step 16).

        Records what the system chose (or what the user previously chose via
        feedback_override) so the audit trail in brain.duckdb is complete.
        Skips when brain_conn is None or fingerprint is UNKNOWN.
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
        except Exception:  # noqa: BLE001
            pass
        return context
