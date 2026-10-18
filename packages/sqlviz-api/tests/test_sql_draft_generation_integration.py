"""Existing HTTP writers advance the internal draft version without changing DTOs."""

from sqlviz_storage.sql_draft_repository import SqlDraftRepository


def test_existing_patch_advances_draft_even_for_identical_text_and_rename_does_not(client):
    owner = client.post("/api/v1/dashboards", json={"name": "D"}).json()["id"]
    drafts = SqlDraftRepository(client.app.state.db_conn)
    initial = drafts.read(owner)
    for _ in range(2):
        response = client.patch(f"/api/v1/dashboards/{owner}", json={"sql_content": ""})
        assert response.status_code == 200
    saved = drafts.read(owner)
    assert saved.initialized and saved.generation == 2 and saved.revision != initial.revision
    assert client.patch(f"/api/v1/dashboards/{owner}", json={"name": "Renamed"}).status_code == 200
    assert drafts.read(owner) == saved


def test_corrupt_draft_revision_returns_safe_error_instead_of_an_initial_snapshot(client):
    owner = client.post("/api/v1/dashboards", json={"name": "D"}).json()["id"]
    db = client.app.state.db_conn
    db.execute(
        "UPDATE dashboards SET sql_draft_generation = -1, "
        "sql_content = 'private_draft' WHERE id = ?",
        [owner],
    )
    response = client.get(f"/api/v1/dashboards/{owner}/sql-script")
    assert response.status_code == 500 and response.json()["code"] == "sql_draft_metadata_invalid"
    assert "private_draft" not in response.text and owner not in response.text


def test_exhaustion_rolls_back_patch_fields_and_allows_non_sql_edits(client):
    owner = client.post("/api/v1/dashboards", json={"name": "D"}).json()["id"]
    db = client.app.state.db_conn
    db.execute("UPDATE dashboards SET sql_draft_generation = ? WHERE id = ?", [2**63 - 1, owner])
    before = db.execute("SELECT * FROM dashboards").fetchall()
    response = client.patch(f"/api/v1/dashboards/{owner}", json={
        "name": "Must not change", "sql_content": "private_draft",
    })
    assert response.status_code == 413 and response.json()["code"] == "sql_draft_revision_limit"
    assert "private_draft" not in response.text
    assert db.execute("SELECT * FROM dashboards").fetchall() == before
    assert client.patch(f"/api/v1/dashboards/{owner}", json={"name": "Renamed"}).status_code == 200


def test_exhausted_run_commit_cannot_create_panels_or_associations(client):
    owner = client.post("/api/v1/dashboards", json={"name": "D"}).json()["id"]
    db = client.app.state.db_conn
    db.execute("UPDATE dashboards SET sql_draft_generation = ? WHERE id = ?", [2**63 - 1, owner])
    path = f"/api/v1/dashboards/{owner}/sql-script"
    initial = client.get(path).json()
    response = client.post(path + "/commit", json={
        "sql": "SELECT 1", "expected_revision": initial["revision"],
        "decisions": [{"kind": "create", "statement_index": 0, "creation_key": "new"}],
    })
    assert response.status_code == 413 and response.json()["code"] == "sql_draft_revision_limit"
    assert client.get(path).json() == initial
    assert db.execute("SELECT count(*) FROM panels").fetchone() == (0,)
    assert db.execute("SELECT count(*) FROM dashboard_sql_scripts").fetchone() == (0,)
