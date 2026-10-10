"""Conditional, short transaction recording a server-verified completed Run."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import duckdb

from sqlviz_storage.dashboard_repository import DashboardNotFound, DashboardRepository
from sqlviz_storage.sql_script_repository import (
    SqlDefinitionConflict,
    SqlDefinitionReference,
    SqlScriptRepository,
)
from sqlviz_storage.timestamps import modification_timestamp
from sqlviz_storage.transactions import project_transaction


@dataclass(frozen=True)
class SqlRunCompletion:
    definition: SqlDefinitionReference
    last_run_at: str
    last_run_sql: str


def record_sql_run(db: duckdb.DuckDBPyConnection, definition: SqlDefinitionReference,
                   completed_at: str) -> SqlRunCompletion:
    """Caller verifies server proof; source always comes from durable publication.

    Touch the parent before reading the definition, then all its bounded peers:
    concurrent commits and legacy SQL/delete writes must conflict at commit.
    The server composition timestamp gives retries the same acknowledgement and
    prevents an older proof from replacing a newer completion of the same script.
    """
    try:
        with project_transaction(db):
            parent = DashboardRepository(db).get(definition.dashboard_id)
            db.execute("UPDATE dashboards SET updated_at = ? WHERE id = ?",
                       [modification_timestamp(parent.updated_at), parent.id])
            snapshot = SqlScriptRepository(db).require_definition(definition)
            assert snapshot.publication is not None
            if not snapshot.publication.bindings:
                raise SqlDefinitionConflict("An empty script is not an executed Run")
            source = snapshot.publication.source
            if parent.last_run_at is not None:
                previous = datetime.fromisoformat(parent.last_run_at)
                requested = datetime.fromisoformat(completed_at)
                if previous > requested:
                    raise SqlDefinitionConflict("A newer Run has already completed")
                if previous == requested and parent.last_run_sql != source:
                    raise SqlDefinitionConflict("Completion acknowledgement is incompatible")
            stamp = modification_timestamp("")
            db.execute(
                "UPDATE panels SET updated_at = CASE WHEN updated_at = ? THEN ? ELSE ? END "
                "WHERE dashboard_id = ?",
                [stamp, modification_timestamp(stamp), stamp, parent.id],
            )
            db.execute("UPDATE dashboards SET last_run_at = ?, last_run_sql = ? WHERE id = ?",
                       [completed_at, source, parent.id])
            result = SqlRunCompletion(definition, completed_at, source)
        return result
    except DashboardNotFound as exc:
        raise SqlDefinitionConflict("Run definition no longer exists") from exc
    except (duckdb.TransactionException, duckdb.ConstraintException) as exc:
        raise SqlDefinitionConflict("Run completion conflicted") from exc
