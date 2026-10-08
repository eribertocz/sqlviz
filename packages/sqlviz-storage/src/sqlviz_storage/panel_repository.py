"""Panel reads and atomic updates on an independent project cursor."""

from __future__ import annotations

from typing import Any

import duckdb
from sqlviz_core.models.panel_presentation import PresentationField, normalize_presentation_value
from sqlviz_core.models.panels import Panel, PanelChanges, validate_panel_changes

from sqlviz_storage.dashboard_repository import DashboardRepository
from sqlviz_storage.timestamps import modification_timestamp
from sqlviz_storage.transactions import project_transaction

_SELECT = (
    "SELECT id, dashboard_id, name, sql_content, sort_order, created_at, updated_at,"
    " fingerprint, inferred_chart_type, selected_chart_type, chart_user_override,"
    " inferred_col_span, selected_col_span, col_span_user_override,"
    " inferred_height_px, selected_height_px, height_user_override,"
    " view_title, view_x_label, view_y_label FROM panels"
)

_PRESENTATION_COLUMNS: dict[PresentationField, str] = {
    "title": "view_title", "x_label": "view_x_label", "y_label": "view_y_label",
}


def _from_row(row: tuple[Any, ...]) -> Panel:
    return Panel(
        id=row[0], dashboard_id=row[1], name=row[2],
        sql_content=row[3] if row[3] is not None else "",
        sort_order=row[4], created_at=row[5], updated_at=row[6],
        fingerprint=row[7], inferred_chart_type=row[8], selected_chart_type=row[9],
        chart_user_override=row[10], inferred_col_span=row[11], selected_col_span=row[12],
        col_span_user_override=row[13], inferred_height_px=row[14], selected_height_px=row[15],
        height_user_override=row[16],
        view_title=row[17], view_x_label=row[18], view_y_label=row[19],
    )


class PanelNotFound(Exception):
    """The panel does not exist in this transaction's snapshot."""


class PanelWriteConflict(Exception):
    """The complete patch was rolled back; the caller may refresh and retry."""


class PanelRepository:
    def __init__(self, db: duckdb.DuckDBPyConnection) -> None:
        self._db = db

    def get(self, panel_id: str) -> Panel:
        row = self._db.execute(f"{_SELECT} WHERE id = ?", [panel_id]).fetchone()
        if row is None:
            raise PanelNotFound("Panel not found")
        return _from_row(row)

    def list(self, dashboard_id: str | None = None) -> list[Panel]:
        if dashboard_id is None:
            rows = self._db.execute(f"{_SELECT} ORDER BY sort_order, created_at").fetchall()
        else:
            rows = self._db.execute(
                f"{_SELECT} WHERE dashboard_id = ? ORDER BY sort_order, created_at", [dashboard_id],
            ).fetchall()
        return [_from_row(row) for row in rows]

    def update(self, panel_id: str, changes: PanelChanges) -> Panel:
        validate_panel_changes(changes)
        if not changes:
            return self.get(panel_id)
        return self._update_fields(panel_id, dict(changes))

    def set_presentation(
        self, panel_id: str, field: PresentationField, value: str | None,
    ) -> Panel:
        normalized = normalize_presentation_value(field, value)
        return self._update_fields(panel_id, {_PRESENTATION_COLUMNS[field]: normalized})

    def _update_fields(self, panel_id: str, changes: dict[str, object]) -> Panel:
        """Only validated public operations supply column names to this private writer."""
        try:
            with project_transaction(self._db):
                previous = self.get(panel_id)
                # Reject legacy orphans. Repository deletions fence updated_at
                # before DELETE; a plain DELETE alone is not a reliable fence.
                DashboardRepository(self._db).get(previous.dashboard_id)
                values = changes.copy()
                values["updated_at"] = modification_timestamp(previous.updated_at)
                assignments = ", ".join(f"{column} = ?" for column in values)
                self._db.execute(
                    f"UPDATE panels SET {assignments} WHERE id = ?", [*values.values(), panel_id],
                )
                result = self.get(panel_id)
        except (duckdb.TransactionException, duckdb.ConstraintException) as exc:
            raise PanelWriteConflict("Panel write conflicted; refresh and retry") from exc
        return result

    def delete(self, panel_id: str) -> None:
        """Fence the panel with a real UPDATE before deleting it atomically."""
        try:
            with project_transaction(self._db):
                previous = self.get(panel_id)
                self._db.execute(
                    "UPDATE panels SET updated_at = ? WHERE id = ?",
                    [modification_timestamp(previous.updated_at), panel_id],
                )
                self._db.execute("DELETE FROM panels WHERE id = ?", [panel_id])
        except (duckdb.TransactionException, duckdb.ConstraintException) as exc:
            raise PanelWriteConflict("Panel write conflicted; refresh and retry") from exc
