"""Native syntax extraction preserves data literals and source boundaries."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event

import duckdb
import pytest
from sqlviz_api.services.queries import QueryFailure
from sqlviz_api.services.sql_scripts import SqlScriptService
from sqlviz_core.models.sql_script import MAX_SQL_SCRIPT_STATEMENTS, SqlScriptError


@pytest.mark.parametrize("source,expected", [
    ("", []), (" ; ; -- only;\n/* comment; */", []),
    ("SELECT 'a;b' AS value; SELECT 2;", ["SELECT 'a;b' AS value", "SELECT 2;"]),
    ("SELECT 'it''s;a'; SELECT 2", ["SELECT 'it''s;a'", "SELECT 2"]),
    ('SELECT "a;b" FROM missing; SELECT 2', ['SELECT "a;b" FROM missing', "SELECT 2"]),
    ("SELECT $$a;b$$; SELECT $tag$c;d$tag$;", ["SELECT $$a;b$$", "SELECT $tag$c;d$tag$;"]),
    ("/* outer /* inner; */ tail; */ SELECT 1; -- end;\n",
     ["/* outer /* inner; */ tail; */ SELECT 1; -- end;"]),
    ("SELECT 1; -- leading;\r\nSELECT 2 /* trailing; */;",
     ["SELECT 1", "-- leading;\r\nSELECT 2 /* trailing; */;"]),
    ("SELECT 1;; /* trivia */ ; SELECT 2; ; -- last",
     ["SELECT 1", "SELECT 2; ; -- last"]),
    ("SELECT '😀;é'; SELECT '😀;é'", ["SELECT '😀;é'", "SELECT '😀;é'"]),
    ("WITH x AS (SELECT ';') SELECT * FROM x; SELECT [1, 2]",
     ["WITH x AS (SELECT ';') SELECT * FROM x", "SELECT [1, 2]"]),
])
def test_native_boundaries_preserve_original_source_and_utf16_spans(source, expected):
    statements = SqlScriptService().parse(source)
    assert [statement.sql for statement in statements] == expected
    encoded = source.encode("utf-16-le")
    previous_end = 0
    for statement in statements:
        assert statement.start_offset >= previous_end
        assert encoded[statement.start_offset * 2:statement.end_offset * 2].decode("utf-16-le") \
            == statement.sql
        previous_end = statement.end_offset


@pytest.mark.parametrize("source", [
    "SELECT 1; SELECT 'unfinished", 'SELECT 1; SELECT "unfinished',
    "SELECT 1; /* unfinished", "SELECT $$unfinished", "SELECT 1; SELECT FROM",
])
def test_invalid_later_statement_rejects_the_entire_script(source):
    with pytest.raises(SqlScriptError) as error:
        SqlScriptService().parse(source)
    assert error.value.code == "sql_script_invalid"
    assert "unfinished" not in str(error.value)  # No source echo in diagnostics.


def test_parser_does_not_bind_tables_functions_or_named_filter_parameters():
    statements = SqlScriptService().parse(
        "SELECT missing_function(x) FROM not_created WHERE x = $x; "
        "SELECT * FROM other_not_created",
    )
    assert len(statements) == 2
    assert "$x" in statements[0].sql


def test_statement_budget_has_an_exact_boundary():
    service = SqlScriptService()
    assert len(service.parse("SELECT 1;" * MAX_SQL_SCRIPT_STATEMENTS)) == 256
    with pytest.raises(SqlScriptError) as error:
        service.parse("SELECT 1;" * (MAX_SQL_SCRIPT_STATEMENTS + 1))
    assert error.value.code == "sql_script_limit"


@pytest.mark.parametrize("source", ["SELECT 1", "SELECT 'unfinished"])
def test_native_catalog_is_closed_after_success_or_syntax_failure(monkeypatch, source):
    connect = duckdb.connect
    connections = []

    def recorded(*args, **kwargs):
        connection = connect(*args, **kwargs)
        connections.append(connection)
        return connection

    monkeypatch.setattr(duckdb, "connect", recorded)
    try:
        SqlScriptService().parse(source)
    except SqlScriptError:
        pass
    assert len(connections) == 1
    with pytest.raises(duckdb.ConnectionException):
        connections[0].extract_statements("SELECT 1")


def test_app_local_admission_rejects_excess_concurrency_and_recovers(monkeypatch):
    connect = duckdb.connect
    ready = Barrier(3)
    release = Event()

    class HeldConnection:
        def __init__(self, connection):
            self.connection = connection

        def extract_statements(self, sql):
            ready.wait(timeout=5)
            assert release.wait(timeout=5)
            return self.connection.extract_statements(sql)

        def close(self):
            self.connection.close()

    monkeypatch.setattr(duckdb, "connect", lambda *a, **kw: HeldConnection(connect(*a, **kw)))
    service = SqlScriptService()
    with ThreadPoolExecutor(max_workers=2) as executor:
        pending = [executor.submit(service.parse, "SELECT 1") for _ in range(2)]
        try:
            ready.wait(timeout=5)
            with pytest.raises(QueryFailure) as error:
                service.parse("SELECT 2")
            assert error.value.status_code == 429
        finally:
            release.set()
        assert all(len(task.result(timeout=5)) == 1 for task in pending)
    monkeypatch.setattr(duckdb, "connect", connect)
    assert len(service.parse("SELECT 2")) == 1
