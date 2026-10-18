"""HTTP admission, authorization and atomic publication on real project databases."""

from uuid import UUID

import duckdb
import pytest
from fastapi.testclient import TestClient
from sqlviz_api.dependencies import get_db
from sqlviz_api.main import create_app
from sqlviz_api.services.queries import QueryFailure
from sqlviz_storage.project_db import create_project, open_project
from sqlviz_storage.sql_script_repository import SqlScriptRepository


def dashboard(client):
    response = client.post("/api/v1/dashboards", json={"name": "Sales"})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def path(owner):
    return f"/api/v1/dashboards/{owner}/sql-script"


def snapshot(client, owner):
    response = client.get(path(owner))
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    return response.json()


def create(index=0, key="new"):
    return {"kind": "create", "statement_index": index, "creation_key": key}


def keep(index, panel):
    return {"kind": "keep", "statement_index": index, "panel_id": panel}


def commit(client, owner, *, sql="SELECT 1", decisions=None, revision=None):
    return client.post(path(owner) + "/commit", json={
        "sql": sql,
        "expected_revision": revision or snapshot(client, owner)["revision"],
        "decisions": [create()] if decisions is None else decisions,
    })


def rows(client):
    return {
        table: client.app.state.db_conn.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
        for table in ("dashboards", "panels", "dashboard_sql_scripts", "shares", "filter_memory")
    }


def forbidden(*args, **kwargs):
    raise AssertionError("Definition endpoint executed SQL or used an unauthorized database")


def test_snapshot_is_read_only_and_has_no_fabricated_legacy_publication(client, monkeypatch):
    owner = dashboard(client)
    before = rows(client)
    monkeypatch.setattr(client.app.state.sql_scripts, "parse", forbidden)
    monkeypatch.setattr(client.app.state.queries, "execute", forbidden)
    first = snapshot(client, owner)
    assert first == snapshot(client, owner)
    assert first["version"] == 1 and first["dashboard_id"] == owner
    assert len(first["revision"]) == 78 and first["revision"].startswith("sql-script-v1:")
    assert first["publication"] is None and first["panels"] == []
    assert rows(client) == before


def test_native_source_bindings_and_generated_ids_are_published_without_execution(
    client, monkeypatch
):
    owner = dashboard(client)
    old = snapshot(client, owner)
    source = "SELECT '😀;é' AS label;\nSELECT * FROM missing WHERE x = $x;"
    monkeypatch.setattr(client.app.state.queries, "execute", forbidden)
    response = commit(client, owner, sql=source, decisions=[create(0, "first"), create(1, "last")])
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    body = response.json()
    saved = body["snapshot"]
    assert body["version"] == 1 and saved == snapshot(client, owner)
    assert saved["revision"] != old["revision"] and saved["draft_source"] == source
    assert saved["publication"]["revision"] == 1 and saved["publication"]["source"] == source
    refs = body["created_panels"]
    assert [item["creation_key"] for item in refs] == ["first", "last"]
    ids = [item["panel_id"] for item in refs]
    assert len(set(ids)) == 2 and all(UUID(panel).version == 4 for panel in ids)
    assert not set(ids) & {"first", "last"}
    bindings = saved["publication"]["bindings"]
    assert [item["panel_id"] for item in bindings] == ids
    for binding, panel in zip(bindings, saved["panels"], strict=True):
        sliced = source.encode("utf-16-le")[
            binding["start_offset"] * 2:binding["end_offset"] * 2
        ].decode("utf-16-le")
        assert sliced == panel["sql_content"]
    assert bindings[1]["start_offset"] > source.index("\n")
    assert client.app.state.db_conn.execute(
        "SELECT last_run_sql, last_run_at FROM dashboards WHERE id = ?", [owner]
    ).fetchone() == (None, None)


def test_explicit_reorder_edit_creation_and_removal_preserve_manual_presentation(client):
    owner = dashboard(client)
    initial = commit(
        client, owner, sql="SELECT 1; SELECT 1", decisions=[create(0, "a"), create(1, "b")]
    )
    assert initial.status_code == 200, initial.text
    a, b = [item["panel_id"] for item in initial.json()["created_panels"]]
    other = dashboard(client)
    assert commit(client, other).status_code == 200
    other_before = snapshot(client, other)
    assert client.patch(f"/api/v1/panels/{b}/override", json={
        "field_name": "col_span", "user_value": "6",
    }).status_code == 200
    assert client.patch(f"/api/v1/panels/{b}/view-override", json={
        "field": "title", "value": "Revenue",
    }).status_code == 200
    response = commit(client, owner, sql="SELECT 20; SELECT 3", decisions=[
        keep(0, b), create(1, "c"), {"kind": "remove", "panel_id": a},
    ])
    assert response.status_code == 200, response.text
    assert response.json()["snapshot"]["publication"]["revision"] == 2
    assert response.json()["snapshot"]["panels"][0]["id"] == b
    assert client.get(f"/api/v1/panels/{a}").status_code == 404
    assert client.app.state.db_conn.execute(
        "SELECT col_span_user_override, selected_col_span, view_title FROM panels WHERE id = ?", [b]
    ).fetchone() == (6, 6, "Revenue")
    assert snapshot(client, other) == other_before


@pytest.mark.parametrize("decisions", [[], [create(1)], [create(), create()],
                                       [keep(0, "foreign")], [{"kind": "remove", "panel_id": "x"}]])
def test_invalid_or_incomplete_identity_has_no_writes(client, decisions):
    owner = dashboard(client)
    before = rows(client)
    response = commit(client, owner, decisions=decisions)
    assert response.status_code == 422, response.text
    assert response.json()["code"].startswith("sql_reconciliation_")
    assert rows(client) == before


@pytest.mark.parametrize("change", [
    {"expected_revision": None}, {"expected_revision": 1}, {"expected_revision": ""},
    {"expected_revision": "sql-script-v1:" + "A" * 64},
    {"expected_revision": "sql-script-v2:" + "0" * 64},
    {"expected_revision": "sql-script-v1:" + "0" * 64 + "\n"},
    {"sql": True}, {"plan": {}}, {"start_offset": 0}, {"panel_id": "new"},
    {"decisions": [{"kind": "guess", "statement_index": 0}]},
    {"decisions": [{"kind": "create", "statement_index": True, "creation_key": "a"}]},
    {"decisions": [{"kind": "create", "statement_index": 256, "creation_key": "a"}]},
    {"decisions": [{"kind": "create", "statement_index": 0, "creation_key": "a", "sql": "x"}]},
    {"decisions": [{"kind": "remove", "panel_id": "p"}] * 513},
])
def test_transport_rejects_coercion_and_client_plans(client, change):
    owner = dashboard(client)
    before = rows(client)
    body = {"sql": "SELECT 1", "expected_revision": snapshot(client, owner)["revision"],
            "decisions": [create()], **change}
    response = client.post(path(owner) + "/commit", json=body)
    assert response.status_code == 422, response.text
    assert rows(client) == before


@pytest.mark.parametrize("field", ["sql", "expected_revision", "decisions"])
def test_commit_requires_every_field(client, field):
    owner = dashboard(client)
    body = {"sql": "SELECT 1", "expected_revision": snapshot(client, owner)["revision"],
            "decisions": [create()]}
    del body[field]
    assert client.post(path(owner) + "/commit", json=body).status_code == 422


@pytest.mark.parametrize("mode", [None, "public", "private"])
def test_anonymous_and_share_readers_cannot_read_or_commit_author_state(client, monkeypatch, mode):
    owner = dashboard(client)
    other = dashboard(client)
    revision = snapshot(client, owner)["revision"]
    headers = {}
    if mode:
        grant = client.post(f"/api/v1/dashboards/{owner}/share", json={
            "mode": mode, "password": "reader-password",
        }).json()
        headers["X-SQLviz-Share"] = grant["token"]
        if mode == "private":
            session = client.app.state.authorization.viewer_sessions.issue(grant["id"])
            headers["X-SQLviz-Viewer-Session"] = session
    client.cookies.clear()
    client.app.dependency_overrides[get_db] = forbidden
    monkeypatch.setattr(client.app.state.sql_scripts, "parse", forbidden)
    for target in (owner, other, "missing"):
        assert client.get(path(target), headers=headers).status_code == (403 if mode else 401)
        response = client.post(path(target) + "/commit", headers=headers, json={
            "sql": "SELECT 1", "expected_revision": revision, "decisions": [create()],
        })
        assert response.status_code == (403 if mode else 401)


@pytest.mark.parametrize("mutation", ["sql", "override", "draft", "create", "delete"])
def test_any_relevant_legacy_change_invalidates_expected_state(client, mutation):
    owner = dashboard(client)
    first = commit(client, owner).json()
    revision = first["snapshot"]["revision"]
    panel = first["created_panels"][0]["panel_id"]
    if mutation == "sql":
        response = client.patch(f"/api/v1/panels/{panel}", json={"sql_content": "SELECT 9"})
    elif mutation == "override":
        response = client.patch(f"/api/v1/panels/{panel}/view-override", json={
            "field": "title", "value": "New title",
        })
    elif mutation == "draft":
        response = client.patch(f"/api/v1/dashboards/{owner}", json={"sql_content": "new draft"})
    elif mutation == "create":
        response = client.post("/api/v1/panels", json={
            "dashboard_id": owner, "name": "Extra", "sql_content": "SELECT 8",
        })
    else:
        response = client.delete(f"/api/v1/panels/{panel}")
    assert response.is_success, response.text
    before = rows(client)
    rejected = commit(client, owner, revision=revision, decisions=[keep(0, panel)])
    assert rejected.status_code == 409 and rejected.json()["code"] == "sql_script_write_conflict"
    assert rows(client) == before
    current = snapshot(client, owner)
    assert current["revision"] != revision
    if mutation in {"sql", "create", "delete"}:
        assert current["publication"] is None
    elif mutation == "draft":
        assert current["publication"]["source"] == "SELECT 1"
        assert current["draft_source"] == "new draft"


def test_replayed_commit_or_another_dashboard_token_cannot_duplicate_creations(client):
    owner = dashboard(client)
    revision = snapshot(client, owner)["revision"]
    assert commit(client, owner, revision=revision).status_code == 200
    before = rows(client)
    assert commit(client, owner, revision=revision).status_code == 409
    assert rows(client) == before
    other = dashboard(client)
    before = rows(client)
    assert commit(client, other, revision=snapshot(client, owner)["revision"]).status_code == 409
    assert rows(client) == before


def test_foreign_panel_cannot_be_adopted_with_a_current_target_revision(client):
    owner, other = dashboard(client), dashboard(client)
    panel = commit(client, other).json()["created_panels"][0]["panel_id"]
    before = rows(client)
    response = commit(client, owner, decisions=[keep(0, panel)])
    assert response.status_code == 422 and rows(client) == before


def test_all_panels_can_be_removed_only_by_explicit_decisions(client):
    owner = dashboard(client)
    first = commit(client, owner).json()
    panel = first["created_panels"][0]["panel_id"]
    before = rows(client)
    rejected = commit(client, owner, sql="-- empty script", decisions=[])
    assert rejected.status_code == 422 and rows(client) == before
    accepted = commit(client, owner, sql="-- empty script", decisions=[
        {"kind": "remove", "panel_id": panel},
    ])
    assert accepted.status_code == 200, accepted.text
    saved = accepted.json()["snapshot"]
    assert saved["panels"] == [] and saved["publication"]["bindings"] == []
    assert saved["publication"]["revision"] == 2 and saved["draft_source"] == "-- empty script"


def test_share_header_does_not_gain_author_rights_from_an_admin_cookie(client):
    owner = dashboard(client)
    token = client.post(
        f"/api/v1/dashboards/{owner}/share", json={"mode": "public"}
    ).json()["token"]
    revision = snapshot(client, owner)["revision"]
    before = rows(client)
    headers = {"X-SQLviz-Share": token}
    assert client.get(path(owner), headers=headers).status_code == 403
    assert client.post(path(owner) + "/commit", headers=headers, json={
        "sql": "SELECT 1", "expected_revision": revision, "decisions": [create()],
    }).status_code == 403
    assert rows(client) == before


def test_oversized_http_body_is_bounded_before_definition_writes(client):
    owner = dashboard(client)
    revision = snapshot(client, owner)["revision"]
    before = rows(client)
    response = client.post(path(owner) + "/commit", json={
        "sql": "SELECT '" + "a" * (1024 * 1024) + "'",
        "expected_revision": revision, "decisions": [create()],
    })
    assert response.status_code == 413 and response.json()["code"] == "body_limit"
    assert rows(client) == before


@pytest.mark.parametrize("sql,status,code", [
    ("SELECT 1; SELECT 'private_unfinished", 422, "sql_script_invalid"),
    ("SELECT 1; CREATE TABLE not_created (x INT)", 403, "query_policy"),
    ("SELECT 1; DELETE FROM panels", 403, "query_policy"),
    ("SELECT 1; SELECT 2 INTO not_created", 422, "sql_script_invalid"),
    ("SELECT '" + "a" * 100_000 + "'", 413, "sql_limit"),
    (";".join(["SELECT 1"] * 257), 413, "sql_script_limit"),
], ids=["syntax", "ddl", "dml", "select-into", "query-budget", "statement-budget"])
def test_native_syntax_and_application_query_policy_admit_entire_source_before_write(
    client, sql, status, code
):
    owner = dashboard(client)
    before = rows(client)
    response = commit(client, owner, sql=sql)
    assert response.status_code == status and response.json()["code"] == code, response.text
    assert "private_unfinished" not in response.text
    assert rows(client) == before


def test_native_valid_but_unsupported_validation_has_safe_error_and_no_write(client, monkeypatch):
    owner = dashboard(client)
    before = rows(client)

    def unsupported(sql):
        raise duckdb.ParserException("private SQL should never be echoed")

    monkeypatch.setattr(client.app.state.queries, "validate", unsupported)
    response = commit(client, owner)
    assert response.status_code == 422 and response.json()["code"] == "sql_commit_query_invalid"
    assert "private SQL" not in response.text and rows(client) == before


def test_parser_admission_busy_returns_retryable_error_without_writes(client, monkeypatch):
    owner = dashboard(client)
    before = rows(client)

    def busy(sql):
        raise QueryFailure(429, "sql_parse_busy", "SQL analysis is busy; retry shortly")

    monkeypatch.setattr(client.app.state.sql_scripts, "parse", busy)
    response = commit(client, owner)
    assert response.status_code == 429 and response.json()["code"] == "sql_parse_busy"
    assert rows(client) == before


def test_failure_after_database_mutations_returns_conflict_and_rolls_back(client, monkeypatch):
    owner = dashboard(client)
    revision = snapshot(client, owner)["revision"]
    before = rows(client)
    read = SqlScriptRepository._read
    calls = 0

    def fail_publication(repo, dashboard_id):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise duckdb.ConstraintException("private database conflict")
        return read(repo, dashboard_id)

    monkeypatch.setattr(SqlScriptRepository, "_read", fail_publication)
    response = commit(client, owner, revision=revision)
    assert calls == 2 and response.status_code == 409
    assert "private database" not in response.text and rows(client) == before


def test_corrupt_associations_fail_closed_without_exposing_source_or_writing(client):
    owner = dashboard(client)
    committed = commit(client, owner).json()
    client.app.state.db_conn.execute(
        "UPDATE dashboard_sql_scripts SET bindings_json = 'private corrupt data'"
    )
    before = rows(client)
    for response in [client.get(path(owner)), commit(
        client, owner, revision=committed["snapshot"]["revision"],
        decisions=[keep(0, committed["created_panels"][0]["panel_id"])],
    )]:
        assert response.status_code == 500
        assert response.json()["code"] == "sql_script_metadata_invalid"
        assert "private corrupt" not in response.text
    assert rows(client) == before


def test_missing_dashboard_and_stored_capacity_have_predictable_errors(client):
    assert client.get(path("missing")).status_code == 404
    assert commit(client, "missing", revision="sql-script-v1:" + "0" * 64).status_code == 404
    owner = dashboard(client)
    client.app.state.db_conn.execute(
        "INSERT INTO panels (id, dashboard_id, name, sql_content, created_at, updated_at) "
        "SELECT 'panel-' || i, ?, 'Panel', 'SELECT 1', 't', 't' FROM range(257) t(i)", [owner]
    )
    before = rows(client)
    for response in [client.get(path(owner)), commit(
        client, owner, revision="sql-script-v1:" + "0" * 64
    )]:
        assert response.status_code == 413 and response.json()["code"] == "sql_script_state_limit"
    assert rows(client) == before


def test_revision_exhaustion_cannot_wrap_or_publish(client):
    owner = dashboard(client)
    first = commit(client, owner).json()
    panel = first["created_panels"][0]["panel_id"]
    client.app.state.db_conn.execute("UPDATE dashboard_sql_scripts SET revision = ?", [2**63 - 1])
    revision = snapshot(client, owner)["revision"]
    before = rows(client)
    response = commit(client, owner, revision=revision, decisions=[keep(0, panel)])
    assert response.status_code == 413 and response.json()["code"] == "sql_script_state_limit"
    assert rows(client) == before


def test_publication_survives_file_reopen_and_demo_can_use_author_routes(tmp_path):
    project = str(tmp_path / "copy.sqlviz")
    conn = create_project(project)
    with TestClient(create_app(conn, demo_mode=True)) as browser:
        owner = dashboard(browser)
        response = commit(browser, owner)
        assert response.status_code == 200, response.text
        saved = response.json()["snapshot"]
    conn.close()
    reopened = open_project(project)
    try:
        with TestClient(create_app(reopened, demo_mode=True)) as browser:
            assert snapshot(browser, owner) == saved
    finally:
        reopened.close()


def test_openapi_declares_strict_decision_union_and_required_revision(client):
    document = client.get("/openapi.json").json()
    schemas = document["components"]["schemas"]
    request = schemas["SqlCommitRequest"]
    assert request["additionalProperties"] is False
    assert set(request["required"]) == {"sql", "expected_revision", "decisions"}
    assert request["properties"]["decisions"]["items"]["discriminator"]["propertyName"] == "kind"
    operation = document["paths"][path("{dashboard_id}") + "/commit"]["post"]
    assert {"401", "403", "404", "409", "413", "422", "429", "500"} <= operation["responses"].keys()
    assert operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"] \
        == "#/components/schemas/SqlCommitResponse"
