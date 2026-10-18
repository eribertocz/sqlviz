"""Run provenance across execution, fallback and composition on real project files."""

import copy

import duckdb
import pytest
from sqlviz_api.routers import compose as compose_router
from sqlviz_api.routers import panels as panels_router
from sqlviz_storage.panel_repository import PanelRepository


def setup_run(client, source="SELECT 1 AS a;\nSELECT 2 AS b"):
    owner = client.post("/api/v1/dashboards", json={"name": "D"}).json()["id"]
    prefix = f"/api/v1/dashboards/{owner}/sql-script"
    before = client.get(prefix).json()
    statements = client.post("/api/v1/sql/parse", json={"sql": source}).json()["statements"]
    receipt = client.post(
        prefix + "/commit",
        json={
            "sql": source,
            "expected_revision": before["revision"],
            "decisions": [
                {"kind": "create", "statement_index": index, "creation_key": f"new-{index}"}
                for index in range(len(statements))
            ],
        },
    )
    assert receipt.status_code == 200, receipt.text
    saved = receipt.json()["snapshot"]
    definition = {"version": 1, "dashboard_id": owner, "revision": saved["definition_revision"]}
    ids = [binding["panel_id"] for binding in saved["publication"]["bindings"]]
    return prefix, definition, ids


def state(client):
    with client.app.state.db_conn.cursor() as db:
        return {
            table: db.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
            for table in ("dashboards", "panels", "dashboard_sql_scripts")
        }


def execute(client, definition, panel):
    return client.post(f"/api/v1/panels/{panel}/execute", json={"definition": definition})


def executed_items(client, definition, ids):
    items = []
    for panel in ids:
        result = execute(client, definition, panel)
        assert result.status_code == 200, result.text
        content = result.json()
        assert content["execution_reference"] == {
            "version": 1,
            "panel_id": panel,
            "definition": definition,
        }
        items.append(
            {
                "panel_id": panel,
                "inference_result": content["inference_result"],
                "execution_reference": content["execution_reference"],
            }
        )
    return items


def forbidden(*args, **kwargs):
    raise AssertionError("A rejected definition reached calculation")


def test_reference_stays_stable_through_execution_drafts_and_compatible_presentation(client):
    prefix, definition, ids = setup_run(client)
    original_snapshot = client.get(prefix).json()
    items = executed_items(client, definition, ids)
    assert (
        client.patch(
            f"/api/v1/dashboards/{definition['dashboard_id']}",
            json={
                "sql_content": "SELECT 'a newer unsaved definition'",
            },
        ).status_code
        == 200
    )
    assert (
        client.patch(
            f"/api/v1/panels/{ids[0]}/view-override",
            json={
                "field": "title",
                "value": "My title",
            },
        ).status_code
        == 200
    )
    assert (
        client.patch(
            f"/api/v1/panels/{ids[0]}/override",
            json={
                "field_name": "col_span",
                "user_value": "6",
            },
        ).status_code
        == 200
    )
    changed = client.get(prefix).json()
    assert changed["revision"] != original_snapshot["revision"]
    assert changed["definition_revision"] == definition["revision"]
    before = state(client)
    response = client.post(prefix + "/compose", json={"definition": definition, "panels": items})
    assert response.status_code == 200, response.text
    assert response.json()["definition"] == definition
    assert {panel["panel_id"] for row in response.json()["rows"] for panel in row["panels"]} == set(
        ids
    )
    assert state(client) == before  # Composition verifies metadata without writing it.


@pytest.mark.parametrize("change", ["sql", "order", "delete", "create", "repeat_commit"])
def test_changed_definition_is_rejected_before_query_or_inference(client, monkeypatch, change):
    prefix, definition, ids = setup_run(client)
    if change == "repeat_commit":
        saved = client.get(prefix).json()
        response = client.post(
            prefix + "/commit",
            json={
                "sql": saved["publication"]["source"],
                "expected_revision": saved["revision"],
                "decisions": [
                    {"kind": "keep", "statement_index": index, "panel_id": panel}
                    for index, panel in enumerate(ids)
                ],
            },
        )
        assert response.status_code == 200, response.text
    elif change == "create":
        client.post(
            "/api/v1/panels",
            json={
                "dashboard_id": definition["dashboard_id"],
                "name": "Extra",
                "sql_content": "SELECT 3",
            },
        )
    elif change == "delete":
        client.delete(f"/api/v1/panels/{ids[1]}")
    else:
        client.patch(
            f"/api/v1/panels/{ids[1]}",
            json={"sql_content": "SELECT 3"} if change == "sql" else {"sort_order": 9},
        )
    before = state(client)
    monkeypatch.setattr(client.app.state.queries, "execute", forbidden)
    monkeypatch.setattr(panels_router.sqlviz_inference, "infer", forbidden)
    response = execute(client, definition, ids[0])
    assert response.status_code == 409 and response.json()["code"] == "sql_definition_conflict"
    assert "SELECT" not in response.text and state(client) == before


def test_peer_sql_changed_after_query_cannot_publish_inference_for_an_old_script(
    client, monkeypatch
):
    _, definition, ids = setup_run(client)
    original = client.app.state.queries.execute
    after_edit = None

    def racing(*args, **kwargs):
        nonlocal after_edit
        result = original(*args, **kwargs)
        with client.app.state.db_conn.cursor() as competing:
            PanelRepository(competing).update(ids[1], {"sql_content": "SELECT 99 AS secret"})
        after_edit = state(client)
        return result

    monkeypatch.setattr(client.app.state.queries, "execute", racing)
    response = execute(client, definition, ids[0])
    assert response.status_code == 409, response.text
    assert "secret" not in response.text and "data" not in response.json()
    assert state(client) == after_edit
    assert client.get(f"/api/v1/panels/{ids[0]}").json()["fingerprint"] is None


@pytest.mark.parametrize(
    "source, syntax_error",
    [
        ("SELECT $value AS n; SELECT 2 AS peer", False),
        ("SELECT region FROM missing_reveal WHERE region = $region; SELECT 2 AS peer", False),
        ("SELECT 1 AS n; SELECT 2 AS peer", True),
    ],
)
def test_fallback_also_returns_a_definition_reference(client, monkeypatch, source, syntax_error):
    _, definition, ids = setup_run(client, source)
    if syntax_error:

        def bad_syntax(*args, **kwargs):
            raise duckdb.ParserException("synthetic syntax failure")

        monkeypatch.setattr(client.app.state.queries, "execute", bad_syntax)
    before = state(client)
    response = execute(client, definition, ids[0])
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["data"] == [] and result["inference_result"]["fallback_applied"]
    assert result["execution_reference"]["definition"] == definition
    assert result["query_executed"] is False and result["execution_receipt"]
    assert state(client) == before


def test_definition_changed_during_fallback_inference_is_rejected_without_writes(
    client, monkeypatch
):
    _, definition, ids = setup_run(client, "SELECT $value AS n; SELECT 2 AS peer")
    original = panels_router.sqlviz_inference.infer
    after_edit = None

    def racing(*args, **kwargs):
        nonlocal after_edit
        result = original(*args, **kwargs)
        with client.app.state.db_conn.cursor() as competing:
            PanelRepository(competing).update(ids[1], {"sql_content": "SELECT 99 AS secret"})
        after_edit = state(client)
        return result

    monkeypatch.setattr(panels_router.sqlviz_inference, "infer", racing)
    response = execute(client, definition, ids[0])
    assert response.status_code == 409 and "data" not in response.json()
    assert state(client) == after_edit


def test_definition_changed_between_queries_and_compose_is_rejected_without_calculation(
    client,
    monkeypatch,
):
    prefix, definition, ids = setup_run(client)
    items = executed_items(client, definition, ids)
    client.patch(f"/api/v1/panels/{ids[1]}", json={"sql_content": "SELECT 99"})
    before = state(client)
    monkeypatch.setattr(compose_router.DashboardEngine, "compose", forbidden)
    response = client.post(prefix + "/compose", json={"definition": definition, "panels": items})
    assert response.status_code == 409 and state(client) == before


@pytest.mark.parametrize(
    "change, status",
    [
        ("missing", 409),
        ("extra", 409),
        ("order", 409),
        ("duplicate", 422),
        ("mixed_reference", 422),
        ("wrong_panel", 422),
        ("wrong_path", 409),
    ],
)
def test_compose_rejects_incomplete_mixed_or_foreign_provenance(client, change, status):
    prefix, definition, ids = setup_run(client)
    items = executed_items(client, definition, ids)
    if change == "missing":
        items.pop()
    elif change == "extra":
        extra = copy.deepcopy(items[0])
        extra["panel_id"] = extra["execution_reference"]["panel_id"] = "another"
        items.append(extra)
    elif change == "order":
        items.reverse()
    elif change == "duplicate":
        items.append(items[0])
    elif change == "mixed_reference":
        items[0]["execution_reference"]["definition"]["revision"] = "sql-definition-v1:" + "0" * 64
    elif change == "wrong_panel":
        items[0]["execution_reference"]["panel_id"] = ids[1]
    elif change == "wrong_path":
        other = client.post("/api/v1/dashboards", json={"name": "Other"}).json()["id"]
        prefix = f"/api/v1/dashboards/{other}/sql-script"
    before = state(client)
    response = client.post(prefix + "/compose", json={"definition": definition, "panels": items})
    assert response.status_code == status, response.text
    assert state(client) == before


def test_empty_script_still_requires_a_current_definition_when_composing(client):
    prefix, definition, ids = setup_run(client, "-- an intentionally empty dashboard")
    assert ids == []
    response = client.post(prefix + "/compose", json={"definition": definition, "panels": []})
    assert response.status_code == 200 and response.json() == {
        "rows": [], "definition": definition, "completion_receipt": None,
    }
    client.post(
        "/api/v1/panels",
        json={
            "dashboard_id": definition["dashboard_id"],
            "name": "Added",
            "sql_content": "SELECT 3",
        },
    )
    assert (
        client.post(prefix + "/compose", json={"definition": definition, "panels": []}).status_code
        == 409
    )


@pytest.mark.parametrize(
    "value", [None, True, 1, "sql-script-v1:" + "0" * 64, "sql-definition-v1:" + "G" * 64]
)
def test_invalid_definition_reference_is_rejected_without_execution(client, monkeypatch, value):
    _, definition, ids = setup_run(client)
    definition["revision"] = value
    before = state(client)
    monkeypatch.setattr(client.app.state.queries, "execute", forbidden)
    assert execute(client, definition, ids[0]).status_code == 422
    assert state(client) == before


def test_anonymous_and_share_requests_cannot_use_author_definition_endpoints(client, monkeypatch):
    prefix, definition, ids = setup_run(client)
    items = executed_items(client, definition, ids)
    share = client.post(
        f"/api/v1/dashboards/{definition['dashboard_id']}/share",
        json={
            "mode": "public",
        },
    ).json()
    before = state(client)
    client.cookies.clear()
    monkeypatch.setattr(client.app.state.queries, "execute", forbidden)
    assert execute(client, definition, ids[0]).status_code == 401
    assert (
        client.post(
            prefix + "/compose", json={"definition": definition, "panels": items}
        ).status_code
        == 401
    )
    headers = {"X-SQLviz-Share": share["token"]}
    assert (
        client.post(
            f"/api/v1/panels/{ids[0]}/execute", headers=headers, json={"definition": definition}
        ).status_code
        == 403
    )
    assert (
        client.post(
            prefix + "/compose", headers=headers, json={"definition": definition, "panels": items}
        ).status_code
        == 403
    )
    assert state(client) == before


@pytest.mark.parametrize("version", [True, "1", 1.0, 2])
def test_reference_version_does_not_coerce_boolean_string_or_float(client, monkeypatch, version):
    _, definition, ids = setup_run(client)
    definition["version"] = version
    before = state(client)
    monkeypatch.setattr(client.app.state.queries, "execute", forbidden)
    response = execute(client, definition, ids[0])
    assert response.status_code == 422 and state(client) == before
