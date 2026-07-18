"""Tests for POST /api/v1/panels/{panel_id}/filter-domain.

The endpoint returns the domain of a filter column so the UI can render a rich
control (dropdown options / slider bounds) instead of a bare text box. It is
best-effort: anything it cannot parse or execute yields an empty domain rather
than an error, so the frontend degrades to a text/number input.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

BASE = "FROM (VALUES ('A',10.0),('B',20.0),('A',30.0),('C',5.0)) t(region,price)"


def _make_panel(client: TestClient, sql: str) -> str:
    dash_id = client.post("/api/v1/dashboards", json={"name": "D"}).json()["id"]
    return client.post("/api/v1/panels", json={
        "dashboard_id": dash_id, "name": "P", "sql_content": sql,
    }).json()["id"]


def test_distinct_returns_sorted_unique_values(client: TestClient) -> None:
    pid = _make_panel(client, f"SELECT * {BASE} WHERE region = $region")
    body = client.post(
        f"/api/v1/panels/{pid}/filter-domain",
        json={"column": "region", "kind": "distinct"},
    ).json()
    assert body["values"] == ["A", "B", "C"]


def test_distinct_ignores_the_parametric_where(client: TestClient) -> None:
    # IN ($region) filters rows, but the domain must reflect the full column.
    pid = _make_panel(
        client,
        f"SELECT region, count(*) {BASE} WHERE region IN ($region) GROUP BY region",
    )
    body = client.post(
        f"/api/v1/panels/{pid}/filter-domain",
        json={"column": "region", "kind": "distinct"},
    ).json()
    assert body["values"] == ["A", "B", "C"]


def test_range_returns_min_and_max(client: TestClient) -> None:
    pid = _make_panel(client, f"SELECT * {BASE} WHERE price BETWEEN $min AND $max")
    body = client.post(
        f"/api/v1/panels/{pid}/filter-domain",
        json={"column": "price", "kind": "range"},
    ).json()
    assert body["min"] == 5.0
    assert body["max"] == 30.0


def test_unparseable_sql_returns_empty_domain(client: TestClient) -> None:
    pid = _make_panel(client, "THIS IS NOT SQL $x")
    body = client.post(
        f"/api/v1/panels/{pid}/filter-domain",
        json={"column": "x", "kind": "distinct"},
    ).json()
    assert body["values"] == []


def test_unknown_panel_returns_404(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/panels/does-not-exist/filter-domain",
        json={"column": "x", "kind": "distinct"},
    )
    assert resp.status_code == 404
