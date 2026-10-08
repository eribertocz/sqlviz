"""Author-only parse contract; analysis never writes or executes project SQL."""

import pytest
from sqlviz_api.dependencies import get_db


def test_parse_preserves_source_offsets_without_using_project_or_execution(client, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("SQL analysis accessed project or executed a query")

    client.app.dependency_overrides[get_db] = forbidden
    monkeypatch.setattr(client.app.state.queries, "execute", forbidden)
    response = client.post("/api/v1/sql/parse", json={
        "sql": "SELECT '😀;é';\nSELECT * FROM missing WHERE x = $x;",
    })
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    body = response.json()
    assert body["version"] == 1 and body["dialect"] == "duckdb"
    assert [statement["sql"] for statement in body["statements"]] == [
        "SELECT '😀;é'", "SELECT * FROM missing WHERE x = $x;",
    ]
    assert body["statements"][1]["start_offset"] == 15


def test_analysis_of_commands_does_not_execute_them(client):
    response = client.post("/api/v1/sql/parse", json={
        "sql": "CREATE TABLE parser_did_not_create_it(x INT); "
               "INSERT INTO parser_did_not_create_it VALUES (1)",
    })
    assert response.status_code == 200
    assert len(response.json()["statements"]) == 2
    assert client.app.state.db_conn.execute(
        "SELECT count(*) FROM information_schema.tables "
        "WHERE table_name = 'parser_did_not_create_it'",
    ).fetchone()[0] == 0


def test_invalid_script_has_no_partial_result_or_source_echo(client):
    response = client.post("/api/v1/sql/parse", json={
        "sql": "SELECT 1; SELECT 'private_unfinished",
    })
    assert response.status_code == 422
    assert response.json()["code"] == "sql_script_invalid"
    assert "statements" not in response.json() and "private_unfinished" not in response.text


@pytest.mark.parametrize("body", [{}, {"sql": None}, {"sql": 1}, {"sql": True},
                                  {"sql": []}, {"sql": "SELECT 1", "execute": True}])
def test_request_contract_is_strict(client, body):
    assert client.post("/api/v1/sql/parse", json=body).status_code == 422


def test_invalid_unicode_is_rejected_predictably(client):
    response = client.post("/api/v1/sql/parse", content='{"sql":"\\ud800"}',
                           headers={"Content-Type": "application/json"})
    # Pydantic's JSON boundary can reject a surrogate before the source service.
    assert response.status_code == 422
    assert "detail" in response.json() and "statements" not in response.json()


def test_comment_only_script_has_no_phantom_panels(client):
    response = client.post("/api/v1/sql/parse", json={"sql": "; -- a;\n/* b; */ ;"})
    assert response.status_code == 200 and response.json()["statements"] == []


def test_anonymous_and_viewer_credentials_cannot_parse_author_sql(client):
    dashboard = client.post("/api/v1/dashboards", json={"name": "Reader"}).json()["id"]
    token = client.post(
        f"/api/v1/dashboards/{dashboard}/share", json={"mode": "public"},
    ).json()["token"]
    client.cookies.clear()
    assert client.post("/api/v1/sql/parse", json={"sql": "SELECT 1"}).status_code == 401
    assert client.post("/api/v1/sql/parse", json={"sql": "SELECT 1"},
                       headers={"X-SQLviz-Share": token}).status_code == 403


def test_openapi_declares_the_typed_request_and_response(client):
    schema = client.get("/openapi.json").json()
    operation = schema["paths"]["/api/v1/sql/parse"]["post"]
    assert operation["requestBody"]["content"]["application/json"]["schema"]["$ref"] \
        == "#/components/schemas/SqlScriptParseRequest"
    assert operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"] \
        == "#/components/schemas/SqlScriptParseResponse"
