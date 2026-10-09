"""Atomic script definitions and durable identity, without execution or HTTP.

The application injects native full-script parsing, never client-provided slices.
Each public method owns a transaction on an independent project cursor.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass

import duckdb
from sqlviz_core.models.panels import Panel
from sqlviz_core.models.sql_reconciliation import (
    ExistingSqlPanel,
    KeepSqlPanel,
    SqlIdentityDecision,
    SqlPanelUpdate,
    reconcile_sql_script,
)
from sqlviz_core.models.sql_script import (
    MAX_SQL_SCRIPT_STATEMENTS,
    SqlStatement,
    validate_sql_script,
)

from sqlviz_storage.dashboard_repository import DashboardRepository
from sqlviz_storage.panel_repository import PanelRepository
from sqlviz_storage.timestamps import modification_timestamp
from sqlviz_storage.transactions import project_transaction


@dataclass(frozen=True)
class SqlPanelBinding:
    panel_id: str
    start_offset: int
    end_offset: int


@dataclass(frozen=True)
class SqlScriptPublication:
    revision: int
    source: str
    bindings: tuple[SqlPanelBinding, ...]


@dataclass(frozen=True)
class SqlScriptSnapshot:
    dashboard_id: str
    revision: str
    draft_source: str
    panels: tuple[Panel, ...]
    # None means absent or incompatible with current panel IDs/SQL. An unrelated
    # presentation change does not invalidate explicit identity.
    publication: SqlScriptPublication | None


@dataclass(frozen=True)
class SqlScriptCommit:
    snapshot: SqlScriptSnapshot
    created_panels: tuple[tuple[str, str], ...]  # creation_key -> allocated panel_id


class SqlScriptWriteConflict(Exception):
    """Stale expected state or a competing write; no script mutation committed."""


class SqlScriptMetadataError(ValueError):
    """Stored script metadata is invalid; never turn it into guessed identity."""


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = dict(pairs)
    if len(result) != len(pairs):
        raise ValueError("Duplicate binding document key")
    return result


def _publication(
    row: tuple[int, str, str, str],
    panels: tuple[Panel, ...],
) -> SqlScriptPublication | None:
    """Validate stored source spans and explicit refs before exposing associations."""
    revision, source, encoded, _timestamp = row
    try:
        validate_sql_script(source)
        if type(revision) is not int or not 1 <= revision < 2**63:
            raise ValueError("Invalid script revision")
        if not isinstance(encoded, str) or len(encoded) > 256 * 1024:
            raise ValueError("Invalid binding document size")
        document = json.loads(encoded, object_pairs_hook=_unique_object)
        if not isinstance(document, dict) or set(document) != {"version", "bindings"}:
            raise ValueError("Invalid binding document")
        if type(document["version"]) is not int or document["version"] != 1:
            raise ValueError("Unsupported binding version")
        items = document["bindings"]
        if not isinstance(items, list) or len(items) > MAX_SQL_SCRIPT_STATEMENTS:
            raise ValueError("Invalid binding count")
        bindings: list[SqlPanelBinding] = []
        statements: list[SqlStatement] = []
        utf16 = source.encode("utf-16-le")
        for item in items:
            if not isinstance(item, dict) or set(item) != {
                "panel_id",
                "start_offset",
                "end_offset",
            }:
                raise ValueError("Invalid binding fields")
            start, end = item["start_offset"], item["end_offset"]
            if (
                type(start) is not int
                or type(end) is not int
                or not 0 <= start < end <= len(utf16) // 2
            ):
                raise ValueError("Invalid binding offsets")
            bindings.append(SqlPanelBinding(item["panel_id"], start, end))
            statements.append(
                SqlStatement(utf16[start * 2 : end * 2].decode("utf-16-le"), start, end)
            )
        # Validate the metadata independently of current state, so legacy SQL
        # edits become stale rather than being mistaken for corrupt metadata.
        original = tuple(
            ExistingSqlPanel(binding.panel_id, statement.sql)
            for binding, statement in zip(bindings, statements, strict=True)
        )
        plan = reconcile_sql_script(
            source,
            statements,
            original,
            tuple(KeepSqlPanel(i, binding.panel_id) for i, binding in enumerate(bindings)),
        )
        plan.require_complete()
    except (ValueError, TypeError, KeyError, AttributeError, RecursionError) as exc:
        raise SqlScriptMetadataError("Invalid stored SQL associations") from exc
    current = {panel.id: panel.sql_content for panel in panels}
    if current != {panel.panel_id: panel.sql for panel in original}:
        return None
    return SqlScriptPublication(revision, source, tuple(bindings))


class SqlScriptRepository:
    def __init__(self, db: duckdb.DuckDBPyConnection) -> None:
        self._db = db

    def _read(self, dashboard_id: str) -> tuple[SqlScriptSnapshot, int]:
        dashboard = DashboardRepository(self._db).get(dashboard_id)
        count = self._db.execute(
            "SELECT count(*) FROM panels WHERE dashboard_id = ?",
            [dashboard_id],
        ).fetchone()
        if count is not None and count[0] > MAX_SQL_SCRIPT_STATEMENTS:
            raise ValueError("Dashboard exceeds 256 SQL panels")
        panels = tuple(
            sorted(PanelRepository(self._db).list(dashboard_id), key=lambda panel: panel.id)
        )
        row = self._db.execute(
            "SELECT revision, source, bindings_json, updated_at FROM dashboard_sql_scripts "
            "WHERE dashboard_id = ?",
            [dashboard_id],
        ).fetchone()
        # This legacy inference column is not part of the public Panel model.
        intents = self._db.execute(
            "SELECT id, inferred_intent_type FROM panels WHERE dashboard_id = ? ORDER BY id",
            [dashboard_id],
        ).fetchall()
        # A deterministic full-state token, not SQL matching or a resource ID.
        # Raw publication metadata is covered too, including a stale publication.
        encoded = json.dumps(
            [asdict(dashboard), [asdict(panel) for panel in panels], intents, row],
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        revision = "sql-script-v1:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        snapshot = SqlScriptSnapshot(
            dashboard_id,
            revision,
            dashboard.sql_content,
            panels,
            _publication(row, panels) if row is not None else None,
        )
        return snapshot, row[0] if row is not None else 0

    def read(self, dashboard_id: str) -> SqlScriptSnapshot:
        with project_transaction(self._db):
            snapshot, _ = self._read(dashboard_id)
        return snapshot

    def write(
        self,
        dashboard_id: str,
        expected_revision: str,
        source: str,
        decisions: Sequence[SqlIdentityDecision],
        *,
        parse: Callable[[str], Sequence[SqlStatement]],
    ) -> SqlScriptCommit:
        """Reparse, revalidate expected state and commit one complete definition set.

        A native application-owned parser is mandatory. Auth belongs to the
        calling service; a read snapshot or a valid token never grants access.
        Do not call from within another transaction or execute SQL inside this one.
        """
        if (
            not isinstance(expected_revision, str)
            or len(expected_revision) != 78
            or not expected_revision.startswith("sql-script-v1:")
            or any(char not in "0123456789abcdef" for char in expected_revision[14:])
        ):
            raise ValueError("Expected a script snapshot revision")
        statements = tuple(parse(source))
        try:
            with project_transaction(self._db):
                previous, script_revision = self._read(dashboard_id)
                if previous.revision != expected_revision:
                    raise SqlScriptWriteConflict(
                        "Dashboard changed; refresh and confirm associations again"
                    )
                if script_revision >= 2**63 - 1:
                    raise ValueError("Script revision exhausted")
                plan = reconcile_sql_script(
                    source,
                    statements,
                    tuple(
                        ExistingSqlPanel(panel.id, panel.sql_content) for panel in previous.panels
                    ),
                    decisions,
                )
                plan.require_complete()
                dashboard = DashboardRepository(self._db).get(dashboard_id)
                self._db.execute(
                    "UPDATE dashboards SET sql_content = ?, updated_at = ? WHERE id = ?",
                    [source, modification_timestamp(dashboard.updated_at), dashboard_id],
                )
                old_panels = {panel.id: panel for panel in previous.panels}
                bindings: list[SqlPanelBinding] = []
                created: list[tuple[str, str]] = []
                for item in plan.statements:
                    if isinstance(item, SqlPanelUpdate):
                        panel_id = item.panel_id
                        # Fence every retained row, even unchanged SQL. This makes
                        # concurrent PATCH/override/delete conflict with the batch.
                        reset = (
                            ", fingerprint = NULL, inferred_chart_type = NULL, "
                            "inferred_col_span = NULL, "
                            "inferred_height_px = NULL, inferred_intent_type = NULL, "
                            "selected_chart_type = chart_user_override, "
                            "selected_col_span = col_span_user_override, "
                            "selected_height_px = height_user_override"
                            if item.sql_changed
                            else ""
                        )
                        self._db.execute(
                            "UPDATE panels SET sql_content = ?, sort_order = ?, updated_at = ?"
                            + reset
                            + " WHERE id = ?",
                            [
                                item.statement.sql,
                                item.statement_index,
                                modification_timestamp(old_panels[panel_id].updated_at),
                                panel_id,
                            ],
                        )
                    else:
                        panel_id = str(uuid.uuid4())
                        timestamp = modification_timestamp("")
                        self._db.execute(
                            "INSERT INTO panels (id, dashboard_id, name, sql_content, "
                            "sort_order, created_at, updated_at) "
                            "VALUES (?, ?, ?, ?, ?, ?, ?)",
                            [
                                panel_id,
                                dashboard_id,
                                f"Panel {item.statement_index + 1}",
                                item.statement.sql,
                                item.statement_index,
                                timestamp,
                                timestamp,
                            ],
                        )
                        created.append((item.creation_key, panel_id))
                    bindings.append(
                        SqlPanelBinding(
                            panel_id, item.statement.start_offset, item.statement.end_offset
                        )
                    )
                for panel_id in plan.removed_panel_ids:
                    self._db.execute(
                        "UPDATE panels SET updated_at = ? WHERE id = ?",
                        [modification_timestamp(old_panels[panel_id].updated_at), panel_id],
                    )
                    self._db.execute("DELETE FROM panels WHERE id = ?", [panel_id])
                document = json.dumps(
                    {"version": 1, "bindings": [asdict(binding) for binding in bindings]},
                    ensure_ascii=True,
                    separators=(",", ":"),
                )
                self._db.execute(
                    "INSERT INTO dashboard_sql_scripts "
                    "(dashboard_id, revision, source, bindings_json, updated_at) "
                    "VALUES (?, ?, ?, ?, ?) ON CONFLICT (dashboard_id) "
                    "DO UPDATE SET revision = excluded.revision, source = excluded.source, "
                    "bindings_json = excluded.bindings_json, updated_at = excluded.updated_at",
                    [
                        dashboard_id,
                        script_revision + 1,
                        source,
                        document,
                        modification_timestamp(""),
                    ],
                )
                snapshot, _ = self._read(dashboard_id)
                result = SqlScriptCommit(snapshot, tuple(created))
        except (duckdb.TransactionException, duckdb.ConstraintException) as exc:
            raise SqlScriptWriteConflict("Script write conflicted; refresh and retry") from exc
        return result
