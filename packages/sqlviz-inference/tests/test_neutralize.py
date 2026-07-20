"""Tests for neutralize_filters (filters/neutralize.py).

Neutralizing an "All" variable must replace exactly its predicate with TRUE,
leave every other predicate (and its bindings) intact, and bail (None) when the
variable is not part of a strippable boolean predicate.
"""

from __future__ import annotations

import duckdb
from sqlviz_inference.filters.neutralize import neutralize_filters

_SRC = (
    "(VALUES ('A', 10), ('B', 50), ('C', 90)) t(region, price)"
)


def _run(sql: str, binds: dict[str, object] | None = None) -> list[tuple[object, ...]]:
    con = duckdb.connect(":memory:")
    return con.execute(sql, binds).fetchall() if binds else con.execute(sql).fetchall()


def test_equality_predicate_becomes_all() -> None:
    out = neutralize_filters(f"SELECT region FROM {_SRC} WHERE region = $region", ["region"])
    assert out is not None
    assert len(_run(out)) == 3


def test_in_list_predicate_becomes_all() -> None:
    out = neutralize_filters(f"SELECT region FROM {_SRC} WHERE region IN ($region)", ["region"])
    assert out is not None
    assert len(_run(out)) == 3


def test_between_range_becomes_all() -> None:
    out = neutralize_filters(
        f"SELECT price FROM {_SRC} WHERE price BETWEEN $lo AND $hi", ["lo", "hi"]
    )
    assert out is not None
    assert len(_run(out)) == 3


def test_ilike_with_concat_becomes_all() -> None:
    out = neutralize_filters(
        f"SELECT region FROM {_SRC} WHERE region ILIKE '%' || $q || '%'", ["q"]
    )
    assert out is not None
    assert len(_run(out)) == 3


def test_only_the_all_predicate_is_stripped() -> None:
    # region = All, price still bound → the surviving $min filters normally.
    out = neutralize_filters(
        f"SELECT region FROM {_SRC} WHERE region = $region AND price >= $min", ["region"]
    )
    assert out is not None
    assert {r[0] for r in _run(out, {"min": 40})} == {"B", "C"}


def test_no_all_vars_returns_sql_unchanged() -> None:
    sql = f"SELECT region FROM {_SRC} WHERE region = $region"
    assert neutralize_filters(sql, []) == sql


def test_placeholder_outside_predicate_returns_none() -> None:
    assert neutralize_filters("SELECT $val AS n", ["val"]) is None
    assert neutralize_filters(f"SELECT region FROM {_SRC} LIMIT $n", ["n"]) is None


def test_unparseable_sql_returns_none() -> None:
    assert neutralize_filters("THIS IS NOT SQL (((", ["x"]) is None
