"""Basic panel editing policy, independent of transport and persistence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

MAX_PANEL_NAME_LENGTH = 256
MAX_PANEL_SQL_BYTES = 1024 * 1024


@dataclass(frozen=True)
class Panel:
    id: str
    dashboard_id: str
    name: str
    sql_content: str
    sort_order: int
    created_at: str
    updated_at: str
    fingerprint: str | None = None
    inferred_chart_type: str | None = None
    selected_chart_type: str | None = None
    chart_user_override: str | None = None
    inferred_col_span: int | None = None
    selected_col_span: int | None = None
    col_span_user_override: int | None = None
    inferred_height_px: int | None = None
    selected_height_px: int | None = None
    height_user_override: int | None = None
    view_title: str | None = None
    view_x_label: str | None = None
    view_y_label: str | None = None


class PanelChanges(TypedDict, total=False):
    name: str
    sql_content: str
    sort_order: int


def validate_panel_changes(changes: PanelChanges) -> None:
    """Reject the whole patch before writing; omission and empty SQL stay distinct."""
    if not changes.keys() <= {"name", "sql_content", "sort_order"}:
        raise ValueError("Unknown panel field")
    for key, value in changes.items():
        if value is None:
            raise ValueError(f"{key} must not be null")
        if key == "sort_order":
            if type(value) is not int or not -(2**31) <= value < 2**31:
                raise ValueError("sort_order must be a 32-bit integer")
            continue
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string")
        try:
            text_bytes = len(value.encode("utf-8"))
        except UnicodeEncodeError:
            raise ValueError(f"{key} must be valid UTF-8 text") from None
        if key == "name" and (not value.strip() or len(value) > MAX_PANEL_NAME_LENGTH):
            raise ValueError(
                f"name must contain text and be at most {MAX_PANEL_NAME_LENGTH} characters",
            )
        if key == "sql_content" and text_bytes > MAX_PANEL_SQL_BYTES:
            raise ValueError(f"sql_content must be at most {MAX_PANEL_SQL_BYTES} UTF-8 bytes")
