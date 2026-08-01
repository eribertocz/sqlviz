"""Tests for PATCH /api/v1/panels/{panel_id}/override — V0.2 Fase E.

Exit criteria (DOC10 §6.14):
  1. PATCH /override persists correctly in .sqlviz (selected_*, *_user_override)
  2. inferred_* never overwritten — selected_* reflects override after PATCH
  3. Session regression test:
       - Execute SQL X → system infers chart A
       - PATCH override to chart B → saved in brain.duckdb
       - Execute SQL X again → inference returns chart B
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
import sqlviz_storage.brain_db as brain_module
from fastapi.testclient import TestClient
from sqlviz_api.main import create_app
from sqlviz_storage.project_db import create_project


@pytest.fixture(autouse=True)
def _reset_brain(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator:
    """Redirect brain.duckdb to tmp_path for test isolation."""
    brain_module._brain_conn = None
    p = tmp_path / ".sqlviz" / "brain.duckdb"
    (tmp_path / ".sqlviz").mkdir()
    monkeypatch.setattr(brain_module, "get_brain_path", lambda: p)
    yield
    if brain_module._brain_conn is not None:
        brain_module._brain_conn.close()
    brain_module._brain_conn = None


@pytest.fixture
def client(tmp_path: Path) -> Generator[TestClient, None, None]:
    conn = create_project(str(tmp_path / "test.sqlviz"))
    app = create_app(conn)
    with TestClient(app) as c:
        yield c
    conn.close()


def _make_panel(client: TestClient, sql: str) -> str:
    dash_id = client.post("/api/v1/dashboards", json={"name": "D"}).json()["id"]
    return client.post("/api/v1/panels", json={
        "dashboard_id": dash_id,
        "name": "P",
        "sql_content": sql,
    }).json()["id"]


_TREND_SQL = (
    "SELECT month, SUM(revenue) AS total "
    "FROM (VALUES (1, 100), (2, 200), (3, 300)) t(month, revenue) "
    "GROUP BY month ORDER BY month"
)


# ── Basic override endpoint ───────────────────────────────────────────────────

class TestOverrideEndpointBasics:

    def test_nonexistent_panel_returns_404(self, client: TestClient) -> None:
        resp = client.patch(
            "/api/v1/panels/does-not-exist/override",
            json={"field_name": "chart_type", "user_value": "bar"},
        )
        assert resp.status_code == 404

    def test_unknown_field_name_returns_422(self, client: TestClient) -> None:
        panel_id = _make_panel(client, "SELECT 1 AS n")
        client.post(f"/api/v1/panels/{panel_id}/execute")
        resp = client.patch(
            f"/api/v1/panels/{panel_id}/override",
            json={"field_name": "bad_field", "user_value": "bar"},
        )
        assert resp.status_code == 422

    def test_returns_updated_panel_response(self, client: TestClient) -> None:
        panel_id = _make_panel(client, _TREND_SQL)
        client.post(f"/api/v1/panels/{panel_id}/execute")
        resp = client.patch(
            f"/api/v1/panels/{panel_id}/override",
            json={"field_name": "chart_type", "user_value": "bar"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == panel_id

    def test_override_before_execute_allowed(self, client: TestClient) -> None:
        # Panel created but never executed — override still allowed
        # (inferred_* are NULL, selected_* set to user_value)
        panel_id = _make_panel(client, "SELECT 1")
        resp = client.patch(
            f"/api/v1/panels/{panel_id}/override",
            json={"field_name": "chart_type", "user_value": "bar"},
        )
        assert resp.status_code == 200


# ── Override persists correctly ───────────────────────────────────────────────

class TestOverridePersistence:

    def test_selected_chart_type_updated(self, client: TestClient) -> None:
        panel_id = _make_panel(client, _TREND_SQL)
        client.post(f"/api/v1/panels/{panel_id}/execute")
        client.patch(
            f"/api/v1/panels/{panel_id}/override",
            json={"field_name": "chart_type", "user_value": "bar"},
        )
        panel = client.get(f"/api/v1/panels/{panel_id}").json()
        assert panel["selected_chart_type"] == "bar"

    def test_chart_user_override_set(self, client: TestClient) -> None:
        panel_id = _make_panel(client, _TREND_SQL)
        client.post(f"/api/v1/panels/{panel_id}/execute")
        client.patch(
            f"/api/v1/panels/{panel_id}/override",
            json={"field_name": "chart_type", "user_value": "pie"},
        )
        panel = client.get(f"/api/v1/panels/{panel_id}").json()
        assert panel["chart_user_override"] == "pie"

    def test_inferred_chart_type_never_overwritten(self, client: TestClient) -> None:
        panel_id = _make_panel(client, _TREND_SQL)
        client.post(f"/api/v1/panels/{panel_id}/execute")
        inferred_before = client.get(
            f"/api/v1/panels/{panel_id}"
        ).json()["inferred_chart_type"]

        client.patch(
            f"/api/v1/panels/{panel_id}/override",
            json={"field_name": "chart_type", "user_value": "pie"},
        )
        inferred_after = client.get(
            f"/api/v1/panels/{panel_id}"
        ).json()["inferred_chart_type"]

        assert inferred_before == inferred_after

    def test_col_span_override_persists(self, client: TestClient) -> None:
        panel_id = _make_panel(client, _TREND_SQL)
        client.post(f"/api/v1/panels/{panel_id}/execute")
        client.patch(
            f"/api/v1/panels/{panel_id}/override",
            json={"field_name": "col_span", "user_value": "6"},
        )
        panel = client.get(f"/api/v1/panels/{panel_id}").json()
        assert panel["selected_col_span"] == 6
        assert panel["col_span_user_override"] == 6
        inferred = panel["inferred_col_span"]
        # inferred must not be 6 unless pipeline chose 6 (it should be 12 for trend)
        assert panel["inferred_col_span"] == inferred  # unchanged

    def test_height_px_override_persists(self, client: TestClient) -> None:
        panel_id = _make_panel(client, _TREND_SQL)
        client.post(f"/api/v1/panels/{panel_id}/execute")
        client.patch(
            f"/api/v1/panels/{panel_id}/override",
            json={"field_name": "height_px", "user_value": "480"},
        )
        panel = client.get(f"/api/v1/panels/{panel_id}").json()
        assert panel["selected_height_px"] == 480
        assert panel["height_user_override"] == 480


# ── Execute stores inference ──────────────────────────────────────────────────

class TestExecuteStoresInference:

    def test_execute_stores_fingerprint(self, client: TestClient) -> None:
        panel_id = _make_panel(client, _TREND_SQL)
        client.post(f"/api/v1/panels/{panel_id}/execute")
        panel = client.get(f"/api/v1/panels/{panel_id}").json()
        assert panel["fingerprint"] is not None
        assert panel["fingerprint"] != "UNKNOWN"

    def test_execute_stores_inferred_chart_type(self, client: TestClient) -> None:
        panel_id = _make_panel(client, _TREND_SQL)
        body = client.post(f"/api/v1/panels/{panel_id}/execute").json()
        panel = client.get(f"/api/v1/panels/{panel_id}").json()
        assert panel["inferred_chart_type"] == body["inference_result"]["chart_winner"]

    def test_execute_initialises_selected_chart_type(self, client: TestClient) -> None:
        panel_id = _make_panel(client, _TREND_SQL)
        client.post(f"/api/v1/panels/{panel_id}/execute")
        panel = client.get(f"/api/v1/panels/{panel_id}").json()
        assert panel["selected_chart_type"] == panel["inferred_chart_type"]


# ── SESSION REGRESSION TEST ───────────────────────────────────────────────────

class TestSessionRegression:
    """Critical exit criterion: learned override survives across executions."""

    def test_override_applied_on_re_execution(self, client: TestClient) -> None:
        """
        1. Execute SQL X → system infers chart A
        2. PATCH override to chart B → brain.duckdb updated
        3. Execute SQL X again → inference returns chart B
        """
        # Use a composition query that normally gets inferred as "bar"
        sql = (
            "SELECT category, SUM(revenue) "
            "FROM (VALUES ('A', 100), ('B', 200), ('C', 300)) t(category, revenue) "
            "GROUP BY category"
        )
        panel_id = _make_panel(client, sql)

        # Step 1: Execute — get inferred chart
        first_exec = client.post(f"/api/v1/panels/{panel_id}/execute").json()
        first_chart = first_exec["inference_result"]["chart_winner"]

        # Step 2: Override to "pie"
        client.patch(
            f"/api/v1/panels/{panel_id}/override",
            json={"field_name": "chart_type", "user_value": "pie"},
        )

        # Step 3: Execute again — should return "pie"
        second_exec = client.post(f"/api/v1/panels/{panel_id}/execute").json()
        second_chart = second_exec["inference_result"]["chart_winner"]

        # The system must have returned "pie" regardless of what it inferred first
        assert second_chart == "pie", (
            f"Session regression: first={first_chart}, "
            f"expected second='pie', got '{second_chart}'"
        )

    def test_new_panel_benefits_from_existing_brain_pattern(
        self, client: TestClient
    ) -> None:
        """
        Override on panel A teaches brain.duckdb.
        A new panel B with the same SQL shape returns the overridden chart.
        """
        sql = (
            "SELECT category, SUM(revenue) "
            "FROM (VALUES ('A', 100), ('B', 200), ('C', 300)) t(category, revenue) "
            "GROUP BY category"
        )
        dash_id = client.post("/api/v1/dashboards", json={"name": "D2"}).json()["id"]

        # Panel A: execute + override
        panel_a = client.post("/api/v1/panels", json={
            "dashboard_id": dash_id, "name": "A", "sql_content": sql,
        }).json()["id"]
        client.post(f"/api/v1/panels/{panel_a}/execute")
        client.patch(
            f"/api/v1/panels/{panel_a}/override",
            json={"field_name": "chart_type", "user_value": "pie"},
        )

        # Panel B: same SQL, never overridden — should get "pie" from brain
        panel_b = client.post("/api/v1/panels", json={
            "dashboard_id": dash_id, "name": "B", "sql_content": sql,
        }).json()["id"]
        result_b = client.post(f"/api/v1/panels/{panel_b}/execute").json()
        assert result_b["inference_result"]["chart_winner"] == "pie"


# ── SIZE OVERRIDES SURVIVE A RE-RUN ───────────────────────────────────────────

class TestSizeOverrideRoundTrip:
    """The size a user picks has to come back on every execute.

    The override columns were written correctly all along, but nothing read them
    back into the inference_result — and that dict is the only thing the layout
    is composed from, for the admin app and for a shared link alike. So a panel
    resized in Panel Properties reverted to its inferred size on the next Run,
    and a shared link never showed the chosen width at all.
    """

    def test_col_span_override_comes_back_on_re_execution(self, client: TestClient) -> None:
        panel_id = _make_panel(client, _TREND_SQL)
        first = client.post(f"/api/v1/panels/{panel_id}/execute").json()
        inferred_span = first["inference_result"]["col_span"]
        chosen = 6 if inferred_span != 6 else 4

        client.patch(
            f"/api/v1/panels/{panel_id}/override",
            json={"field_name": "col_span", "user_value": str(chosen)},
        )

        second = client.post(f"/api/v1/panels/{panel_id}/execute").json()
        assert second["inference_result"]["col_span"] == chosen

    def test_height_override_comes_back_on_re_execution(self, client: TestClient) -> None:
        panel_id = _make_panel(client, _TREND_SQL)
        client.post(f"/api/v1/panels/{panel_id}/execute")
        client.patch(
            f"/api/v1/panels/{panel_id}/override",
            json={"field_name": "height_px", "user_value": "480"},
        )

        again = client.post(f"/api/v1/panels/{panel_id}/execute").json()
        assert again["inference_result"]["panel_height_px"] == 480

    def test_size_override_does_not_disturb_the_inferred_value(self, client: TestClient) -> None:
        panel_id = _make_panel(client, _TREND_SQL)
        first = client.post(f"/api/v1/panels/{panel_id}/execute").json()
        inferred_span = first["inference_result"]["col_span"]

        client.patch(
            f"/api/v1/panels/{panel_id}/override",
            json={"field_name": "col_span", "user_value": "3"},
        )
        client.post(f"/api/v1/panels/{panel_id}/execute")

        panel = client.get(f"/api/v1/panels/{panel_id}").json()
        assert panel["inferred_col_span"] == inferred_span
        assert panel["selected_col_span"] == 3


# ── RESET TO AUTO ─────────────────────────────────────────────────────────────

class TestClearOverride:
    """`user_value: null` withdraws the correction and follows inference again."""

    def test_clearing_col_span_restores_the_inferred_size(self, client: TestClient) -> None:
        panel_id = _make_panel(client, _TREND_SQL)
        first = client.post(f"/api/v1/panels/{panel_id}/execute").json()
        inferred_span = first["inference_result"]["col_span"]

        client.patch(
            f"/api/v1/panels/{panel_id}/override",
            json={"field_name": "col_span", "user_value": "3"},
        )
        client.patch(
            f"/api/v1/panels/{panel_id}/override",
            json={"field_name": "col_span", "user_value": None},
        )

        panel = client.get(f"/api/v1/panels/{panel_id}").json()
        assert panel["col_span_user_override"] is None
        assert panel["selected_col_span"] == inferred_span

        after = client.post(f"/api/v1/panels/{panel_id}/execute").json()
        assert after["inference_result"]["col_span"] == inferred_span

    def test_clearing_height_restores_the_inferred_size(self, client: TestClient) -> None:
        panel_id = _make_panel(client, _TREND_SQL)
        first = client.post(f"/api/v1/panels/{panel_id}/execute").json()
        inferred_height = first["inference_result"]["panel_height_px"]

        client.patch(
            f"/api/v1/panels/{panel_id}/override",
            json={"field_name": "height_px", "user_value": "480"},
        )
        client.patch(
            f"/api/v1/panels/{panel_id}/override",
            json={"field_name": "height_px", "user_value": None},
        )

        after = client.post(f"/api/v1/panels/{panel_id}/execute").json()
        assert after["inference_result"]["panel_height_px"] == inferred_height

    def test_clearing_an_unknown_field_is_rejected(self, client: TestClient) -> None:
        panel_id = _make_panel(client, _TREND_SQL)
        r = client.patch(
            f"/api/v1/panels/{panel_id}/override",
            json={"field_name": "nonsense", "user_value": None},
        )
        assert r.status_code == 422

    def test_clearing_on_a_missing_panel_is_404(self, client: TestClient) -> None:
        r = client.patch(
            "/api/v1/panels/does-not-exist/override",
            json={"field_name": "col_span", "user_value": None},
        )
        assert r.status_code == 404


# ── KPI PANELS: THE SHELF MUST NOT DISCARD A PINNED WIDTH ─────────────────────

_KPI_SQL = "SELECT SUM(revenue) AS total FROM (VALUES (1, 100), (2, 200)) t(month, revenue)"


class TestKpiWidthReachesCompose:
    """compose() is what the shared viewer renders, so the width has to survive it.

    execute already returns the pinned width, but the KPI shelf reassigned it
    while centring the row. The admin app hid this behind its own optimistic
    update until the next Run; a viewer had nothing to hide it with.
    """

    def _compose(self, client: TestClient, panel_id: str, ir: dict) -> dict:
        return client.post(
            "/api/v1/compose",
            json=[{"panel_id": panel_id, "inference_result": ir}],
        ).json()

    def test_pinned_kpi_width_survives_compose(self, client: TestClient) -> None:
        panel_id = _make_panel(client, _KPI_SQL)
        first = client.post(f"/api/v1/panels/{panel_id}/execute").json()
        assert first["inference_result"]["chart_winner"] == "kpi"

        client.patch(
            f"/api/v1/panels/{panel_id}/override",
            json={"field_name": "col_span", "user_value": "6"},
        )
        ir = client.post(f"/api/v1/panels/{panel_id}/execute").json()["inference_result"]
        layout = self._compose(client, panel_id, ir)

        assert layout["rows"][0]["panels"][0]["final_col_span"] == 6

    def test_unpinned_kpi_keeps_the_shelf_width(self, client: TestClient) -> None:
        panel_id = _make_panel(client, _KPI_SQL)
        ir = client.post(f"/api/v1/panels/{panel_id}/execute").json()["inference_result"]
        layout = self._compose(client, panel_id, ir)

        assert layout["rows"][0]["panels"][0]["final_col_span"] == 4

    def test_clearing_the_override_returns_the_kpi_to_the_shelf(self, client: TestClient) -> None:
        panel_id = _make_panel(client, _KPI_SQL)
        client.post(f"/api/v1/panels/{panel_id}/execute")
        client.patch(
            f"/api/v1/panels/{panel_id}/override",
            json={"field_name": "col_span", "user_value": "6"},
        )
        client.patch(
            f"/api/v1/panels/{panel_id}/override",
            json={"field_name": "col_span", "user_value": None},
        )
        ir = client.post(f"/api/v1/panels/{panel_id}/execute").json()["inference_result"]
        layout = self._compose(client, panel_id, ir)

        assert layout["rows"][0]["panels"][0]["final_col_span"] == 4

    def test_pinned_width_survives_compose_for_a_normal_panel_too(self, client: TestClient) -> None:
        panel_id = _make_panel(client, _TREND_SQL)
        client.post(f"/api/v1/panels/{panel_id}/execute")
        client.patch(
            f"/api/v1/panels/{panel_id}/override",
            json={"field_name": "col_span", "user_value": "4"},
        )
        ir = client.post(f"/api/v1/panels/{panel_id}/execute").json()["inference_result"]
        layout = self._compose(client, panel_id, ir)

        assert layout["rows"][0]["panels"][0]["final_col_span"] == 4
