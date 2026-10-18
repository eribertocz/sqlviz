"""Conditional draft writes; no parsing, inference or panel mutations.

read/write own their transactions. Authorization belongs to the caller.
"""

from __future__ import annotations

import re

import duckdb
from sqlviz_core.models.sql_script import validate_sql_script

from sqlviz_storage.dashboard_repository import (
    DashboardNotFound,
    DashboardWriteConflict,
    dashboard_write,
)
from sqlviz_storage.sql_draft_revision import (
    SqlDraftMetadataError,
    SqlDraftSnapshot,
    next_draft_generation,
    require_draft_generation,
)
from sqlviz_storage.transactions import project_transaction


class SqlDraftWriteConflict(Exception):
    """The expected draft changed or a competing write won; nothing committed."""


class SqlDraftRepository:
    def __init__(self, db: duckdb.DuckDBPyConnection) -> None:
        self._db = db

    def _read(self, dashboard_id: str) -> SqlDraftSnapshot:
        row = self._db.execute(
            "SELECT sql_content, sql_draft_generation FROM dashboards WHERE id = ?",
            [dashboard_id],
        ).fetchone()
        if row is None:
            raise DashboardNotFound("Dashboard not found")
        source = row[0] if row[0] is not None else ""
        if not isinstance(source, str):
            raise SqlDraftMetadataError("Invalid stored SQL draft source")
        return SqlDraftSnapshot(dashboard_id, source, require_draft_generation(row[1]))

    def read(self, dashboard_id: str) -> SqlDraftSnapshot:
        with project_transaction(self._db):
            snapshot = self._read(dashboard_id)
        return snapshot

    def write(self, dashboard_id: str, expected_revision: str, source: str) -> SqlDraftSnapshot:
        if not isinstance(expected_revision, str) or not re.fullmatch(
            r"sql-draft-v1:[0-9a-f]{64}", expected_revision,
        ):
            raise ValueError("Expected a SQL draft revision")
        # Validate text/UTF-8 budget only: an unfinished or empty draft is valid.
        validate_sql_script(source)
        try:
            # Fence the shared parent before checking the version or writing text.
            # A conditional UPDATE alone is insufficient for all competing SQL
            # update plans; the existing aggregate fence owns rollback/commit.
            with dashboard_write(self._db, dashboard_id):
                previous = self._read(dashboard_id)
                if previous.revision != expected_revision:
                    raise SqlDraftWriteConflict("SQL draft changed; review before saving")
                generation = next_draft_generation(previous.generation)
                result = self._db.execute(
                    "UPDATE dashboards SET sql_content = ?, sql_draft_generation = ? "
                    "WHERE id = ? AND sql_draft_generation = ? AND COALESCE(sql_content, '') = ? "
                    "RETURNING id",
                    [source, generation, dashboard_id,
                     previous.generation, previous.source],
                ).fetchone()
                if result is None:
                    raise SqlDraftWriteConflict("SQL draft changed; review before saving")
                snapshot = self._read(dashboard_id)
        except DashboardWriteConflict as exc:
            raise SqlDraftWriteConflict(
                "SQL draft write conflicted; review before retrying"
            ) from exc
        return snapshot
