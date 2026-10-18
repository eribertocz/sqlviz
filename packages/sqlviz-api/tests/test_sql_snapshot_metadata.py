"""Reload metadata belongs to the same read snapshot as SQL definitions."""

from sqlviz_storage.panel_repository import PanelRepository


def test_snapshot_preserves_exact_draft_last_run_and_reports_legacy_without_writes(client):
    owner = client.post("/api/v1/dashboards", json={"name": "D"}).json()["id"]
    source = "-- español\r\nSELECT 'a;b'"
    db = client.app.state.db_conn
    db.execute(
        "UPDATE dashboards SET sql_content = ?, last_run_at = ?, last_run_sql = ? WHERE id = ?",
        [source, "2026-10-09T12:00:00Z", "SELECT 1", owner],
    )
    before = db.execute("SELECT * FROM dashboards").fetchall()
    response = client.get(f"/api/v1/dashboards/{owner}/sql-script")
    assert response.status_code == 200
    snapshot = response.json()
    assert snapshot["draft_source"] == source
    assert snapshot["last_run_at"] == "2026-10-09T12:00:00Z"
    assert snapshot["last_run_sql"] == "SELECT 1"
    assert snapshot["publication_status"] == "absent" and snapshot["publication"] is None
    assert db.execute("SELECT * FROM dashboards").fetchall() == before


def test_snapshot_distinguishes_stale_associations_from_absent_legacy_state(client):
    owner = client.post("/api/v1/dashboards", json={"name": "D"}).json()["id"]
    path = f"/api/v1/dashboards/{owner}/sql-script"
    before = client.get(path).json()
    response = client.post(
        path + "/commit",
        json={
            "sql": "SELECT 1",
            "expected_revision": before["revision"],
            "decisions": [{"kind": "create", "statement_index": 0, "creation_key": "a"}],
        },
    )
    assert response.status_code == 200
    saved = response.json()["snapshot"]
    assert saved["publication_status"] == "confirmed"
    assert saved["last_run_at"] is None and saved["last_run_sql"] is None
    panel = saved["panels"][0]["id"]
    with client.app.state.db_conn.cursor() as cursor:
        PanelRepository(cursor).update(panel, {"sql_content": "SELECT 2"})
    client.patch(f"/api/v1/dashboards/{owner}", json={"sql_content": ""})
    stale = client.get(path).json()
    assert stale["publication_status"] == "incompatible"
    assert stale["draft_source"] == "" and stale["publication"] is None
    assert stale["definition_revision"] is None


def test_parent_change_between_metadata_reads_does_not_mix_last_run_or_draft(client, monkeypatch):
    from sqlviz_storage.dashboard_repository import DashboardRepository

    owner = client.post("/api/v1/dashboards", json={"name": "D"}).json()["id"]
    db = client.app.state.db_conn
    db.execute(
        "UPDATE dashboards SET sql_content = 'SELECT old', last_run_sql = 'old', "
        "last_run_at = '2026-10-09T12:00:00Z' WHERE id = ?",
        [owner],
    )
    original = DashboardRepository.get

    def racing(repository, requested):
        result = original(repository, requested)
        with db.cursor() as competing:
            competing.execute(
                "UPDATE dashboards SET sql_content = 'SELECT new', last_run_sql = 'new', "
                "last_run_at = '2026-10-09T13:00:00Z' WHERE id = ?",
                [owner],
            )
        return result

    monkeypatch.setattr(DashboardRepository, "get", racing)
    response = client.get(f"/api/v1/dashboards/{owner}/sql-script")
    assert response.status_code == 200
    assert response.json()["draft_source"] == "SELECT old"
    assert response.json()["last_run_sql"] == "old"
    assert response.json()["last_run_at"] == "2026-10-09T12:00:00Z"
    assert db.execute("SELECT sql_content, last_run_sql FROM dashboards").fetchone() == (
        "SELECT new",
        "new",
    )
