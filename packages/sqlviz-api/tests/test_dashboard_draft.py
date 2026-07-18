"""Draft auto-save fields on dashboards (UX spec v1.0 §Draft, v0.2.8).

The dashboard carries the exact editor text (`sql_content`) and the timestamp
of the last successful run (`last_run_at`), both patchable and returned by the
list/get endpoints so a refreshed browser can restore the draft and show
"Last run X ago".
"""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_new_dashboard_has_empty_draft_and_no_last_run(client: TestClient) -> None:
    d = client.post("/api/v1/dashboards", json={"name": "D"}).json()
    assert d["sql_content"] == ""
    assert d["last_run_at"] is None


def test_patch_draft_sql_content(client: TestClient) -> None:
    d = client.post("/api/v1/dashboards", json={"name": "D"}).json()
    upd = client.patch(
        f"/api/v1/dashboards/{d['id']}", json={"sql_content": "SELECT 42"}
    ).json()
    assert upd["sql_content"] == "SELECT 42"


def test_draft_survives_reload_via_get(client: TestClient) -> None:
    d = client.post("/api/v1/dashboards", json={"name": "D"}).json()
    client.patch(f"/api/v1/dashboards/{d['id']}", json={"sql_content": "SELECT 1;\nSELECT 2"})
    got = client.get(f"/api/v1/dashboards/{d['id']}").json()
    assert got["sql_content"] == "SELECT 1;\nSELECT 2"


def test_patch_last_run_at(client: TestClient) -> None:
    d = client.post("/api/v1/dashboards", json={"name": "D"}).json()
    ts = "2026-07-18T10:15:00+00:00"
    upd = client.patch(f"/api/v1/dashboards/{d['id']}", json={"last_run_at": ts}).json()
    assert upd["last_run_at"] == ts


def test_list_exposes_draft_and_last_run(client: TestClient) -> None:
    d = client.post("/api/v1/dashboards", json={"name": "D"}).json()
    client.patch(
        f"/api/v1/dashboards/{d['id']}",
        json={"sql_content": "SELECT 1", "last_run_at": "2026-07-18T10:00:00+00:00"},
    )
    row = next(r for r in client.get("/api/v1/dashboards").json() if r["id"] == d["id"])
    assert row["sql_content"] == "SELECT 1"
    assert row["last_run_at"] == "2026-07-18T10:00:00+00:00"


def test_empty_draft_can_be_cleared(client: TestClient) -> None:
    d = client.post("/api/v1/dashboards", json={"name": "D"}).json()
    client.patch(f"/api/v1/dashboards/{d['id']}", json={"sql_content": "SELECT 1"})
    upd = client.patch(f"/api/v1/dashboards/{d['id']}", json={"sql_content": ""}).json()
    assert upd["sql_content"] == ""


def test_last_run_sql_is_independent_of_draft(client: TestClient) -> None:
    # last_run_sql (for "Restore last run") is kept separate from the draft.
    d = client.post("/api/v1/dashboards", json={"name": "D"}).json()
    assert d["last_run_sql"] is None
    client.patch(
        f"/api/v1/dashboards/{d['id']}",
        json={"sql_content": "SELECT 1", "last_run_sql": "SELECT 1"},
    )
    # The user keeps editing the draft — last_run_sql must not change.
    upd = client.patch(
        f"/api/v1/dashboards/{d['id']}", json={"sql_content": "SELECT 2"}
    ).json()
    assert upd["sql_content"] == "SELECT 2"
    assert upd["last_run_sql"] == "SELECT 1"
