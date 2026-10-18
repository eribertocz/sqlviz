"""HTTP draft saves: author-only, conditional on revision, never parsed or executed."""

import pytest
from sqlviz_api.dependencies import get_db

ZERO = "sql-draft-v1:" + "0" * 64


def dashboard(client):
    response = client.post("/api/v1/dashboards", json={"name": "Sales"})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def path(owner):
    return f"/api/v1/dashboards/{owner}/sql-script/draft"


def read(client, owner):
    response = client.get(path(owner))
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    return response.json()


def save(client, owner, source, revision=None):
    return client.put(path(owner), json={
        "expected_revision": revision or read(client, owner)["revision"], "source": source,
    })


def state(client):
    return client.app.state.db_conn.execute(
        "SELECT id, sql_content, sql_draft_generation FROM dashboards ORDER BY id"
    ).fetchall()


def forbidden(*args, **kwargs):
    raise AssertionError("Draft endpoint parsed, executed SQL or used the database")


def test_new_dashboard_draft_is_empty_and_uninitialized(client):
    owner = dashboard(client)
    draft = read(client, owner)
    assert draft == {
        "version": 1, "dashboard_id": owner, "source": "",
        "revision": draft["revision"], "initialized": False,
    }
    assert draft["revision"].startswith("sql-draft-v1:") and len(draft["revision"]) == 77
    assert read(client, owner) == draft


def test_unfinished_text_is_saved_without_parsing_or_execution(client, monkeypatch):
    owner = dashboard(client)
    monkeypatch.setattr(client.app.state.sql_scripts, "parse", forbidden)
    monkeypatch.setattr(client.app.state.queries, "execute", forbidden)
    response = save(client, owner, "SELECT 'unfinished;\n-- 😀")
    assert response.status_code == 200, response.text
    saved = response.json()
    assert saved["source"] == "SELECT 'unfinished;\n-- 😀" and saved["initialized"] is True
    assert read(client, owner) == saved


def test_identical_text_and_empty_save_advance_the_revision(client):
    owner = dashboard(client)
    first = read(client, owner)
    empty = save(client, owner, "", first["revision"]).json()
    assert empty["revision"] != first["revision"] and empty["initialized"] is True
    again = save(client, owner, "", empty["revision"]).json()
    assert again["revision"] != empty["revision"]


def test_stale_revision_conflicts_without_echoing_or_writing(client):
    owner = dashboard(client)
    old = read(client, owner)["revision"]
    assert save(client, owner, "SELECT 1", old).status_code == 200
    before = state(client)
    response = save(client, owner, "SELECT 'private'", old)
    assert response.status_code == 409
    assert response.json()["code"] == "sql_draft_conflict"
    assert "SELECT" not in response.text
    assert state(client) == before


def test_another_dashboard_token_is_rejected(client):
    owner, other = dashboard(client), dashboard(client)
    response = save(client, owner, "SELECT 1", read(client, other)["revision"])
    assert response.status_code == 409
    assert read(client, owner)["initialized"] is False


def test_script_snapshot_exposes_the_same_draft_revision(client):
    owner = dashboard(client)
    saved = save(client, owner, "SELECT 2").json()
    snapshot = client.get(f"/api/v1/dashboards/{owner}/sql-script").json()
    assert snapshot["draft_source"] == saved["source"]
    assert snapshot["draft_revision"] == saved["revision"]
    assert snapshot["draft_initialized"] is True


def test_run_commit_invalidates_a_draft_revision_captured_before_it(client):
    owner = dashboard(client)
    captured = read(client, owner)["revision"]
    script = client.get(f"/api/v1/dashboards/{owner}/sql-script").json()
    committed = client.post(f"/api/v1/dashboards/{owner}/sql-script/commit", json={
        "sql": "SELECT 1", "expected_revision": script["revision"],
        "decisions": [{"kind": "create", "statement_index": 0, "creation_key": "k"}],
    })
    assert committed.status_code == 200, committed.text
    assert save(client, owner, "SELECT 3", captured).status_code == 409


def test_missing_dashboard_has_predictable_errors(client):
    assert client.get(path("missing")).status_code == 404
    response = save(client, "missing", "SELECT 1", ZERO)
    assert response.status_code == 404
    assert response.json()["code"] == "dashboard_not_found"


@pytest.mark.parametrize("body", [
    {"source": "SELECT 1"},
    {"expected_revision": ZERO},
    {"expected_revision": "sql-script-v1:" + "0" * 64, "source": ""},
    {"expected_revision": ZERO, "source": 1},
    {"expected_revision": ZERO, "source": "", "parse": True},
])
def test_transport_is_strict(client, body):
    owner = dashboard(client)
    before = state(client)
    assert client.put(path(owner), json=body).status_code == 422
    assert state(client) == before


def test_nul_and_oversized_drafts_are_rejected_without_writes(client):
    owner = dashboard(client)
    before = state(client)
    nul = save(client, owner, "SELECT 1\x00")
    assert nul.status_code == 422 and nul.json()["code"] == "sql_script_invalid"
    big = save(client, owner, "é" * 600_000)
    assert big.status_code in (413, 422)
    assert state(client) == before


@pytest.mark.parametrize("mode", [None, "public", "private"])
def test_anonymous_and_share_readers_cannot_read_or_save_drafts(client, mode):
    owner = dashboard(client)
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
    expected = 403 if mode else 401
    assert client.get(path(owner), headers=headers).status_code == expected
    response = client.put(path(owner), headers=headers,
                          json={"expected_revision": ZERO, "source": "SELECT 1"})
    assert response.status_code == expected
