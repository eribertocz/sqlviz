"""Transactional writes to a dashboard aggregate in the project database.

Each operation owns its transaction on an independent cursor. Child creation
must use dashboard_write too: checking the parent in a separate autocommit
statement is insufficient when deletion can run concurrently.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import duckdb

from sqlviz_storage.transactions import project_transaction


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
            now = datetime.now(timezone.utc)
            modified_at = now.isoformat(timespec="microseconds")
            if modified_at == row[0]:
                modified_at = (now + timedelta(microseconds=1)).isoformat(timespec="microseconds")
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
    """Persistence of the deletion operation; no HTTP or session dependencies."""

    def __init__(self, db: duckdb.DuckDBPyConnection) -> None:
        self._db = db

    def delete(self, dashboard_id: str) -> DashboardDeletion:
        with dashboard_write(self._db, dashboard_id):
            self._db.execute("DELETE FROM panels WHERE dashboard_id = ?", [dashboard_id])
            tokens = self._db.execute(
                "DELETE FROM shares WHERE dashboard_id = ? RETURNING token", [dashboard_id],
            ).fetchall()
            self._db.execute("DELETE FROM filter_memory WHERE dashboard_id = ?", [dashboard_id])
            self._db.execute("DELETE FROM dashboards WHERE id = ?", [dashboard_id])
        # Reaching this line means COMMIT succeeded. No deletion result escapes
        # from a rolled-back transaction.
        return DashboardDeletion(tuple(str(row[0]) for row in tokens))
