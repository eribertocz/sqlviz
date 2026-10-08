"""Bounded analytical execution in a catalog that never attaches the project.

The legacy project format mixes data and application tables. Only physical user
tables referenced by a read query are copied, using trusted identifiers, into a
fresh catalog. User SQL is never executed by the metadata connection.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import BoundedSemaphore, Event, Timer
from typing import Any

import duckdb
import sqlglot
from sqlglot.optimizer.scope import traverse_scope
from sqlviz_core.models.parameters import ParameterLimits, validate_parameters
from sqlviz_storage.schema import APPLICATION_TABLES

from sqlviz_api.serialization import json_safe
from sqlviz_api.services.access import AccessDenied
from sqlviz_api.services.query_policy import validate_read_query


@dataclass(frozen=True)
class QueryLimits:
    timeout_seconds: float = 10
    max_rows: int = 10_000
    max_result_bytes: int = 8 * 1024 * 1024
    max_source_rows: int = 100_000
    max_snapshot_bytes: int = 64 * 1024 * 1024
    max_tables: int = 16
    max_sql_bytes: int = 100_000
    max_concurrent: int = 2
    memory_limit: str = "256MB"

    def __post_init__(self) -> None:
        if any(
            value <= 0
            for value in (
                self.timeout_seconds,
                self.max_rows,
                self.max_result_bytes,
                self.max_source_rows,
                self.max_snapshot_bytes,
                self.max_tables,
                self.max_sql_bytes,
                self.max_concurrent,
            )
        ):
            raise ValueError("Query limits must be positive")


class QueryFailure(Exception):
    def __init__(self, status_code: int, code: str, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class QueryResult:
    columns: tuple[tuple[str, str], ...]
    rows: list[tuple[Any, ...]]


def _identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _reserved(name: str) -> bool:
    lowered = name.lower()
    return (
        lowered in APPLICATION_TABLES
        or lowered.startswith(("_sqlviz_", "_brain_"))
        or lowered
        in {
            "feedback_patterns",
            "layout_patterns",
            "feedback_events",
        }
    )


class QueryService:
    """App-local admission control; every operation owns and closes its catalog."""

    def __init__(
        self,
        limits: QueryLimits | None = None,
        *,
        parameter_limits: ParameterLimits | None = None,
    ):
        self.limits = limits or QueryLimits()
        self.parameter_limits = parameter_limits or ParameterLimits()
        self._slots = BoundedSemaphore(self.limits.max_concurrent)

    def validate(self, sql: str) -> sqlglot.exp.Query:
        if len(sql.encode("utf-8")) > self.limits.max_sql_bytes:
            raise QueryFailure(413, "sql_limit", "SQL exceeds the size limit")
        try:
            return validate_read_query(sql)
        except (sqlglot.errors.ParseError, RecursionError):
            # Preserve the author's existing syntax-error inference fallback.
            raise duckdb.ParserException("SQL could not be parsed") from None
        except AccessDenied as exc:
            raise QueryFailure(403, "query_policy", exc.detail) from None

    def execute(
        self,
        source: duckdb.DuckDBPyConnection,
        sql: str,
        parameters: dict[str, Any] | None = None,
        *,
        schema_only: bool = False,
    ) -> QueryResult:
        if not self._slots.acquire(blocking=False):
            raise QueryFailure(429, "query_busy", "Analytical execution is busy; retry shortly")
        try:
            parameters = validate_parameters(parameters or {}, self.parameter_limits)
            query = self.validate(sql)
            return self._execute(source, sql, query, parameters, schema_only)
        finally:
            self._slots.release()

    def _execute(
        self,
        source: duckdb.DuckDBPyConnection,
        sql: str,
        query: sqlglot.exp.Query,
        parameters: dict[str, Any] | None,
        schema_only: bool,
    ) -> QueryResult:
        with TemporaryDirectory(prefix="sqlviz-query-") as directory:
            conn = duckdb.connect(
                ":memory:",
                config={
                    "secret_directory": directory,
                    "allow_persistent_secrets": False,
                    "autoinstall_known_extensions": False,
                    "autoload_known_extensions": False,
                    "allow_community_extensions": False,
                    "python_enable_replacements": False,
                    "memory_limit": self.limits.memory_limit,
                    "threads": 2,
                    "max_temp_directory_size": "0B",
                },
            )
            expired = Event()

            def interrupt() -> None:
                expired.set()
                source.interrupt()
                conn.interrupt()

            timer = Timer(self.limits.timeout_seconds, interrupt)
            timer.daemon = True
            timer.start()
            try:
                self._snapshot(source, conn, query, Path(directory), expired)
                conn.execute("SET enable_external_access = false")
                conn.execute("SET lock_configuration = true")
                self._check_deadline(expired)
                statement = (
                    f"SELECT * FROM ({query.sql(dialect='duckdb')}) AS _schema LIMIT 0"
                    if schema_only
                    else sql
                )
                conn.execute(statement, parameters or None)
                columns = tuple((str(d[0]), str(d[1])) for d in conn.description or [])
                rows: list[tuple[Any, ...]] = []
                size = 0
                while batch := conn.fetchmany(min(256, self.limits.max_rows + 1)):
                    self._check_deadline(expired)
                    for row in batch:
                        if len(rows) >= self.limits.max_rows:
                            raise QueryFailure(
                                413,
                                "row_limit",
                                "Query exceeds the row limit; aggregate or add LIMIT",
                            )
                        size += len(
                            json.dumps(
                                dict(zip((c[0] for c in columns), (json_safe(v) for v in row))),
                                ensure_ascii=False,
                            ).encode("utf-8")
                        )
                        if size > self.limits.max_result_bytes:
                            raise QueryFailure(
                                413, "result_limit", "Query exceeds the result size limit"
                            )
                        rows.append(row)
                self._check_deadline(expired)
                return QueryResult(columns, rows)
            except duckdb.InterruptException:
                raise QueryFailure(
                    408, "query_timeout", "Analytical execution exceeded its time limit"
                ) from None
            except duckdb.PermissionException:
                raise QueryFailure(
                    403, "external_access", "External access is disabled for analytical SQL"
                ) from None
            except duckdb.OutOfMemoryException:
                raise QueryFailure(
                    413, "memory_limit", "Query exceeds the analytical memory budget"
                ) from None
            except (sqlglot.errors.OptimizeError, RecursionError):
                raise QueryFailure(
                    422, "invalid_query", "Query sources could not be resolved"
                ) from None
            finally:
                timer.cancel()
                timer.join()
                conn.close()

    @staticmethod
    def _check_deadline(expired: Event) -> None:
        if expired.is_set():
            raise QueryFailure(408, "query_timeout", "Analytical execution exceeded its time limit")

    def _snapshot(
        self,
        source: duckdb.DuckDBPyConnection,
        target: duckdb.DuckDBPyConnection,
        query: sqlglot.exp.Query,
        directory: Path,
        expired: Event,
    ) -> None:
        tables: set[tuple[str, str]] = set()
        for scope in traverse_scope(query):
            for _, relation in scope.selected_sources.values():
                if not isinstance(relation, sqlglot.exp.Table) or not isinstance(
                    relation.this, sqlglot.exp.Identifier
                ):
                    continue  # CTEs/subqueries and table functions stay in the isolated catalog.
                if relation.catalog:
                    raise QueryFailure(
                        403,
                        "catalog_access",
                        "Project and attached catalogs are unavailable to analytical SQL",
                    )
                if _reserved(relation.name):
                    raise QueryFailure(
                        403,
                        "metadata_access",
                        "Application tables are unavailable to analytical SQL",
                    )
                tables.add((relation.db or "main", relation.name))
        if len(tables) > self.limits.max_tables:
            raise QueryFailure(413, "source_limit", "Query references too many source tables")
        total_rows = total_bytes = 0
        for index, (schema, name) in enumerate(sorted(tables)):
            self._check_deadline(expired)
            row = source.execute(
                "SELECT schema_name, table_name FROM duckdb_tables() "
                "WHERE database_name = current_database() AND lower(schema_name) = lower(?) "
                "AND lower(table_name) = lower(?) AND NOT internal",
                [schema, name],
            ).fetchone()
            if row is None:
                view = source.execute(
                    "SELECT 1 FROM duckdb_views() WHERE database_name = current_database() "
                    "AND lower(schema_name) = lower(?) AND lower(view_name) = lower(?) "
                    "AND NOT internal",
                    [schema, name],
                ).fetchone()
                if view:
                    raise QueryFailure(
                        422,
                        "unsupported_view",
                        "Local views require a dataset adapter; use a physical table",
                    )
                continue  # DuckDB reports missing relations in the isolated catalog.
            schema, name = row
            qualified = f"{_identifier(schema)}.{_identifier(name)}"
            path = directory / f"source-{index}.parquet"
            literal = "'" + path.as_posix().replace("'", "''") + "'"
            # No user expression reaches the metadata connection. LIMIT includes
            # one sentinel row: oversized sources fail, never silently truncate.
            remaining_rows = self.limits.max_source_rows - total_rows + 1
            source.execute(
                f"COPY (SELECT * FROM {qualified} LIMIT {remaining_rows}) "
                f"TO {literal} (FORMAT PARQUET)"
            )
            total_bytes += path.stat().st_size
            if total_bytes > self.limits.max_snapshot_bytes:
                raise QueryFailure(413, "snapshot_limit", "Source snapshot exceeds the size limit")
            target.execute("LOAD parquet")
            target.execute(f"CREATE SCHEMA IF NOT EXISTS {_identifier(schema)}")
            target.execute(f"CREATE TABLE {qualified} AS SELECT * FROM read_parquet({literal})")
            count = target.execute(f"SELECT count(*) FROM {qualified}").fetchone()
            total_rows += int(count[0]) if count else 0
            if total_rows > self.limits.max_source_rows:
                raise QueryFailure(413, "source_limit", "Source snapshot exceeds the row limit")
