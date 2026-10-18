"""Success is a server fact, conditional on a complete and current definition."""

import copy

import pytest
from sqlviz_api.services.sql_run_receipts import SqlRunReceiptError, SqlRunReceipts
from sqlviz_storage.sql_script_repository import SqlDefinitionReference


def run(client, source="-- exact source\r\nSELECT 1 AS a;\nSELECT 2 AS b"):
    owner = client.post("/api/v1/dashboards", json={"name": "D"}).json()["id"]
    path = f"/api/v1/dashboards/{owner}/sql-script"
    statements = client.post("/api/v1/sql/parse", json={"sql": source}).json()["statements"]
    commit = client.post(
        path + "/commit",
        json={
            "expected_revision": client.get(path).json()["revision"],
            "sql": source,
            "decisions": [
                {"kind": "create", "statement_index": i, "creation_key": str(i)}
                for i in range(len(statements))
            ],
        },
    )
    assert commit.status_code == 200, commit.text
    saved = commit.json()["snapshot"]
    definition = {"version": 1, "dashboard_id": owner, "revision": saved["definition_revision"]}
    items = []
    for binding in saved["publication"]["bindings"]:
        panel = binding["panel_id"]
        response = client.post(f"/api/v1/panels/{panel}/execute", json={"definition": definition})
        assert response.status_code == 200, response.text
        content = response.json()
        items.append(
            {
                "panel_id": panel,
                **{
                    field: content[field]
                    for field in (
                        "inference_result",
                        "execution_reference",
                        "execution_receipt",
                    )
                },
            }
        )
    return path, definition, items, source


def compose(client, path, definition, items):
    return client.post(path + "/compose", json={"definition": definition, "panels": items})


def finish(client, path, definition, token):
    return client.post(
        path + "/complete",
        json={
            "definition": definition,
            "completion_receipt": token,
        },
    )


def parent(client, definition):
    return client.get(f"/api/v1/dashboards/{definition['dashboard_id']}").json()


def test_completion_uses_server_source_and_time_preserves_draft_and_retries(client):
    path, definition, items, source = run(client)
    clock = [2_000_000_000.123456]
    client.app.state.sql_run_receipts._clock = lambda: clock[0]
    # The execution receipts predate this synthetic clock, so execute them again.
    for item in items:
        response = client.post(
            f"/api/v1/panels/{item['panel_id']}/execute", json={"definition": definition}
        ).json()
        item["execution_receipt"] = response["execution_receipt"]
        item["inference_result"] = response["inference_result"]
    composed = compose(client, path, definition, items)
    assert composed.status_code == 200, composed.text
    token = composed.json()["completion_receipt"]
    newer_draft = "SELECT 'new draft'"
    assert (
        client.patch(
            f"/api/v1/dashboards/{definition['dashboard_id']}", json={"sql_content": newer_draft}
        ).status_code
        == 200
    )
    clock[0] += 2
    done = finish(client, path, definition, token)
    assert done.status_code == 200, done.text
    assert done.json() == {
        "definition": definition,
        "last_run_sql": source,
        "last_run_at": "2033-05-18T03:33:20.123456+00:00",
    }
    assert parent(client, definition)["sql_content"] == newer_draft
    clock[0] += 3
    assert finish(client, path, definition, token).json() == done.json()
    assert parent(client, definition)["last_run_at"] == done.json()["last_run_at"]


@pytest.mark.parametrize("mutation", ["sql", "delete", "add", "identical_commit"])
def test_changed_definition_after_composition_cannot_record_success(client, mutation):
    path, definition, items, _ = run(client)
    token = compose(client, path, definition, items).json()["completion_receipt"]
    if mutation == "sql":
        client.patch(f"/api/v1/panels/{items[1]['panel_id']}", json={"sql_content": "SELECT 99"})
    elif mutation == "delete":
        client.delete(f"/api/v1/panels/{items[1]['panel_id']}")
    elif mutation == "add":
        client.post(
            "/api/v1/panels",
            json={
                "dashboard_id": definition["dashboard_id"],
                "name": "Extra",
                "sql_content": "SELECT 3",
            },
        )
    else:
        saved = client.get(path).json()
        response = client.post(
            path + "/commit",
            json={
                "expected_revision": saved["revision"],
                "sql": saved["publication"]["source"],
                "decisions": [
                    {"kind": "keep", "statement_index": i, "panel_id": item["panel_id"]}
                    for i, item in enumerate(items)
                ],
            },
        )
        assert response.status_code == 200
    before = parent(client, definition)
    response = finish(client, path, definition, token)
    assert response.status_code == 409, response.text
    assert parent(client, definition) == before
    assert before["last_run_at"] is None
    assert "SELECT 99" not in response.text


@pytest.mark.parametrize("mutation", ["inference", "panel", "token", "other_app", "missing"])
def test_forged_or_incompatible_execution_cannot_mint_completion(client, mutation):
    path, definition, items, _ = run(client)
    submitted = copy.deepcopy(items)
    if mutation == "inference":
        submitted[0]["inference_result"]["fallback_reason"] = "Forged"
    elif mutation == "panel":
        submitted[0]["execution_receipt"] = submitted[1]["execution_receipt"]
    elif mutation == "token":
        token = submitted[0]["execution_receipt"]
        submitted[0]["execution_receipt"] = token[:-1] + ("0" if token[-1] != "0" else "1")
    elif mutation == "other_app":
        client.app.state.sql_run_receipts = SqlRunReceipts()
    else:
        del submitted[0]["execution_receipt"]
    response = compose(client, path, definition, submitted)
    if mutation == "missing":
        assert response.status_code == 200
        assert response.json()["completion_receipt"] is None
    else:
        assert response.status_code == 409, response.text
    assert parent(client, definition)["last_run_at"] is None


def test_fallback_and_empty_script_cannot_mint_success_but_empty_rows_can(client):
    path, definition, items, _ = run(client, "SELECT $quantity AS quantity")
    composed = compose(client, path, definition, items)
    assert composed.status_code == 200, composed.text
    assert composed.json()["completion_receipt"] is None
    assert parent(client, definition)["last_run_at"] is None
    path, definition, items, _ = run(client, "-- no queries")
    assert compose(client, path, definition, items).json()["completion_receipt"] is None
    path, definition, items, _ = run(client, "SELECT 1 AS a WHERE false")
    token = compose(client, path, definition, items).json()["completion_receipt"]
    assert token is not None
    assert finish(client, path, definition, token).status_code == 200


@pytest.mark.parametrize("field", ["last_run_at", "last_run_sql"])
@pytest.mark.parametrize("value", [None, "", "SELECT 1", "2026-10-09T12:00:00Z"])
def test_patch_cannot_forge_or_clear_server_completion(client, field, value):
    path, definition, items, _ = run(client)
    token = compose(client, path, definition, items).json()["completion_receipt"]
    assert finish(client, path, definition, token).status_code == 200
    before = parent(client, definition)
    response = client.patch(
        f"/api/v1/dashboards/{definition['dashboard_id']}",
        json={field: value, "sql_content": "must not save"},
    )
    assert response.status_code == 422
    assert parent(client, definition) == before


def test_newer_completion_cannot_be_replaced_by_an_older_proof(client):
    path, definition, items, _ = run(client)
    first = compose(client, path, definition, items).json()["completion_receipt"]
    second = compose(client, path, definition, items).json()["completion_receipt"]
    assert finish(client, path, definition, second).status_code == 200
    before = parent(client, definition)
    assert finish(client, path, definition, first).status_code == 409
    assert parent(client, definition) == before


@pytest.mark.parametrize("kind", ["execution", "completion"])
def test_receipts_expire_and_do_not_survive_an_app_restart(kind):
    clock = [1000.0]
    receipts = SqlRunReceipts(clock=lambda: clock[0])
    definition = SqlDefinitionReference("d", "sql-definition-v1:" + "a" * 64)
    token = (
        receipts.execution(definition, "p", {}, executed=True)
        if kind == "execution"
        else receipts.completion(definition)
    )

    def verify(service):
        return (
            service.verify_execution(token, definition, "p", {})
            if kind == "execution"
            else service.verify_completion(token, definition)
        )

    assert verify(receipts)
    with pytest.raises(SqlRunReceiptError):
        verify(SqlRunReceipts(clock=lambda: clock[0]))
    clock[0] += receipts.TTL_SECONDS + 1
    with pytest.raises(SqlRunReceiptError):
        verify(receipts)


def test_authorization_and_execution_token_cannot_bypass_composition(client):
    path, definition, items, _ = run(client)
    assert finish(client, path, definition, items[0]["execution_receipt"]).status_code == 409
    token = compose(client, path, definition, items).json()["completion_receipt"]
    share = client.post(
        f"/api/v1/dashboards/{definition['dashboard_id']}/share", json={"mode": "public"}
    ).json()
    client.cookies.clear()
    assert finish(client, path, definition, token).status_code == 401
    assert (
        client.post(
            path + "/complete",
            headers={"X-SQLviz-Share": share["token"]},
            json={"definition": definition, "completion_receipt": token},
        ).status_code
        == 403
    )


@pytest.mark.parametrize("change", ["expired", "restart", "tampered"])
def test_invalid_completion_proof_preserves_previous_metadata(client, change):
    path, definition, items, _ = run(client)
    token = compose(client, path, definition, items).json()["completion_receipt"]
    before = parent(client, definition)
    if change == "expired":
        previous_clock = client.app.state.sql_run_receipts._clock
        client.app.state.sql_run_receipts._clock = lambda: previous_clock() + 901
    elif change == "restart":
        client.app.state.sql_run_receipts = SqlRunReceipts()
    else:
        token = token[:-1] + ("0" if token[-1] != "0" else "1")
    response = finish(client, path, definition, token)
    assert response.status_code == 409, response.text
    assert parent(client, definition) == before


@pytest.mark.parametrize("field", ["last_run_at", "sql", "last_run_sql"])
def test_completion_rejects_client_timestamps_and_sql(client, field):
    path, definition, items, _ = run(client)
    token = compose(client, path, definition, items).json()["completion_receipt"]
    before = parent(client, definition)
    response = client.post(
        path + "/complete",
        json={"definition": definition, "completion_receipt": token, field: "untrusted"},
    )
    assert response.status_code == 422
    assert parent(client, definition) == before


def test_incomplete_engine_output_cannot_mint_completion(client, monkeypatch):
    from sqlviz_api.routers import sql_script_commits

    path, definition, items, _ = run(client)
    monkeypatch.setattr(sql_script_commits, "compose_items", lambda *args: {"rows": []})
    response = compose(client, path, definition, items)
    assert response.status_code == 409
    assert "completion_receipt" not in response.json()


def test_execution_digest_accepts_unchanged_browser_json_numbers():
    receipts = SqlRunReceipts()
    definition = SqlDefinitionReference("d", "sql-definition-v1:" + "a" * 64)
    token = receipts.execution(
        definition, "p", {"weight": 1.0, "zero": -0.0, "nested": [0.0]}, executed=True
    )
    assert receipts.verify_execution(
        token, definition, "p", {"nested": [0], "zero": 0, "weight": 1}
    )


def test_deleted_dashboard_cannot_record_success(client):
    path, definition, items, _ = run(client)
    token = compose(client, path, definition, items).json()["completion_receipt"]
    assert client.delete(f"/api/v1/dashboards/{definition['dashboard_id']}").status_code == 204
    assert finish(client, path, definition, token).status_code == 409


def test_receipt_capacity_covers_maximum_unicode_legacy_ids():
    receipts = SqlRunReceipts()
    owner, panel = "🧠" * 256, "📊" * 256
    definition = SqlDefinitionReference(owner, "sql-definition-v1:" + "a" * 64)
    token = receipts.execution(definition, panel, {}, executed=True)
    assert len(token) <= receipts.MAX_TOKEN_LENGTH
    assert receipts.verify_execution(token, definition, panel, {})
    with pytest.raises(SqlRunReceiptError):
        receipts.verify_execution(token, definition, panel[:-1], {})
