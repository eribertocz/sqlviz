"""Author and viewer share strict parameter rules over real API and DuckDB."""

from __future__ import annotations

import json

import pytest
from sqlviz_api.request_limits import MAX_FILTER_BODY_BYTES


def panel(client, sql):
    dash = client.post("/api/v1/dashboards", json={"name": "Parameters"}).json()["id"]
    pid = client.post(
        "/api/v1/panels", json={"dashboard_id": dash, "name": "P", "sql_content": sql}
    ).json()["id"]
    token = client.post(f"/api/v1/dashboards/{dash}/share", json={"mode": "public"}).json()["token"]
    return pid, token


@pytest.mark.parametrize("reader", [False, True])
@pytest.mark.parametrize(
    ("value", "status"),
    [
        ({"nested": "synthetic-canary"}, 422),
        (["synthetic-canary", 2], 422),
        ([None], 422),
        ("synthetic-canary" * 400, 413),
        (list(range(501)), 413),
        (float("nan"), 422),
        (2**128, 422),
        ("\ud800", 422),
    ],
    ids=["object", "mixed", "null-list", "long-text", "long-list", "nan", "integer", "unicode"],
)
def test_invalid_values_fail_without_sql_or_value_echo(client, reader, value, status):
    pid, token = panel(client, "SELECT CAST($value AS INTEGER) AS value")
    before = client.app.state.db_conn.execute("SELECT * FROM panels WHERE id=?", [pid]).fetchone()
    response = client.post(
        f"/api/v1/panels/{pid}/execute",
        headers={
            "Content-Type": "application/json",
            **({"X-SQLviz-Share": token} if reader else {}),
        },
        content=json.dumps({"variables": {"value": value}}),
    )
    assert response.status_code == status, response.text
    assert "synthetic-canary" not in response.text
    assert "data" not in response.json()
    assert (
        client.app.state.db_conn.execute("SELECT * FROM panels WHERE id=?", [pid]).fetchone()
        == before
    )


def test_sql_cast_errors_do_not_echo_values(client):
    pid, token = panel(client, "SELECT CAST($value AS DATE) AS value")
    response = client.post(
        f"/api/v1/panels/{pid}/execute",
        headers={"X-SQLviz-Share": token},
        json={"variables": {"value": "synthetic-canary"}},
    )
    assert response.status_code == 422
    assert "synthetic-canary" not in response.text


def test_strings_with_sql_fragments_are_bound_as_data(client):
    pid, _ = panel(client, "SELECT $value AS value")
    attack = "A'); DELETE FROM dashboards; --"
    response = client.post(f"/api/v1/panels/{pid}/execute", json={"variables": {"value": attack}})
    assert response.json()["data"] == [{"value": attack}]
    assert client.get(f"/api/v1/panels/{pid}").status_code == 200


def test_literal_and_comment_dollars_do_not_create_filters(client):
    pid, _ = panel(client, "SELECT '$literal' AS note -- region = $comment\n")
    response = client.post(f"/api/v1/panels/{pid}/execute")
    assert response.status_code == 200
    assert response.json()["data"] == [{"note": "$literal"}]
    assert response.json()["inference_result"]["filter_controls"] == []


def test_list_binding_does_not_rewrite_a_string(client):
    pid, _ = panel(
        client,
        "SELECT 'IN ($names)' AS note, name FROM (VALUES ('A'),('B')) t(name) "
        "WHERE name IN ($names)",
    )
    response = client.post(f"/api/v1/panels/{pid}/execute", json={"variables": {"names": ["B"]}})
    assert response.status_code == 200, response.text
    assert response.json()["data"] == [{"note": "IN ($names)", "name": "B"}]


def test_case_names_work_for_all_and_selected_values(client):
    pid, _ = panel(client, "SELECT region FROM (VALUES ('A'),('B')) t(region) WHERE region=$Region")
    all_response = client.post(f"/api/v1/panels/{pid}/execute")
    assert len(all_response.json()["data"]) == 2
    response = client.post(f"/api/v1/panels/{pid}/execute", json={"variables": {"REGION": "A"}})
    assert response.json()["data"] == [{"region": "A"}]


def test_body_limit_applies_before_parsing_and_to_chunked_uploads(client):
    pid, _ = panel(client, "SELECT 1")
    path = f"/api/v1/panels/{pid}/execute"
    for content in [b"x" * (MAX_FILTER_BODY_BYTES + 1), iter([b"x" * 65536] * 3)]:
        response = client.post(path, content=content)
        assert response.status_code == 413
        assert response.json()["code"] == "body_limit"
        assert response.headers["cache-control"] == "no-store"
    assert client.post(path).status_code == 200


@pytest.mark.parametrize("kind", ["not-a-kind", 42])
def test_filter_domain_kind_has_a_strict_contract(client, kind):
    pid, _ = panel(client, "SELECT 1")
    response = client.post(
        f"/api/v1/panels/{pid}/filter-domain", json={"column": "value", "kind": kind}
    )
    assert response.status_code == 422
    assert "input" not in response.json()["detail"][0]


def test_http_validation_errors_do_not_repeat_input(client):
    pid, _ = panel(client, "SELECT 1")
    response = client.post(f"/api/v1/panels/{pid}/execute", json={"variables": "synthetic-canary"})
    assert response.status_code == 422
    assert "synthetic-canary" not in response.text


def test_product_version_is_shared_by_api_and_creation_metadata(client):
    from sqlviz_core.version import __version__

    assert client.app.version == __version__
    assert client.get("/api/v1/meta").json()["version"] == __version__
    assert client.app.state.db_conn.execute(
        "SELECT value FROM _sqlviz_meta WHERE key='version'"
    ).fetchone() == (__version__,)
