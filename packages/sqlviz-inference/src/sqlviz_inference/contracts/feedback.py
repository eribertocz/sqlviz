from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FeedbackEvent:
    """
    A single user correction — persisted to brain.duckdb by FeedbackEngine
    (pipeline step 16). Fingerprint links the event to the SQL+data pattern
    so future similar queries can benefit from the correction.
    """

    fingerprint: str
    field_name: str       # "chart_type" | "col_span" | "height_px"
    inferred_value: str
    user_value: str
    panel_id: str | None = None
    dashboard_id: str | None = None
