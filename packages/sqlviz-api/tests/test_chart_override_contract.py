"""Chart choices are validated, confirmed and shared without allowing viewer writes."""

import json

import pytest
from sqlviz_storage import brain_db
from sqlviz_storage.transactions import project_transaction


def seed(client):
    dashboard = client.post("/api/v1/dashboards", json={"name": "D"}).json()["id"]
    return client.post("/api/v1/panels", json={"dashboard_id": dashboard, "name": "P",
        "sql_content": ("SELECT category, amount FROM "
                        "(VALUES ('A', 7), ('B', 12)) t(category, amount)"),
    }).json()


@pytest.mark.parametrize("value", ["", " ", "funnel", "BAR", " bar", "bar ", "unknown",
                                  "\ud800", 1, True, [], {}])
def test_invalid_identifiers_do_not_change_project_or_learning(client, value):
    panel = seed(client)
    before = client.get(f"/api/v1/panels/{panel['id']}").json()
    response = client.patch(
        f"/api/v1/panels/{panel['id']}/override", headers={"Content-Type": "application/json"},
        content=json.dumps({"field_name": "chart_type", "user_value": value}),
    )
    assert response.status_code == 422, response.text
    assert client.get(f"/api/v1/panels/{panel['id']}").json() == before
    assert brain_db.get_brain_connection().execute(
        "SELECT count(*) FROM feedback_events").fetchone() == (0,)


@pytest.mark.parametrize("body", [{}, {"field_name": "chart_type"}, {"user_value": "line"},
                                  {"field_name": "chart_type", "user_value": "line", "extra": 1}])
def test_omission_and_extra_fields_do_not_clear_manual_choice(client, body):
    panel = seed(client)
    path = f"/api/v1/panels/{panel['id']}/override"
    saved = client.patch(path, json={"field_name": "chart_type", "user_value": "line"})
    assert saved.status_code == 200
    before = client.get(f"/api/v1/panels/{panel['id']}").json()
    assert client.patch(path, json=body).status_code == 422
    assert client.get(f"/api/v1/panels/{panel['id']}").json() == before


def test_learning_failure_does_not_turn_a_confirmed_save_into_an_error(client, monkeypatch):
    import sqlviz_api.routers.panels as router
    panel = seed(client)
    assert client.post(f"/api/v1/panels/{panel['id']}/execute").status_code == 200

    def fail():
        raise OSError("private path")
    monkeypatch.setattr(router, "get_brain_connection", fail)
    response = client.patch(f"/api/v1/panels/{panel['id']}/override",
                            json={"field_name": "chart_type", "user_value": "line"})
    assert response.status_code == 200, response.text
    assert response.json()["chart_user_override"] == "line"
    assert response.json() == client.get(f"/api/v1/panels/{panel['id']}").json()


def test_reexecution_never_stores_manual_choice_as_automatic_inference(client):
    panel = seed(client)
    path = f"/api/v1/panels/{panel['id']}"
    first = client.post(f"{path}/execute").json()["inference_result"]
    chosen = "line" if first["chart_engine_winner"] != "line" else "pie"
    assert client.patch(f"{path}/override", json={
        "field_name": "chart_type", "user_value": chosen,
    }).status_code == 200
    executed = client.post(f"{path}/execute").json()["inference_result"]
    assert executed["chart_winner"] == chosen
    stored = client.get(path).json()
    assert stored["inferred_chart_type"] == executed["chart_engine_winner"]
    assert stored["selected_chart_type"] == chosen
    reset = client.patch(f"{path}/override", json={
        "field_name": "chart_type", "user_value": None,
    }).json()
    assert reset["selected_chart_type"] == executed["chart_engine_winner"]


@pytest.mark.parametrize("value", ["line", None])
def test_concurrent_update_returns_predictable_conflict_without_learning(client, value):
    panel = seed(client)
    with client.app.state.db_conn.cursor() as held:
        with project_transaction(held):
            held.execute("UPDATE panels SET updated_at = 'held' WHERE id = ?", [panel["id"]])
            response = client.patch(f"/api/v1/panels/{panel['id']}/override",
                                    json={"field_name": "chart_type", "user_value": value})
            assert response.status_code == 409
            assert response.json()["code"] == "panel_write_conflict"
    assert client.get(f"/api/v1/panels/{panel['id']}").json()["chart_user_override"] is None


@pytest.mark.parametrize("scope", ["dashboard", "workspace"])
def test_manual_choice_equal_to_engine_stays_explicit_in_author_compose_and_viewer(client, scope):
    panel = seed(client)
    execute = f"/api/v1/panels/{panel['id']}/execute"
    auto = client.post(execute).json()["inference_result"]
    winner = auto["chart_engine_winner"]
    patch = client.patch(f"/api/v1/panels/{panel['id']}/override",
                         json={"field_name": "chart_type", "user_value": winner})
    assert patch.status_code == 200
    author = client.post(execute).json()["inference_result"]
    assert author["chart_user_override"] == winner
    assert author["chart_winner"] == author["chart_engine_winner"] == winner
    composed = client.post("/api/v1/compose", json=[{"panel_id": panel["id"],
                                                   "inference_result": author}])
    assert composed.status_code == 200, composed.text
    composed_result = composed.json()["rows"][0]["panels"][0]["inference_result"]
    assert composed_result["chart_user_override"] == winner
    share_path = (f"/api/v1/dashboards/{panel['dashboard_id']}/share"
                  if scope == "dashboard" else "/api/v1/workspace/share")
    token = client.post(share_path, json={"mode": "public"}).json()["token"]
    cookie = client.cookies.get("sqlviz_session")
    client.cookies.clear()
    try:
        headers = {"X-SQLviz-Share": token}
        response = client.post(execute, headers=headers)
        assert response.status_code == 200, response.text
        assert response.json()["inference_result"]["chart_user_override"] == winner
        denied = client.patch(f"/api/v1/panels/{panel['id']}/override", headers=headers,
                              json={"field_name": "chart_type", "user_value": None})
        assert denied.status_code == 403
    finally:
        client.cookies.set("sqlviz_session", cookie)
    response = client.patch(f"/api/v1/panels/{panel['id']}/override",
                            json={"field_name": "chart_type", "user_value": None})
    assert response.json()["chart_user_override"] is None
    assert client.post(execute).json()["inference_result"]["chart_user_override"] is None
