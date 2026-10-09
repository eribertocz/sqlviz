"""Transactional writes to a dashboard aggregate in the project database.

Each operation owns its transaction on an independent cursor. Child creation
must use dashboard_write too: checking the parent in a separate autocommit
statement is insufficient when deletion can run concurrently.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

import duckdb
from sqlviz_core.models.dashboards import Dashboard, DashboardChanges, normalize_dashboard_changes

from sqlviz_storage.folder_repository import FolderRepository
from sqlviz_storage.timestamps import modification_timestamp
from sqlviz_storage.transactions import project_transaction

_SELECT = (
    "SELECT id, name, folder_id, connection_id, sort_order, created_at, updated_at,"
    " dashboard_hint, dashboard_domain, description, sql_content, last_run_at, last_run_sql "
    "FROM dashboards"
)


def _from_row(row: tuple[Any, ...]) -> Dashboard:
    return Dashboard(
        id=row[0], name=row[1], folder_id=row[2], connection_id=row[3],
        sort_order=row[4], created_at=row[5], updated_at=row[6],
        dashboard_hint=row[7], dashboard_domain=row[8], description=row[9],
        sql_content=row[10] if row[10] is not None else "",
        last_run_at=row[11], last_run_sql=row[12],
    )


class DashboardNotFound(Exception):
    """The parent does not exist in this transaction's snapshot."""


class DashboardWriteConflict(Exception):
    """The whole write was rolled back; the caller may refresh and retry."""


@contextmanager
def dashboard_write(db: duckdb.DuckDBPyConnection, dashboard_id: str) -> Iterator[None]:
    """Validate and fence the parent, then commit all writes or roll them back.

    Touching the parent's modification timestamp establishes a DuckDB write
    conflict with competing creation/deletion of its children, without
    serializing unrelated dashboards. Successful child creation also counts as
    a modification of its dashboard. A no-op update is not a reliable fence.
    This context must not be nested inside another transaction.
    """
    try:
        with project_transaction(db):
            row = db.execute(
                "SELECT updated_at FROM dashboards WHERE id = ?",
                [dashboard_id],
            ).fetchone()
            if row is None:
                raise DashboardNotFound("Dashboard not found")
            modified_at = modification_timestamp(row[0])
            db.execute(
                "UPDATE dashboards SET updated_at = ? WHERE id = ?", [modified_at, dashboard_id],
            )
            yield
    except (duckdb.TransactionException, duckdb.ConstraintException) as exc:
        raise DashboardWriteConflict("Dashboard write conflicted; refresh and retry") from exc


@dataclass(frozen=True)
class DashboardDeletion:
    # Credentials are used only for post-commit session revocation, never logs.
    share_tokens: tuple[str, ...] = field(repr=False)


class DashboardRepository:
    """Dashboard reads and atomic mutations; no HTTP or session dependencies."""

    def __init__(self, db: duckdb.DuckDBPyConnection) -> None:
        self._db = db

    def get(self, dashboard_id: str) -> Dashboard:
        row = self._db.execute(f"{_SELECT} WHERE id = ?", [dashboard_id]).fetchone()
        if row is None:
            raise DashboardNotFound("Dashboard not found")
        return _from_row(row)

    def list(self) -> list[Dashboard]:
        rows = self._db.execute(f"{_SELECT} ORDER BY sort_order, created_at").fetchall()
        return [_from_row(row) for row in rows]

    def update(self, dashboard_id: str, changes: DashboardChanges) -> Dashboard:
        normalized = normalize_dashboard_changes(changes)
        if not normalized:
            return self.get(dashboard_id)
        # Placement shares the folder-tree fence; all other fields still get
        # their own transaction without contending on unrelated folder changes.
        transaction = (
            FolderRepository(self._db).dashboard_placement(normalized["folder_id"])
            if "folder_id" in normalized else project_transaction(self._db)
        )
        try:
            with transaction:
                previous = self.get(dashboard_id)
                values: dict[str, object] = dict(normalized)
                values["updated_at"] = modification_timestamp(previous.updated_at)
                # Field names are whitelisted by core; values are always bound.
                assignments = ", ".join(f"{column} = ?" for column in values)
                self._db.execute(
                    f"UPDATE dashboards SET {assignments} WHERE id = ?",
                    [*values.values(), dashboard_id],
                )
                result = self.get(dashboard_id)
        except (duckdb.TransactionException, duckdb.ConstraintException) as exc:
            raise DashboardWriteConflict("Dashboard write conflicted; refresh and retry") from exc
        return result

    def delete(self, dashboard_id: str) -> DashboardDeletion:
        with dashboard_write(self._db, dashboard_id):
            # UPDATE vs DELETE alone does not reliably conflict. Fence the same
            # timestamp used by panel editing before removing any owned rows.
            modified_at = modification_timestamp("")
            alternate = modification_timestamp(modified_at)
            self._db.execute(
                "UPDATE panels SET updated_at = CASE WHEN updated_at = ? THEN ? ELSE ? END "
                "WHERE dashboard_id = ?", [modified_at, alternate, modified_at, dashboard_id],
            )
            self._db.execute("DELETE FROM panels WHERE dashboard_id = ?", [dashboard_id])
            self._db.execute(
                "DELETE FROM dashboard_sql_scripts WHERE dashboard_id = ?", [dashboard_id],
            )
            tokens = self._db.execute(
                "DELETE FROM shares WHERE dashboard_id = ? RETURNING token", [dashboard_id],
            ).fetchall()
            self._db.execute("DELETE FROM filter_memory WHERE dashboard_id = ?", [dashboard_id])
            self._db.execute("DELETE FROM dashboards WHERE id = ?", [dashboard_id])
        # Reaching this line means COMMIT succeeded. No deletion result escapes
        # from a rolled-back transaction.
        return DashboardDeletion(tuple(str(row[0]) for row in tokens))
