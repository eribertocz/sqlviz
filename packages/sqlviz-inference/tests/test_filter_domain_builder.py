"""Tests for the filter-domain query builder (filters/domain.py)."""

from __future__ import annotations

import duckdb
from sqlviz_inference.filters.domain import build_domain_query

_SRC = "(VALUES ('A',10.0),('B',20.0),('A',30.0),('C',5.0)) t(region,price)"


def _run(sql: str) -> list[tuple[object, ...]]:
    return duckdb.connect(":memory:").execute(sql).fetchall()


def test_distinct_strips_where_and_dedups() -> None:
    q = build_domain_query(
        f"SELECT * FROM {_SRC} WHERE region = $region", "region", "distinct"
    )
    assert q is not None
    assert _run(q) == [("A",), ("B",), ("C",)]


def test_range_returns_min_max_row() -> None:
    q = build_domain_query(
        f"SELECT * FROM {_SRC} WHERE price BETWEEN $lo AND $hi", "price", "range"
    )
    assert q is not None
    assert _run(q) == [(5.0, 30.0)]


def test_distinct_survives_group_by_and_order() -> None:
    q = build_domain_query(
        f"SELECT region, count(*) c FROM {_SRC} "
        "WHERE region IN ($r) GROUP BY region ORDER BY c DESC",
        "region", "distinct",
    )
    assert q is not None
    assert _run(q) == [("A",), ("B",), ("C",)]


def test_unparseable_returns_none() -> None:
    assert build_domain_query("NOT SQL !!!", "x", "distinct") is None


def test_no_from_returns_none() -> None:
    assert build_domain_query("SELECT 1 AS x", "x", "distinct") is None


def test_unknown_kind_returns_none() -> None:
    assert build_domain_query(
        f"SELECT * FROM {_SRC} WHERE region = $r", "region", "bogus"
    ) is None
