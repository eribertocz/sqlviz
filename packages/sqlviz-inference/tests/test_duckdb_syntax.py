"""Paso 7 — DuckDB advanced syntax: EXCLUDE/REPLACE/RENAME, FILTER(WHERE), QUALIFY,
quantile_cont, COLUMNS(regex).

Paso 7a: Star-modifier clauses (EXCLUDE/REPLACE/RENAME) → detail/table.
Paso 7b: FILTER(WHERE) → trend/line; QUALIFY + RANK() OVER → ranking/bar_horizontal.
Paso 7c: quantile_cont/disc → distribution/table (§16.33 fix);
         COLUMNS('regex') → detail/table in D0 (D1 tech debt: §TD-COLUMNS-D1).

§16.32: QUALIFY without LIMIT is DuckDB's idiomatic ranking pattern.
§16.33: percentile aggregates (PercentileCont/Disc) force distribution/table
        because boxplot is not in V0.1 chart types.
"""
from sqlviz_core.models import ColumnSchema
from sqlviz_inference import infer

# ── Shared schemas ────────────────────────────────────────────────────────────

_SCHEMA_EVENTS = [
    ColumnSchema(name="event_id",    type="INTEGER"),
    ColumnSchema(name="user_id",     type="INTEGER"),
    ColumnSchema(name="event_name",  type="VARCHAR"),
    ColumnSchema(name="event_date",  type="DATE"),
    ColumnSchema(name="internal_id", type="INTEGER"),
    ColumnSchema(name="raw_payload", type="VARCHAR"),
]

_SCHEMA_RAW_SALES = [
    ColumnSchema(name="order_id",  type="INTEGER"),
    ColumnSchema(name="customer",  type="VARCHAR"),
    ColumnSchema(name="amount",    type="VARCHAR"),
    ColumnSchema(name="sale_date", type="DATE"),
]

_SCHEMA_EVENTS2 = [
    ColumnSchema(name="event_id",   type="INTEGER"),
    ColumnSchema(name="user_id",    type="INTEGER"),
    ColumnSchema(name="created_at", type="DATE"),
    ColumnSchema(name="event_type", type="VARCHAR"),
]

_SQL_EXCLUDE = "SELECT * EXCLUDE (internal_id, raw_payload) FROM events"
_SQL_REPLACE = (
    "SELECT * REPLACE (try_cast(amount AS DOUBLE) AS amount) FROM raw_sales"
)
_SQL_RENAME  = "SELECT * RENAME (created_at AS event_date) FROM events"


# ── SELECT * EXCLUDE ──────────────────────────────────────────────────────────

class TestDuckDBExclude:

    def test_exclude_d0(self) -> None:
        r = infer(sql=_SQL_EXCLUDE)
        assert r.intent_winner == "detail"
        assert r.chart_winner  == "table"
        assert not r.errors

    def test_exclude_d1(self) -> None:
        r = infer(sql=_SQL_EXCLUDE, schema=_SCHEMA_EVENTS)
        assert r.intent_winner == "detail"
        assert r.chart_winner  == "table"
        assert not r.errors


# ── SELECT * REPLACE ──────────────────────────────────────────────────────────

class TestDuckDBReplace:

    def test_replace_d0(self) -> None:
        r = infer(sql=_SQL_REPLACE)
        assert r.intent_winner == "detail"
        assert r.chart_winner  == "table"
        assert not r.errors

    def test_replace_d1(self) -> None:
        r = infer(sql=_SQL_REPLACE, schema=_SCHEMA_RAW_SALES)
        assert r.intent_winner == "detail"
        assert r.chart_winner  == "table"
        assert not r.errors


# ── SELECT * RENAME ───────────────────────────────────────────────────────────

class TestDuckDBRename:

    def test_rename_d0(self) -> None:
        r = infer(sql=_SQL_RENAME)
        assert r.intent_winner == "detail"
        assert r.chart_winner  == "table"
        assert not r.errors

    def test_rename_d1(self) -> None:
        r = infer(sql=_SQL_RENAME, schema=_SCHEMA_EVENTS2)
        assert r.intent_winner == "detail"
        assert r.chart_winner  == "table"
        assert not r.errors


# ── Paso 7b: COUNT(*) FILTER (WHERE ...) ─────────────────────────────────────

_SCHEMA_ORDERS = [
    ColumnSchema(name="month",     type="DATE"),
    ColumnSchema(name="completed", type="BIGINT"),
    ColumnSchema(name="cancelled", type="BIGINT"),
]

_SQL_FILTER = (
    "SELECT month,"
    " COUNT(*) FILTER (WHERE status = 'completed') AS completed,"
    " COUNT(*) FILTER (WHERE status = 'cancelled') AS cancelled"
    " FROM orders GROUP BY month ORDER BY month"
)


class TestDuckDBFilter:

    def test_filter_d0(self) -> None:
        r = infer(sql=_SQL_FILTER)
        assert r.intent_winner == "trend"
        assert r.chart_winner  == "line"
        assert not r.errors

    def test_filter_d1(self) -> None:
        r = infer(sql=_SQL_FILTER, schema=_SCHEMA_ORDERS)
        assert r.intent_winner == "trend"
        assert r.chart_winner  == "line"
        assert not r.errors


# ── Paso 7b: QUALIFY (§16.32) ────────────────────────────────────────────────

_SCHEMA_PRODUCTS = [
    ColumnSchema(name="product", type="VARCHAR"),
    ColumnSchema(name="revenue", type="DOUBLE"),
    ColumnSchema(name="rnk",    type="INTEGER"),
]

_SQL_QUALIFY = (
    "SELECT product, revenue,"
    " RANK() OVER (ORDER BY revenue DESC) AS rnk"
    " FROM product_revenue"
    " QUALIFY rnk <= 10"
)


class TestDuckDBQualify:

    def test_qualify_d0(self) -> None:
        r = infer(sql=_SQL_QUALIFY)
        assert r.intent_winner == "ranking"
        assert r.chart_winner  == "bar_horizontal"
        assert not r.errors

    def test_qualify_d1(self) -> None:
        r = infer(sql=_SQL_QUALIFY, schema=_SCHEMA_PRODUCTS)
        assert r.intent_winner == "ranking"
        assert r.chart_winner  == "bar_horizontal"
        assert not r.errors


# ── Paso 7c: quantile_cont (§16.33) ──────────────────────────────────────────
# quantile_cont → sqlglot PercentileCont → distribution/table.
# Boxplot is not in V0.1 chart types; table is the explicit fallback.

_SCHEMA_EMPLOYEES = [
    ColumnSchema(name="department", type="VARCHAR"),
    ColumnSchema(name="p25",        type="DOUBLE"),
    ColumnSchema(name="median",     type="DOUBLE"),
    ColumnSchema(name="p75",        type="DOUBLE"),
]

_SQL_QUANTILE = (
    "SELECT department,"
    " quantile_cont(salary, 0.25) AS p25,"
    " quantile_cont(salary, 0.50) AS median,"
    " quantile_cont(salary, 0.75) AS p75"
    " FROM employees GROUP BY department"
)


class TestDuckDBQuantile:

    def test_quantile_cont_d0(self) -> None:
        r = infer(sql=_SQL_QUANTILE)
        assert r.intent_winner == "distribution"
        assert r.chart_winner  == "table"
        assert r.fallback_applied
        assert not r.errors

    def test_quantile_cont_d1(self) -> None:
        r = infer(sql=_SQL_QUANTILE, schema=_SCHEMA_EMPLOYEES)
        assert r.intent_winner == "distribution"
        assert r.chart_winner  == "table"
        assert r.fallback_applied
        assert not r.errors


# ── Paso 7c: COLUMNS('regex') — tech debt §TD-COLUMNS-D1 ─────────────────────
# D0 (SQL only): detail/table ✓ — COLUMNS treated as wide SELECT without schema.
# D1 (SQL+schema): correlation/scatter ✗ — schema of all-DOUBLE columns triggers
#   has_two_numeric_columns=1 + no_group_by=1 + no_aggregation=1 → correlation.
#   Root cause: exp.Columns node not recognized as a "select all" marker;
#   correlation penalty for has_string_column doesn't fire (no string cols).
#   Fix deferred to V0.2: requires detecting exp.Columns in AST to suppress
#   correlation signals. Non-blocking for V0.1 given rarity of COLUMNS() usage.

_SQL_COLUMNS = "SELECT COLUMNS('metric_.*') FROM metrics"

_SCHEMA_METRICS = [
    ColumnSchema(name="metric_revenue", type="DOUBLE"),
    ColumnSchema(name="metric_users",   type="BIGINT"),
    ColumnSchema(name="metric_orders",  type="BIGINT"),
]


class TestDuckDBColumns:

    def test_columns_regex_d0(self) -> None:
        r = infer(sql=_SQL_COLUMNS)
        assert r.intent_winner == "detail"
        assert r.chart_winner  == "table"
        assert not r.errors

    def test_columns_regex_d1_known_regression(self) -> None:
        r = infer(sql=_SQL_COLUMNS, schema=_SCHEMA_METRICS)
        # §TD-COLUMNS-D1: known issue — all-numeric schema misclassifies as
        # correlation. Assert current (wrong) behavior so any change is noticed.
        assert r.intent_winner == "correlation"
        assert r.chart_winner  == "scatter"
        assert not r.errors
