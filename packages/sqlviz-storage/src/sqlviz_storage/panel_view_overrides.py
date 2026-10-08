"""Panel presentation overrides — editable title + axis labels.

Single responsibility: user-authored *presentation* text for a panel (its
title and X/Y axis labels). This is deliberately separate from the inference
OverrideSystem (chart type / span / height), which corrects *inferred* values
and feeds the brain. Presentation overrides never touch inference — they are
overlaid onto the render contract at the API layer, so admin and shared viewers
render them identically.

Storage: three nullable columns on `panels` (NULL = use the inferred default).
"""

from __future__ import annotations

from typing import Any, cast

import duckdb
from sqlviz_core.models.panel_presentation import PresentationField

from sqlviz_storage.panel_repository import PanelRepository


def set_view_override(
    conn: duckdb.DuckDBPyConnection,
    panel_id: str,
    field: str,
    value: str | None,
) -> None:
    """Set (or clear, with '' / None) one presentation field on a panel."""
    PanelRepository(conn).set_presentation(panel_id, cast(PresentationField, field), value)


def get_view_overrides(conn: duckdb.DuckDBPyConnection, panel_id: str) -> dict[str, str | None]:
    """Return {title, x_label, y_label} for a panel (values may be None)."""
    row = conn.execute(
        "SELECT view_title, view_x_label, view_y_label FROM panels WHERE id = ?",
        [panel_id],
    ).fetchone()
    if row is None:
        return {"title": None, "x_label": None, "y_label": None}
    return {"title": row[0], "x_label": row[1], "y_label": row[2]}


def apply_view_overrides(
    inference_dict: dict[str, Any],
    overrides: dict[str, str | None],
) -> dict[str, Any]:
    """Overlay presentation overrides onto an inference_result dict in place.

    - `title` replaces inference_result.title.
    - `x_label` / `y_label` are written onto visual_spec (read by the renderer,
      which falls back to the field name when they are null).
    """
    if overrides.get("title"):
        inference_dict["title"] = overrides["title"]
    spec = inference_dict.get("visual_spec")
    if isinstance(spec, dict):
        spec["x_label"] = overrides.get("x_label")
        spec["y_label"] = overrides.get("y_label")
    return inference_dict
