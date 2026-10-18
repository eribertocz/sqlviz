"""Author and public reader use the same analytical boundary over real HTTP."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlviz_api.services.queries import QueryLimits, QueryService


def _panel(client: TestClient, sql: str) -> tuple[str, str]:
    dash = client.post("/api/v1/dashboards", json={"name": "Isolation"}).json()["id"]
    panel = client.post(
        "/api/v1/panels",
        json={
            "dashboard_id": dash,
            "name": "P",
            "sql_content": sql,
        },
    ).json()["id"]
    token = client.post(f"/api/v1/dashboards/{dash}/share", json={"mode": "public"}).json()[
        "token"
    ]
    return panel, token


@pytest.mark.parametrize("reader", [False, True])
@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM _sqlviz_auth",
        "SELECT * FROM shares",
        "SELECT * FROM connections",
        "SELECT * FROM read_text('README.md')",
        "SELECT 1; DROP TABLE panels",
        "SELECT 1 WHERE 1=$filter; DROP TABLE panels",
        "SELECT session_secret FROM _sqlviz_auth WHERE password_hash=$password",
    ],
)
def test_sql_access_denied_even_in_reveal_path(client, reader, sql):
    panel, token = _panel(client, sql)
    response = client.post(
        f"/api/v1/panels/{panel}/execute", headers={"X-SQLviz-Share": token} if reader else {}
    )
    assert response.status_code == 403, response.text
    assert "data" not in response.json()


@pytest.mark.parametrize("reader", [False, True])
def test_domain_access_uses_same_boundary(client, reader):
    panel, token = _panel(client, "SELECT password_hash FROM _sqlviz_auth")
    response = client.post(
        f"/api/v1/panels/{panel}/filter-domain",
        json={
            "column": "password_hash",
            "kind": "distinct",
        },
        headers={"X-SQLviz-Share": token} if reader else {},
    )
    assert response.status_code == 403


@pytest.mark.parametrize("reader", [False, True])
def test_large_result_has_explicit_error_and_leaves_metadata_intact(client, reader):
    client.app.state.queries = QueryService(QueryLimits(max_rows=2))
    panel, token = _panel(client, "SELECT * FROM range(3)")
    response = client.post(
        f"/api/v1/panels/{panel}/execute", headers={"X-SQLviz-Share": token} if reader else {}
    )
    assert response.status_code == 413
    assert response.json()["code"] == "row_limit"
    assert client.get(f"/api/v1/panels/{panel}").status_code == 200


def test_local_data_execute_and_filter_domains_still_work(client):
    client.app.state.db_conn.execute(
        "CREATE TABLE sales AS SELECT * FROM (VALUES ('A', 5), ('B', 7)) t(region, amount)"
    )
    panel, token = _panel(client, "SELECT region, amount FROM sales WHERE region=$region")
    headers = {"X-SQLviz-Share": token}
    response = client.post(
        f"/api/v1/panels/{panel}/execute", headers=headers, json={"variables": {"region": "B"}}
    )
    assert response.status_code == 200, response.text
    assert response.json()["data"] == [{"region": "B", "amount": 7}]
    domain = client.post(
        f"/api/v1/panels/{panel}/filter-domain",
        headers=headers,
        json={"column": "region", "kind": "distinct"},
    )
    assert domain.status_code == 200, domain.text
    assert domain.json() == {"values": ["A", "B"]}
