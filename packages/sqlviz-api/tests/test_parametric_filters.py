"""End-to-end coverage for the 8 parametric filter control types.

Each case exercises the full pipeline: FilterEngine control detection
(no-values fallback) + real DuckDB execution with values bound.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

BASE = (
    "FROM (VALUES "
    "('A','2024-01-01'::DATE,10.0,'apple',true),"
    "('B','2024-06-01'::DATE,50.0,'banana',false),"
    "('C','2024-12-01'::DATE,90.0,'cherry',true)"
    ") t(region,fecha,price,name,active)"
)

CASES = [
    pytest.param(
        f"SELECT * {BASE} WHERE region = $region", {"region": "A"}, 1,
        ["dropdown"], "region", id="dropdown",
    ),
    pytest.param(
        f"SELECT * {BASE} WHERE region IN ($region)", {"region": ["A", "B"]}, 2,
        ["multiselect"], "region", id="multiselect",
    ),
    pytest.param(
        f"SELECT * {BASE} WHERE fecha = $fecha", {"fecha": "2024-01-01"}, 1,
        ["date_picker"], "fecha", id="date_picker",
    ),
    pytest.param(
        f"SELECT * {BASE} WHERE fecha BETWEEN $desde AND $hasta",
        {"desde": "2024-01-01", "hasta": "2024-07-01"}, 2,
        ["date_range_picker"], "desde,hasta", id="date_range_picker",
    ),
    pytest.param(
        f"SELECT * {BASE} WHERE price = $price", {"price": 50.0}, 1,
        ["numeric"], "price", id="numeric",
    ),
    pytest.param(
        f"SELECT * {BASE} WHERE price BETWEEN $min AND $max",
        {"min": 20.0, "max": 60.0}, 1,
        ["range_slider"], "min,max", id="range_slider",
    ),
    pytest.param(
        f"SELECT * {BASE} WHERE name ILIKE $q", {"q": "%an%"}, 1,
        ["search"], "q", id="search",
    ),
    pytest.param(
        f"SELECT * {BASE} WHERE active = $active", {"active": True}, 2,
        ["toggle"], "active", id="toggle",
    ),
]


def _make_panel(client: TestClient, sql: str) -> str:
    dash_id = client.post("/api/v1/dashboards", json={"name": "D"}).json()["id"]
    return client.post("/api/v1/panels", json={
        "dashboard_id": dash_id, "name": "P", "sql_content": sql,
    }).json()["id"]


@pytest.mark.parametrize(
    "sql,variables,expected_rows,expected_types,expected_variable", CASES,
)
def test_filter_type_detected_and_filters_data(
    client: TestClient,
    sql: str,
    variables: dict[str, object],
    expected_rows: int,
    expected_types: list[str],
    expected_variable: str,
) -> None:
    # No values yet: filter bar must show the correct control.
    panel_id = _make_panel(client, sql)
    body = client.post(f"/api/v1/panels/{panel_id}/execute").json()
    controls = body["inference_result"]["filter_controls"]
    assert [c["control_type"] for c in controls] == expected_types
    assert controls[0]["variable"] == expected_variable

    # With values bound: query must actually filter the data.
    panel_id2 = _make_panel(client, sql)
    resp = client.post(
        f"/api/v1/panels/{panel_id2}/execute", json={"variables": variables}
    )
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == expected_rows
