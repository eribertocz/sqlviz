"""Read-only author preflight uses native parsing and persisted dashboard ownership."""

import pytest


def existing(client):
    dashboard = client.post("/api/v1/dashboards", json={"name": "Sales"}).json()["id"]
    panels = [
        client.post(
            "/api/v1/panels",
            json={
                "dashboard_id": dashboard,
                "name": name,
                "sql_content": "SELECT 1",
            },
        ).json()["id"]
        for name in ("Margin", "Revenue")
    ]
    return dashboard, panels


def request(dashboard=None, panels=(), **kwargs):
    return {
        "sql": "SELECT 20; SELECT 10",
        "dashboard_id": dashboard,
        "expected_panel_ids": list(panels),
        "decisions": [],
        **kwargs,
    }


def test_preview_reorders_edits_and_preserves_database_settings_without_execution(
    client, monkeypatch
):
    dashboard, panels = existing(client)
    override = client.patch(
        f"/api/v1/panels/{panels[0]}/override", json={"field_name": "col_span", "user_value": "6"}
    )
    assert override.status_code == 200, override.text
    before = client.get("/api/v1/panels").json()
    assert before[0]["col_span_user_override"] == 6

    def forbidden(*args, **kwargs):
        raise AssertionError("Preflight executed SQL")

    monkeypatch.setattr(client.app.state.queries, "execute", forbidden)
    response = client.post(
        "/api/v1/sql/reconcile",
        json=request(
            dashboard,
            panels,
            decisions=[
                {"kind": "keep", "statement_index": 0, "panel_id": panels[1]},
                {"kind": "keep", "statement_index": 1, "panel_id": panels[0]},
            ],
        ),
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["complete"]
    assert [item["panel_id"] for item in result["statements"]] == list(reversed(panels))
    assert [item["sql"] for item in result["statements"]] == ["SELECT 20", "SELECT 10"]
    assert client.get("/api/v1/panels").json() == before
    assert response.headers["cache-control"] == "no-store"


def test_unresolved_duplicate_sql_is_not_matched_and_has_no_writes(client):
    dashboard, panels = existing(client)
    response = client.post(
        "/api/v1/sql/reconcile", json=request(dashboard, panels, sql="SELECT 1; SELECT 1")
    )
    result = response.json()
    assert response.status_code == 200 and not result["complete"]
    assert result["unresolved_statement_indexes"] == [0, 1]
    assert set(result["unresolved_panel_ids"]) == set(panels)
    assert result["statements"] == [] and result["removed_panel_ids"] == []


def test_explicit_creation_and_removal_are_proposals_only(client):
    dashboard, panels = existing(client)
    response = client.post(
        "/api/v1/sql/reconcile",
        json=request(
            dashboard,
            panels,
            sql="SELECT 3",
            decisions=[
                {"kind": "create", "statement_index": 0, "creation_key": "draft-new"},
                *[{"kind": "remove", "panel_id": panel} for panel in panels],
            ],
        ),
    )
    assert response.status_code == 200 and response.json()["complete"]
    assert response.json()["statements"][0]["panel_id"] is None
    assert set(response.json()["removed_panel_ids"]) == set(panels)
    assert len(client.get("/api/v1/panels").json()) == 2


def test_references_cannot_escape_dashboard_and_snapshot_mismatch_is_a_conflict(client):
    dashboard, panels = existing(client)
    other, foreign = existing(client)
    response = client.post(
        "/api/v1/sql/reconcile",
        json=request(
            dashboard,
            panels,
            decisions=[
                {"kind": "keep", "statement_index": 0, "panel_id": foreign[0]},
            ],
        ),
    )
    assert response.status_code == 422
    assert response.json()["code"] == "sql_reconciliation_invalid"
    assert (
        client.post("/api/v1/sql/reconcile", json=request(dashboard, panels[:1])).status_code == 409
    )
    assert client.post("/api/v1/sql/reconcile", json=request(other, panels)).status_code == 409
    assert client.post("/api/v1/sql/reconcile", json=request("missing")).status_code == 404


@pytest.mark.parametrize(
    "decision",
    [
        {"kind": "keep", "statement_index": True, "panel_id": "p"},
        {"kind": "create", "statement_index": 0, "creation_key": 1},
        {"kind": "guess", "statement_index": 0},
        {"kind": "keep", "statement_index": 0, "panel_id": "p", "sql": "SELECT 99"},
        {"kind": "create", "statement_index": 256, "creation_key": "new"},
    ],
)
def test_decision_contract_rejects_coercion_extras_and_unknown_types(client, decision):
    assert (
        client.post("/api/v1/sql/reconcile", json=request(decisions=[decision])).status_code == 422
    )


def test_invalid_later_statement_and_excess_decisions_have_no_writes(client):
    dashboard, panels = existing(client)
    before = client.get("/api/v1/panels").json()
    assert (
        client.post(
            "/api/v1/sql/reconcile",
            json=request(dashboard, panels, sql="SELECT 1; SELECT 'unfinished"),
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/sql/reconcile",
            json=request(
                decisions=[
                    {"kind": "remove", "panel_id": "p"},
                ]
                * 513
            ),
        ).status_code
        == 422
    )
    assert client.get("/api/v1/panels").json() == before


def test_fresh_source_can_be_proposed_and_readers_cannot_use_author_preflight(client):
    response = client.post(
        "/api/v1/sql/reconcile",
        json=request(
            sql="SELECT '\U0001f680;a'",
            decisions=[
                {"kind": "create", "statement_index": 0, "creation_key": "new"},
            ],
        ),
    )
    assert response.status_code == 200 and response.json()["complete"]
    dashboard, _ = existing(client)
    token = client.post(f"/api/v1/dashboards/{dashboard}/share", json={"mode": "public"}).json()[
        "token"
    ]
    client.cookies.clear()
    assert client.post("/api/v1/sql/reconcile", json=request()).status_code == 401
    assert (
        client.post(
            "/api/v1/sql/reconcile", json=request(), headers={"X-SQLviz-Share": token}
        ).status_code
        == 403
    )
