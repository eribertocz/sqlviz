"""Real DuckDB tests for isolation, legacy data projection and budgets."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from threading import Event
from typing import Any

import duckdb
import pytest
from sqlviz_api.services.queries import QueryFailure, QueryLimits, QueryService
from sqlviz_storage.project_db import create_project
from sqlviz_storage.schema import APPLICATION_TABLES


@pytest.fixture
def source():
    conn = create_project(":memory:")
    conn.execute(
        "CREATE TABLE sales AS SELECT * FROM (VALUES ('A', 12.50), ('B', 8.25)) t(region, amount)"
    )
    yield conn
    conn.close()


def test_reserved_registry_covers_entire_project_schema(source):
    tables = {row[0] for row in source.execute("SHOW TABLES").fetchall()}
    assert tables - {"sales"} == APPLICATION_TABLES


@pytest.mark.parametrize("table", sorted(APPLICATION_TABLES))
def test_metadata_is_rejected_in_all_identifier_cases(source, table):
    with pytest.raises(QueryFailure) as failure:
        QueryService().execute(source, f'SELECT * FROM main."{table.upper()}"')
    assert failure.value.code == "metadata_access"


@pytest.mark.parametrize(
    "sql",
    [
        "CREATE TABLE stolen AS SELECT * FROM _sqlviz_auth",
        "DELETE FROM sales",
        "SELECT 1; SELECT 2",
        "ATTACH 'other.sqlviz' AS stolen",
        "SET enable_external_access = true",
        "INSTALL httpfs",
        "SELECT 1 INTO stolen",
    ],
)
def test_author_queries_are_read_only_too(source, sql):
    with pytest.raises(QueryFailure) as failure:
        QueryService().execute(source, sql)
    assert failure.value.code == "query_policy"
    assert source.execute("SELECT count(*) FROM sales").fetchone() == (2,)


def test_local_tables_preserve_types_and_bound_parameters(source):
    result = QueryService().execute(
        source, "SELECT region, amount FROM sales WHERE region=$region", {"region": "A"}
    )
    assert result.columns == (("region", "VARCHAR"), ("amount", "DECIMAL(4,2)"))
    assert result.rows == [("A", Decimal("12.50"))]


def test_cte_names_do_not_export_project_tables(source):
    result = QueryService().execute(
        source, "WITH shares AS (SELECT 42 AS value) SELECT * FROM shares"
    )
    assert result.rows == [(42,)]


def test_quoted_schema_and_table_names_are_data_not_sql(source):
    source.execute('CREATE SCHEMA "a;\'b"')
    source.execute('CREATE TABLE "a;\'b"."c""d" AS SELECT 7 AS value')
    result = QueryService().execute(source, 'SELECT * FROM "a;\'b"."c""d"')
    assert result.rows == [(7,)]
    assert source.execute("SELECT count(*) FROM _sqlviz_auth").fetchone() == (1,)


def test_catalog_enumeration_contains_no_application_tables_or_project_path(source):
    result = QueryService().execute(
        source, "SELECT table_name FROM duckdb_tables() WHERE NOT internal"
    )
    assert result.rows == []
    databases = QueryService().execute(source, "SELECT path FROM duckdb_databases()")
    assert all(row[0] is None for row in databases.rows)


def test_dynamic_table_lookup_cannot_bypass_physical_isolation(source):
    with pytest.raises(duckdb.CatalogException):
        QueryService().execute(source, "SELECT * FROM query_table('_sqlviz_auth')")


def test_project_macros_and_secrets_are_not_copied(source):
    source.execute("CREATE MACRO leak() AS (SELECT session_secret FROM _sqlviz_auth)")
    source.execute("CREATE SECRET test_secret (TYPE HTTP, BEARER_TOKEN 'synthetic-canary')")
    assert QueryService().execute(source, "SELECT name FROM duckdb_secrets()").rows == []
    with pytest.raises(duckdb.CatalogException):
        QueryService().execute(source, "SELECT leak()")


def test_views_are_not_materialized_on_metadata_connection(source):
    source.execute("CREATE VIEW leak AS SELECT session_secret FROM _sqlviz_auth")
    with pytest.raises(QueryFailure) as failure:
        QueryService().execute(source, "SELECT * FROM leak")
    assert failure.value.code == "unsupported_view"


def test_attached_catalogs_are_not_accessible(source):
    source.execute("ATTACH ':memory:' AS other")
    source.execute("CREATE TABLE other.data AS SELECT 42")
    with pytest.raises(QueryFailure) as failure:
        QueryService().execute(source, "SELECT * FROM other.main.data")
    assert failure.value.code == "catalog_access"


@pytest.mark.parametrize("function", ["read_text", "read_csv_auto", "read_parquet", "glob"])
def test_external_functions_cannot_read_even_existing_files(source, tmp_path, function):
    path = tmp_path / "canary.txt"
    path.write_text("synthetic-secret", encoding="utf-8")
    with pytest.raises(QueryFailure) as failure:
        QueryService().execute(source, f"SELECT * FROM {function}('{path.as_posix()}')")
    assert failure.value.code == "external_access"
    assert path.read_text(encoding="utf-8") == "synthetic-secret"


@pytest.mark.parametrize(
    ("limits", "sql", "code"),
    [
        (QueryLimits(max_rows=2), "SELECT * FROM range(3)", "row_limit"),
        (QueryLimits(max_result_bytes=8), "SELECT 'long value' AS value", "result_limit"),
        (QueryLimits(max_source_rows=1), "SELECT SUM(amount) FROM sales", "source_limit"),
        (QueryLimits(max_snapshot_bytes=1), "SELECT * FROM sales", "snapshot_limit"),
        (QueryLimits(max_sql_bytes=4), "SELECT 1", "sql_limit"),
    ],
)
def test_limit_failure_never_returns_partial_data(source, limits, sql, code):
    with pytest.raises(QueryFailure) as failure:
        QueryService(limits).execute(source, sql)
    assert failure.value.status_code == 413
    assert failure.value.code == code


def test_schema_probe_does_not_compute_huge_result(source):
    result = QueryService(QueryLimits(max_rows=1)).execute(
        source, "SELECT i FROM range(100000000000) t(i); -- end", schema_only=True
    )
    assert result.columns == (("i", "BIGINT"),)
    assert result.rows == []


def test_timeout_interrupts_engine_and_next_query_still_runs(source):
    service = QueryService(QueryLimits(timeout_seconds=0.2))
    with pytest.raises(QueryFailure) as failure:
        service.execute(source, "SELECT sum(sin(i)) FROM range(100000000000) t(i)")
    assert failure.value.code == "query_timeout"
    assert service.execute(source, "SELECT 42").rows == [(42,)]
    assert source.execute("SELECT count(*) FROM _sqlviz_auth").fetchone() == (1,)


def test_admission_is_app_local_and_releases_after_failure(source, monkeypatch):
    service = QueryService(QueryLimits(max_concurrent=1))
    entered, release = Event(), Event()
    original = service._execute

    def blocked(*args: Any, **kwargs: Any):
        entered.set()
        assert release.wait(5)
        raise QueryFailure(413, "test_failure", "Synthetic failure")

    monkeypatch.setattr(service, "_execute", blocked)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(service.execute, source, "SELECT 1")
        try:
            assert entered.wait(5)
            with pytest.raises(QueryFailure) as failure:
                service.execute(source, "SELECT 2")
            assert failure.value.code == "query_busy"
            assert QueryService().execute(source, "SELECT 3").rows == [(3,)]
        finally:
            release.set()
        with pytest.raises(QueryFailure):
            future.result(timeout=5)
    monkeypatch.setattr(service, "_execute", original)
    assert service.execute(source, "SELECT 4").rows == [(4,)]


def test_snapshot_directory_is_removed_on_success_and_failure(source, monkeypatch):
    from sqlviz_api.services import queries

    original = queries.TemporaryDirectory
    paths: list[Path] = []

    def tracked(*args: Any, **kwargs: Any):
        directory = original(*args, **kwargs)
        paths.append(Path(directory.name))
        return directory

    monkeypatch.setattr(queries, "TemporaryDirectory", tracked)
    service = QueryService()
    service.execute(source, "SELECT * FROM sales")
    with pytest.raises(QueryFailure):
        service.execute(source, "SELECT * FROM _sqlviz_auth")
    assert len(paths) == 2
    assert all(not path.exists() for path in paths)


def test_nonpositive_limits_fail_before_serving():
    with pytest.raises(ValueError):
        replace(QueryLimits(), max_concurrent=0)


def test_combined_sources_share_one_snapshot_budget(source):
    source.execute("CREATE TABLE other AS SELECT 3 AS id")
    with pytest.raises(QueryFailure) as failure:
        QueryService(QueryLimits(max_source_rows=2)).execute(
            source,
            "SELECT region, id FROM sales CROSS JOIN other",
        )
    assert failure.value.code == "source_limit"
    with pytest.raises(QueryFailure) as failure:
        QueryService(QueryLimits(max_tables=1)).execute(
            source,
            "SELECT region, id FROM sales CROSS JOIN other",
        )
    assert failure.value.code == "source_limit"


def test_parallel_queries_own_independent_catalogs_and_source_cursors(source):
    service = QueryService()

    def run(region):
        cursor = source.cursor()
        try:
            return service.execute(
                cursor,
                "SELECT region FROM sales WHERE region=$value",
                {
                    "value": region,
                },
            ).rows
        finally:
            cursor.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(run, ["A", "B"])) == [[("A",)], [("B",)]]


def test_persistent_project_data_and_credentials_are_not_migrated(tmp_path):
    path = tmp_path / "legacy.sqlviz"
    conn = create_project(str(path))
    try:
        conn.execute("CREATE TABLE sales AS SELECT DATE '2026-10-06' AS day, [1, 2] AS items")
        before = conn.execute("SELECT * FROM _sqlviz_auth").fetchall()
        result = QueryService().execute(conn, "SELECT * FROM sales")
        assert result.rows == conn.execute("SELECT * FROM sales").fetchall()
        assert result.columns == (("day", "DATE"), ("items", "INTEGER[]"))
        assert conn.execute("SELECT * FROM _sqlviz_auth").fetchall() == before
    finally:
        conn.close()
    reopened = duckdb.connect(str(path))
    try:
        assert reopened.execute("SELECT items FROM sales").fetchone() == ([1, 2],)
        assert reopened.execute("SELECT * FROM _sqlviz_auth").fetchall() == before
    finally:
        reopened.close()
