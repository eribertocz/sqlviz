"""Phase 7 automated QA — docs/qa/phase7-qa-checklist.md.

Covers the maximum automatable items from the checklist using pytest +
FastAPI TestClient. Each test docstring references its checklist section.

Items requiring visual browser verification are NOT here — they remain
marked as [manual] in the checklist.
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
import sqlviz_api.routers.auth as auth_module
import sqlviz_inference
from fastapi.testclient import TestClient
from sqlviz_api.main import create_app
from sqlviz_core.models import ColumnSchema
from sqlviz_inference.dashboard import DashboardEngine
from sqlviz_storage.auth import set_admin_password
from sqlviz_storage.project_db import create_project

_PW = "qapassword1"


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _reset_sessions() -> Generator[None, None, None]:
    auth_module._sessions.clear()
    yield
    auth_module._sessions.clear()


@pytest.fixture
def demo_client() -> Generator[TestClient, None, None]:
    conn = create_project(":memory:")
    app = create_app(conn, demo_mode=True)
    with TestClient(app) as c:
        yield c
    conn.close()


@pytest.fixture
def auth_client(tmp_path: Path) -> Generator[TestClient, None, None]:
    conn = create_project(str(tmp_path / "qa.sqlviz"))
    set_admin_password(conn, _PW)
    app = create_app(conn)
    with TestClient(app) as c:
        yield c
    conn.close()


@pytest.fixture
def admin_client(auth_client: TestClient) -> TestClient:
    auth_client.post("/api/v1/auth/login", json={"password": _PW})
    return auth_client


@pytest.fixture
def admin_dash_id(admin_client: TestClient) -> str:
    return admin_client.post(
        "/api/v1/dashboards", json={"name": "QA Dashboard"}
    ).json()["id"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _exec_sql(client: TestClient, sql: str) -> dict:
    dash = client.post("/api/v1/dashboards", json={"name": "D"}).json()
    panel = client.post("/api/v1/panels", json={
        "dashboard_id": dash["id"], "name": "P", "sql_content": sql,
    }).json()
    return client.post(f"/api/v1/panels/{panel['id']}/execute").json()


def _infer(sql: str, schema: list[ColumnSchema], data: list[dict] | None = None) -> object:
    return sqlviz_inference.infer(sql, data=data or [], schema=schema)


# ── §1 CLI Flows ──────────────────────────────────────────────────────────────

class TestCLIFlows:
    """§1 — Only disk-side behavior is automatable.
    Terminal output, browser opening, and Ctrl+C require manual testing.
    """

    def test_demo_mode_creates_no_disk_files(self, tmp_path: Path) -> None:
        """§1.1 — create_project(':memory:') writes nothing to disk."""
        before = set(tmp_path.iterdir())
        conn = create_project(":memory:")
        conn.close()
        assert set(tmp_path.iterdir()) == before


# ── §2 Auth Flows ─────────────────────────────────────────────────────────────

class TestAuthFlows:
    """§2 — §2.2–2.6 covered by test_auth.py; §2.7 by test_demo.py.
    UI elements (login screen, redirect, browser tab) are manual.
    """

    def test_session_cookie_is_httponly(self, auth_client: TestClient) -> None:
        """§2.2 — Set-Cookie header must carry the HttpOnly flag."""
        resp = auth_client.post("/api/v1/auth/login", json={"password": _PW})
        assert resp.status_code == 200
        assert "httponly" in resp.headers.get("set-cookie", "").lower()

    def test_session_persists_across_requests(self, auth_client: TestClient) -> None:
        """§2.4 — Cookie from login allows a subsequent protected request."""
        auth_client.post("/api/v1/auth/login", json={"password": _PW})
        resp = auth_client.get("/api/v1/auth/me")
        assert resp.status_code == 200
        assert resp.json()["status"] == "authenticated"

    def test_root_redirects_to_login_without_session(
        self, auth_client: TestClient
    ) -> None:
        """§2.8 — GET / without a session redirects to /login (persistent mode)."""
        resp = auth_client.get("/", follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers["location"] == "/login"

    def test_login_page_accessible_without_session(
        self, auth_client: TestClient
    ) -> None:
        """§2.8 — GET /login without a session serves the SPA (login form loads)."""
        resp = auth_client.get("/login", follow_redirects=False)
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")

    def test_root_accessible_after_login(self, admin_client: TestClient) -> None:
        """§2.8 — GET / with a valid session returns 200."""
        resp = admin_client.get("/", follow_redirects=False)
        assert resp.status_code == 200

    def test_frontend_accessible_in_demo_mode(self, demo_client: TestClient) -> None:
        """§2.8 — GET / in demo mode returns 200 without any session."""
        resp = demo_client.get("/", follow_redirects=False)
        assert resp.status_code == 200

    def test_api_401_not_redirected(self, auth_client: TestClient) -> None:
        """§2.8 — 401 from API routes is NOT converted to a redirect."""
        resp = auth_client.get("/api/v1/auth/me", follow_redirects=False)
        assert resp.status_code == 401
        assert resp.json() == {"detail": "Not authenticated"}


# ── §3 Dashboard and Panel Flows ──────────────────────────────────────────────

class TestDashboardPanelFlows:
    """§3 — §3.1 covered by test_demo.py.
    Overflow menu, Edit SQL, Change chart UI flows are manual.
    """

    def test_kpi_from_single_aggregate(self, client: TestClient) -> None:
        """§3.2 — SUM with no GROUP BY → chart_winner='kpi'."""
        body = _exec_sql(
            client,
            "SELECT SUM(x) AS total FROM (VALUES (100.0),(200.0),(300.0)) t(x)",
        )
        assert body["inference_result"]["chart_winner"] == "kpi"

    def test_line_from_time_series(self, client: TestClient) -> None:
        """§3.2 — month + revenue GROUP BY month ORDER BY month → chart_winner='line'."""
        body = _exec_sql(
            client,
            "SELECT month, SUM(rev) AS revenue "
            "FROM (VALUES (1,100.0),(2,150.0),(3,200.0),(4,180.0)) t(month,rev) "
            "GROUP BY month ORDER BY month",
        )
        assert body["inference_result"]["chart_winner"] == "line"

    def test_line_chart_has_correct_row_count(self, client: TestClient) -> None:
        """§3.2 — 4-month series → 4 data rows returned."""
        body = _exec_sql(
            client,
            "SELECT month, SUM(rev) AS revenue "
            "FROM (VALUES (1,100.0),(2,150.0),(3,200.0),(4,180.0)) t(month,rev) "
            "GROUP BY month ORDER BY month",
        )
        assert len(body["data"]) == 4

    def test_three_panel_chart_types_via_compose(self) -> None:
        """§3.3 — DashboardEngine produces kpi + line + bar for 3 mixed queries."""
        kpi_r = _infer(
            "SELECT SUM(x) AS total FROM (VALUES (1.0)) t(x)",
            data=[{"total": 1.0}],
            schema=[ColumnSchema(name="total", type="DOUBLE")],
        )
        # 6 monthly points → "line"
        months = list(range(1, 7))
        line_r = _infer(
            "SELECT month, SUM(revenue) AS monthly_revenue "
            "FROM (VALUES (1,15000.0),(2,12000.0),(3,18000.0),"
            "(4,16000.0),(5,21000.0),(6,19000.0)) AS t(month,revenue) "
            "GROUP BY month ORDER BY month",
            data=[{"month": m, "monthly_revenue": float(v)}
                  for m, v in zip(months, [15000, 12000, 18000, 16000, 21000, 19000])],
            schema=[ColumnSchema(name="month", type="INTEGER"),
                    ColumnSchema(name="monthly_revenue", type="DOUBLE")],
        )
        # 4 categories alphabetical → "bar"
        bar_r = _infer(
            "SELECT category, SUM(sales) AS total_sales "
            "FROM (VALUES ('Electronics',45000.0),('Clothing',28000.0),"
            "('Food',15000.0),('Books',8000.0)) AS t(category,sales) "
            "GROUP BY category ORDER BY category",
            data=[{"category": c, "total_sales": float(v)}
                  for c, v in [("Books", 8000), ("Clothing", 28000),
                                ("Electronics", 45000), ("Food", 15000)]],
            schema=[ColumnSchema(name="category", type="VARCHAR"),
                    ColumnSchema(name="total_sales", type="DOUBLE")],
        )
        layout = DashboardEngine().compose([("p0", kpi_r), ("p1", line_r), ("p2", bar_r)])
        types = {p.inference_result.chart_winner for row in layout.rows for p in row.panels}
        assert types == {"kpi", "line", "bar"}

    def test_three_panel_all_panels_have_col_span(self) -> None:
        """§3.3 — Layout auto-places all panels (col_span > 0 for each)."""
        kpi_r = _infer(
            "SELECT SUM(x) AS total FROM (VALUES (1.0)) t(x)",
            data=[{"total": 1.0}],
            schema=[ColumnSchema(name="total", type="DOUBLE")],
        )
        line_r = _infer(
            "SELECT m, SUM(r) AS rev FROM (VALUES (1,10.0),(2,20.0)) t(m,r) GROUP BY m ORDER BY m",
            data=[{"m": 1, "rev": 10.0}],
            schema=[ColumnSchema(name="m", type="INTEGER"), ColumnSchema(name="rev", type="DOUBLE")],
        )
        bar_r = _infer(
            "SELECT cat, SUM(v) AS total FROM (VALUES ('A',30.0)) t(cat,v) GROUP BY cat ORDER BY cat",
            data=[{"cat": "A", "total": 30.0}],
            schema=[ColumnSchema(name="cat", type="VARCHAR"), ColumnSchema(name="total", type="DOUBLE")],
        )
        layout = DashboardEngine().compose([("p0", kpi_r), ("p1", line_r), ("p2", bar_r)])
        for row in layout.rows:
            for panel in row.panels:
                assert panel.final_col_span > 0

    def test_panel_auto_title_is_nonempty(self, client: TestClient) -> None:
        """§3.4 — execute returns a non-empty title."""
        body = _exec_sql(
            client,
            "SELECT month, SUM(revenue) AS monthly_revenue "
            "FROM (VALUES (1,100.0),(2,200.0)) t(month,revenue) "
            "GROUP BY month ORDER BY month",
        )
        assert body["inference_result"]["title"] != ""

    def test_panel_title_contains_column_keyword(self, client: TestClient) -> None:
        """§3.4 — Title Engine uses column names from SQL."""
        body = _exec_sql(
            client,
            "SELECT month, SUM(revenue) AS monthly_revenue "
            "FROM (VALUES (1,100.0),(2,200.0)) t(month,revenue) "
            "GROUP BY month ORDER BY month",
        )
        title = body["inference_result"]["title"].lower()
        assert any(kw in title for kw in ("month", "revenue"))


# ── §6 Filter Flows ───────────────────────────────────────────────────────────

class TestFilterFlows:
    """§6 — All 8 control types are automatable via the inference engine.
    FilterBar rendering, interaction, and debounce require manual testing.
    """

    def _controls(self, sql: str, schema: list[ColumnSchema]) -> list[dict]:
        return _infer(sql, schema=schema, data=[]).filter_controls

    def test_varchar_equality_gives_dropdown(self) -> None:
        """§6.4 — VARCHAR + equality → dropdown."""
        controls = self._controls(
            "SELECT v FROM (VALUES ('A')) t(v) WHERE v = $category",
            [ColumnSchema(name="v", type="VARCHAR")],
        )
        assert any(c["control_type"] == "dropdown" for c in controls)

    def test_date_column_gives_date_picker(self) -> None:
        """§6.4 — DATE column → date_picker."""
        controls = self._controls(
            "SELECT d FROM (VALUES ('2024-01-01'::DATE)) t(d) WHERE d = $fecha",
            [ColumnSchema(name="d", type="DATE")],
        )
        assert any(c["control_type"] == "date_picker" for c in controls)

    def test_boolean_column_gives_toggle(self) -> None:
        """§6.4 — BOOLEAN column → toggle."""
        controls = self._controls(
            "SELECT b FROM (VALUES (true)) t(b) WHERE b = $active",
            [ColumnSchema(name="b", type="BOOLEAN")],
        )
        assert any(c["control_type"] == "toggle" for c in controls)

    def test_numeric_column_gives_numeric(self) -> None:
        """§6.4 — INTEGER column → numeric."""
        controls = self._controls(
            "SELECT n FROM (VALUES (1)) t(n) WHERE n = $amount",
            [ColumnSchema(name="n", type="INTEGER")],
        )
        assert any(c["control_type"] == "numeric" for c in controls)

    def test_ilike_gives_search(self) -> None:
        """§6.4 — ILIKE on VARCHAR → search."""
        controls = self._controls(
            "SELECT v FROM (VALUES ('A')) t(v) WHERE v ILIKE $search",
            [ColumnSchema(name="v", type="VARCHAR")],
        )
        assert any(c["control_type"] == "search" for c in controls)

    def test_any_operator_gives_multiselect(self) -> None:
        """§6.4 — ANY() operator on VARCHAR → multiselect."""
        controls = self._controls(
            "SELECT v FROM (VALUES ('A')) t(v) WHERE v = ANY($tags)",
            [ColumnSchema(name="v", type="VARCHAR")],
        )
        assert any(c["control_type"] == "multiselect" for c in controls)

    def test_paired_date_filters_give_date_range_picker(self) -> None:
        """§6.4 — Two $vars on same DATE column → date_range_picker."""
        controls = self._controls(
            "SELECT d FROM (VALUES ('2024-01-01'::DATE)) t(d) "
            "WHERE d >= $start_date AND d <= $end_date",
            [ColumnSchema(name="d", type="DATE")],
        )
        assert any(c["control_type"] == "date_range_picker" for c in controls)

    def test_paired_numeric_filters_give_range_slider(self) -> None:
        """§6.4 — Two $vars on same INTEGER column → range_slider."""
        controls = self._controls(
            "SELECT n FROM (VALUES (1)) t(n) WHERE n >= $min_val AND n <= $max_val",
            [ColumnSchema(name="n", type="INTEGER")],
        )
        assert any(c["control_type"] == "range_slider" for c in controls)

    def test_two_variables_produce_two_controls(self) -> None:
        """§6.3 (backend) — Two $vars in SQL → two FilterControl entries."""
        controls = self._controls(
            "SELECT r, SUM(rev) AS total "
            "FROM (VALUES ('N',100.0)) t(r,rev) "
            "WHERE r = $region AND rev > $min_rev "
            "GROUP BY r",
            [
                ColumnSchema(name="r", type="VARCHAR"),
                ColumnSchema(name="rev", type="DOUBLE"),
            ],
        )
        assert len(controls) == 2

    def test_variable_without_value_populates_filter_controls(
        self, client: TestClient
    ) -> None:
        """§11.3 — Execute panel with $var and no values → filter_controls populated."""
        dash = client.post("/api/v1/dashboards", json={"name": "D"}).json()
        panel = client.post("/api/v1/panels", json={
            "dashboard_id": dash["id"],
            "name": "P",
            "sql_content": "SELECT v FROM (VALUES ('A'),('B')) t(v) WHERE v = $region",
        }).json()
        body = client.post(f"/api/v1/panels/{panel['id']}/execute").json()
        assert body["inference_result"]["filter_controls"] != []

    def test_variable_without_value_returns_empty_data(
        self, client: TestClient
    ) -> None:
        """§11.3 — Execute with $var and no values → data=[] (inference-only mode)."""
        dash = client.post("/api/v1/dashboards", json={"name": "D"}).json()
        panel = client.post("/api/v1/panels", json={
            "dashboard_id": dash["id"],
            "name": "P",
            "sql_content": "SELECT v FROM (VALUES ('A'),('B')) t(v) WHERE v = $region",
        }).json()
        body = client.post(f"/api/v1/panels/{panel['id']}/execute").json()
        assert body["data"] == []


# ── §7 Explainability ─────────────────────────────────────────────────────────

class TestExplainability:
    """§7 — Drawer UI, close behavior, and override interaction are manual.
    Inference quality fields and explanation payload are automatable.
    """

    def test_inference_result_has_explanation_list(self) -> None:
        """§7.2 — explanation is a list in every InferenceResult."""
        result = _infer(
            "SELECT SUM(x) AS total FROM (VALUES (1.0)) t(x)",
            data=[{"total": 1.0}],
            schema=[ColumnSchema(name="total", type="DOUBLE")],
        )
        assert isinstance(result.explanation, list)

    def test_inference_result_has_chart_alternatives(self) -> None:
        """§7.2 — chart_alternatives list present (may be empty)."""
        result = _infer(
            "SELECT cat, SUM(v) AS total "
            "FROM (VALUES ('A',10.0),('B',5.0)) t(cat,v) GROUP BY cat",
            data=[{"cat": "A", "total": 10.0}],
            schema=[ColumnSchema(name="cat", type="VARCHAR"), ColumnSchema(name="total", type="DOUBLE")],
        )
        assert isinstance(result.chart_alternatives, list)

    def test_inference_result_has_confidence_gaps(self) -> None:
        """§7.2 — intent_confidence_gap and chart_confidence_gap are floats."""
        result = _infer(
            "SELECT SUM(x) AS total FROM (VALUES (1.0)) t(x)",
            data=[{"total": 1.0}],
            schema=[ColumnSchema(name="total", type="DOUBLE")],
        )
        assert isinstance(result.intent_confidence_gap, float)
        assert isinstance(result.chart_confidence_gap, float)

    def test_kpi_chart_quality_is_high(self) -> None:
        """§7.1 — Unambiguous KPI query has chart_quality='high'."""
        result = _infer(
            "SELECT SUM(x) AS total FROM (VALUES (1.0),(2.0),(3.0)) t(x)",
            data=[{"total": 6.0}],
            schema=[ColumnSchema(name="total", type="DOUBLE")],
        )
        assert result.chart_quality == "high"

    def test_ambiguous_query_has_valid_quality(self) -> None:
        """§7.1 — Every query has a quality field from the set {high, medium, low}."""
        result = _infer(
            "SELECT COUNT(*) AS n "
            "FROM (VALUES (1),(2),(3),(4),(5),(6),(7),(8),(9),(10)) t(v)",
            data=[{"n": 10}],
            schema=[ColumnSchema(name="n", type="BIGINT")],
        )
        assert result.chart_quality in {"high", "medium", "low"}

    def test_intent_quality_is_valid(self) -> None:
        """§7.2 — intent_quality is always one of the 3 valid values."""
        result = _infer(
            "SELECT cat, SUM(v) AS total "
            "FROM (VALUES ('A',10.0)) t(cat,v) GROUP BY cat",
            data=[{"cat": "A", "total": 10.0}],
            schema=[ColumnSchema(name="cat", type="VARCHAR"), ColumnSchema(name="total", type="DOUBLE")],
        )
        assert result.intent_quality in {"high", "medium", "low"}

    def test_score_trace_present(self) -> None:
        """§7.2 — score_trace dict (top signals) present in result."""
        result = _infer(
            "SELECT SUM(x) AS total FROM (VALUES (1.0)) t(x)",
            data=[{"total": 1.0}],
            schema=[ColumnSchema(name="total", type="DOUBLE")],
        )
        assert isinstance(result.score_trace, dict)


# ── §8 KPI Shelf Layout ───────────────────────────────────────────────────────

class TestKPIShelfLayout:
    """§8 — col_span, centering, and row ordering are computed by DashboardEngine
    and fully automatable. Number formatting and trend arrow colors are manual.
    """

    def _kpi(self, label: str) -> tuple[str, object]:
        sql = f"SELECT SUM(x) AS total_{label} FROM (VALUES (1.0)) t(x)"
        r = _infer(
            sql,
            data=[{f"total_{label}": 1.0}],
            schema=[ColumnSchema(name=f"total_{label}", type="DOUBLE")],
        )
        return (label, r)

    def _compose(self, n: int):
        return DashboardEngine().compose([self._kpi(str(i)) for i in range(n)])

    def _flat_panels(self, layout):
        return [p for row in layout.rows for p in row.panels]

    def test_single_kpi_col_span_4(self) -> None:
        """§8.1 — 1 KPI → col_span=4."""
        panels = self._flat_panels(self._compose(1))
        assert panels[0].final_col_span == 4

    def test_single_kpi_centered_offset_4(self) -> None:
        """§8.1 — 1 KPI centered: col_offset=4 (4+4+4=12)."""
        panels = self._flat_panels(self._compose(1))
        assert panels[0].col_offset == 4

    def test_two_kpis_col_span_4_each(self) -> None:
        """§8.2 — 2 KPIs each have col_span=4."""
        panels = self._flat_panels(self._compose(2))
        assert all(p.final_col_span == 4 for p in panels)

    def test_two_kpis_centered_offset_2(self) -> None:
        """§8.2 — 2 KPIs centered: first starts at col_offset=2 (2+4+4+2=12)."""
        panels = self._flat_panels(self._compose(2))
        assert panels[0].col_offset == 2

    def test_three_kpis_col_span_4_each(self) -> None:
        """§8.3 — 3 KPIs each have col_span=4 (4+4+4=12)."""
        panels = self._flat_panels(self._compose(3))
        assert all(p.final_col_span == 4 for p in panels)

    def test_four_kpis_col_span_3_each(self) -> None:
        """§8.4 — 4 KPIs each have col_span=3 (3+3+3+3=12)."""
        panels = self._flat_panels(self._compose(4))
        assert all(p.final_col_span == 3 for p in panels)

    def test_four_kpis_total_span_12(self) -> None:
        """§8.4 — 4 KPIs fill the row exactly: sum of col_spans=12."""
        panels = self._flat_panels(self._compose(4))
        assert sum(p.final_col_span for p in panels) == 12

    def test_kpi_shelf_row_before_chart_row(self) -> None:
        """§8.5 — KPI row_index < line chart row_index."""
        kpi_p = self._kpi("a")
        # 6-point series guarantees "line" inference
        line_r = _infer(
            "SELECT month, SUM(revenue) AS monthly_revenue "
            "FROM (VALUES (1,15000.0),(2,12000.0),(3,18000.0),"
            "(4,16000.0),(5,21000.0),(6,19000.0)) AS t(month,revenue) "
            "GROUP BY month ORDER BY month",
            data=[{"month": m, "monthly_revenue": float(v)}
                  for m, v in zip(range(1, 7), [15000, 12000, 18000, 16000, 21000, 19000])],
            schema=[ColumnSchema(name="month", type="INTEGER"),
                    ColumnSchema(name="monthly_revenue", type="DOUBLE")],
        )
        layout = DashboardEngine().compose([kpi_p, ("line", line_r)])
        panels = self._flat_panels(layout)
        kpi_panel = next(p for p in panels if p.inference_result.chart_winner == "kpi")
        line_panel = next(p for p in panels if p.inference_result.chart_winner == "line")
        assert kpi_panel.row_index < line_panel.row_index

    def test_trend_direction_label_is_valid(self) -> None:
        """§8.6 — trend_direction_label is always one of the 4 valid values."""
        result = _infer(
            "SELECT SUM(x) AS total FROM (VALUES (1.0)) t(x)",
            data=[{"total": 1.0}],
            schema=[ColumnSchema(name="total", type="DOUBLE")],
        )
        assert result.trend_direction_label in {"growing", "declining", "flat", "unknown"}

    def test_single_kpi_trend_is_unknown(self) -> None:
        """§8.6 — Single aggregate KPI has no trend → 'unknown'."""
        result = _infer(
            "SELECT SUM(x) AS total FROM (VALUES (1.0),(2.0),(3.0)) t(x)",
            data=[{"total": 6.0}],
            schema=[ColumnSchema(name="total", type="DOUBLE")],
        )
        assert result.trend_direction_label == "unknown"


# ── §9 Share Flows ────────────────────────────────────────────────────────────

class TestShareFlows:
    """§9 — §9.4–9.5 (revoke, regenerate) covered by test_shares.py.
    New: viewer-side access without admin session.
    """

    def _share(
        self,
        client: TestClient,
        dash_id: str,
        mode: str = "private",
        pw: str | None = None,
    ) -> str:
        body: dict = {"mode": mode}
        if pw:
            body["password"] = pw
        r = client.post(f"/api/v1/dashboards/{dash_id}/share", json=body)
        assert r.status_code == 201
        return r.json()["token"]

    def test_private_share_accessible_without_session(
        self, admin_client: TestClient, admin_dash_id: str
    ) -> None:
        """§9.1 — /view/<token> returns 200 with no session cookie."""
        token = self._share(admin_client, admin_dash_id)
        with TestClient(admin_client.app) as anon:
            resp = anon.get(f"/view/{token}")
        assert resp.status_code == 200

    def test_private_share_response_has_dashboard_key(
        self, admin_client: TestClient, admin_dash_id: str
    ) -> None:
        """§9.1 — Share response body includes dashboard data."""
        token = self._share(admin_client, admin_dash_id)
        with TestClient(admin_client.app) as anon:
            body = anon.get(f"/view/{token}").json()
        assert "dashboard" in body

    def test_password_share_wrong_password_rejected(
        self, admin_client: TestClient, admin_dash_id: str
    ) -> None:
        """§9.2 — Wrong unlock password → 401."""
        token = self._share(admin_client, admin_dash_id, mode="password", pw="secret123")
        with TestClient(admin_client.app) as anon:
            resp = anon.post(f"/view/{token}/unlock", json={"password": "wrong"})
        assert resp.status_code == 401

    def test_password_share_correct_password_works(
        self, admin_client: TestClient, admin_dash_id: str
    ) -> None:
        """§9.2 — Correct unlock password → 200."""
        token = self._share(admin_client, admin_dash_id, mode="password", pw="secret123")
        with TestClient(admin_client.app) as anon:
            resp = anon.post(f"/view/{token}/unlock", json={"password": "secret123"})
        assert resp.status_code == 200

    def test_public_share_accessible_without_session(
        self, admin_client: TestClient, admin_dash_id: str
    ) -> None:
        """§9.3 — Public share loads without any auth."""
        token = self._share(admin_client, admin_dash_id, mode="public")
        with TestClient(admin_client.app) as anon:
            resp = anon.get(f"/view/{token}")
        assert resp.status_code == 200


# ── §10 Example Dashboard ─────────────────────────────────────────────────────

class TestExampleDashboard:
    """§10 — §10.3 (singleton-connection regression) covered by test_demo.py.
    §10.1 adds value/row/ordering checks on top of the chart-type checks
    already in test_demo.py.
    """

    def _panels(self, demo_client: TestClient) -> list[dict]:
        return [
            p
            for row in demo_client.get("/api/v1/demo/dashboard").json()["rows"]
            for p in row["panels"]
        ]

    def test_kpi_total_revenue_value_is_42000(self, demo_client: TestClient) -> None:
        """§10.1 — KPI value = 42,000.0 (15000+12000+15000)."""
        panels = self._panels(demo_client)
        kpi = next(p for p in panels if p["inference_result"]["chart_winner"] == "kpi")
        numeric_values = [v for v in kpi["data"][0].values() if isinstance(v, (int, float))]
        assert any(abs(v - 42000.0) < 0.01 for v in numeric_values)

    def test_line_panel_has_six_data_points(self, demo_client: TestClient) -> None:
        """§10.1 — Monthly revenue line chart has 6 rows (months 1–6)."""
        panels = self._panels(demo_client)
        line = next(p for p in panels if p["inference_result"]["chart_winner"] == "line")
        assert len(line["data"]) == 6

    def test_bar_panel_has_four_categories(self, demo_client: TestClient) -> None:
        """§10.1 — Bar chart (total_sales) has 4 category rows."""
        panels = self._panels(demo_client)
        bar = next(p for p in panels if p["inference_result"]["chart_winner"] == "bar")
        assert len(bar["data"]) == 4

    def test_bar_horizontal_ordered_desc(self, demo_client: TestClient) -> None:
        """§10.1 — bar_horizontal rows are ordered by regional_revenue DESC."""
        panels = self._panels(demo_client)
        bh = next(p for p in panels if p["inference_result"]["chart_winner"] == "bar_horizontal")
        revenues = [list(row.values())[1] for row in bh["data"]]
        assert revenues == sorted(revenues, reverse=True)

    def test_kpi_is_in_kpi_shelf_col_span_4(self, demo_client: TestClient) -> None:
        """§10.1 — KPI panel has final_col_span=4 (KPI Shelf positioning)."""
        panels = self._panels(demo_client)
        kpi = next(p for p in panels if p["inference_result"]["chart_winner"] == "kpi")
        assert kpi["final_col_span"] == 4

    def test_line_chart_is_full_width(self, demo_client: TestClient) -> None:
        """§10.1 — Line chart is full-width (col_span=12)."""
        panels = self._panels(demo_client)
        line = next(p for p in panels if p["inference_result"]["chart_winner"] == "line")
        assert line["final_col_span"] == 12

    def test_persistent_mode_produces_same_four_chart_types(
        self, client: TestClient
    ) -> None:
        """§10.2 — Same 4 demo queries in persistent mode → kpi, line, bar, bar_horizontal."""
        demo_queries = [
            "SELECT SUM(amount) AS total_revenue "
            "FROM (VALUES (15000.0),(12000.0),(15000.0)) t(amount)",
            "SELECT month, SUM(revenue) AS monthly_revenue "
            "FROM (VALUES (1,15000.0),(2,12000.0),(3,18000.0),"
            "(4,16000.0),(5,21000.0),(6,19000.0)) AS t(month,revenue) "
            "GROUP BY month ORDER BY month",
            "SELECT category, SUM(sales) AS total_sales "
            "FROM (VALUES ('Electronics',45000.0),('Clothing',28000.0),"
            "('Food',15000.0),('Books',8000.0)) AS t(category,sales) "
            "GROUP BY category ORDER BY category",
            "SELECT region, SUM(revenue) AS regional_revenue "
            "FROM (VALUES ('North',35000.0),('South',28000.0),"
            "('East',22000.0),('West',31000.0)) AS t(region,revenue) "
            "GROUP BY region ORDER BY regional_revenue DESC LIMIT 4",
        ]
        dash = client.post("/api/v1/dashboards", json={"name": "D"}).json()
        chart_types = set()
        for i, sql in enumerate(demo_queries):
            panel = client.post("/api/v1/panels", json={
                "dashboard_id": dash["id"],
                "name": f"P{i}",
                "sql_content": sql,
            }).json()
            body = client.post(f"/api/v1/panels/{panel['id']}/execute").json()
            chart_types.add(body["inference_result"]["chart_winner"])
        assert chart_types == {"kpi", "line", "bar", "bar_horizontal"}


# ── §11 Edge Cases ────────────────────────────────────────────────────────────

class TestEdgeCases:
    """§11 — §11.1 (invalid SQL fallback) covered by test_execute.py.
    UI behaviors (error toolbar, empty state message) are manual.
    """

    def test_no_rows_returns_empty_data(self, client: TestClient) -> None:
        """§11.2 — WHERE clause that matches nothing → data=[]."""
        body = _exec_sql(
            client,
            "SELECT month, SUM(rev) AS rev "
            "FROM (VALUES (1,10.0),(2,20.0)) t(month,rev) "
            "WHERE month > 999 GROUP BY month",
        )
        assert body["data"] == []

    def test_no_rows_returns_200_no_crash(self, client: TestClient) -> None:
        """§11.2 — 0-row result returns HTTP 200, no 5xx."""
        dash = client.post("/api/v1/dashboards", json={"name": "D"}).json()
        panel = client.post("/api/v1/panels", json={
            "dashboard_id": dash["id"],
            "name": "P",
            "sql_content": (
                "SELECT month, SUM(rev) AS rev "
                "FROM (VALUES (1,10.0)) t(month,rev) "
                "WHERE month > 999 GROUP BY month"
            ),
        }).json()
        resp = client.post(f"/api/v1/panels/{panel['id']}/execute")
        assert resp.status_code == 200

    def test_delete_all_panels_leaves_empty_list(self, client: TestClient) -> None:
        """§11.4 — Delete all panels → panel list for dashboard is empty."""
        dash = client.post("/api/v1/dashboards", json={"name": "D"}).json()
        p1 = client.post("/api/v1/panels", json={
            "dashboard_id": dash["id"], "name": "P1",
            "sql_content": "SELECT 1 AS x",
        }).json()["id"]
        p2 = client.post("/api/v1/panels", json={
            "dashboard_id": dash["id"], "name": "P2",
            "sql_content": "SELECT 2 AS x",
        }).json()["id"]
        client.delete(f"/api/v1/panels/{p1}")
        client.delete(f"/api/v1/panels/{p2}")
        panels = client.get("/api/v1/panels", params={"dashboard_id": dash["id"]}).json()
        assert panels == []

    def test_fresh_panels_work_after_delete(self, client: TestClient) -> None:
        """§11.4 — After deleting all, new SQL creates and executes fresh panels."""
        dash = client.post("/api/v1/dashboards", json={"name": "D"}).json()
        old = client.post("/api/v1/panels", json={
            "dashboard_id": dash["id"], "name": "Old",
            "sql_content": "SELECT 1 AS x",
        }).json()["id"]
        client.delete(f"/api/v1/panels/{old}")
        new = client.post("/api/v1/panels", json={
            "dashboard_id": dash["id"], "name": "New",
            "sql_content": "SELECT SUM(x) AS total FROM (VALUES (1.0),(2.0)) t(x)",
        }).json()["id"]
        body = client.post(f"/api/v1/panels/{new}/execute").json()
        assert body["data"] == [{"total": 3.0}]
