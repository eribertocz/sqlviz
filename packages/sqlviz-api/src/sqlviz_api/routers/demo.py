"""Demo dashboard endpoint — Phase 5.2 development aid.

Returns a DashboardLayout (DOC5 §15.4) for 4 canonical panel types
(KPI, trend/line, bar × 2) using DuckDB VALUES queries — no external
tables needed, no project data touched.

The layout is produced by DashboardEngine.compose(), so KPIs are
grouped with KPI Shelf v0.1 centering (DOC5 §16.34), and other panels
are ordered narratively (Rule 2) and row-packed (Rules 3-4). This is
the same engine used for real dashboards.

Safe in production: pure SELECT, no mutations.
"""

from __future__ import annotations

from typing import Any

import sqlviz_inference
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlviz_core.models import ColumnSchema
from sqlviz_inference.dashboard import DashboardEngine, DashboardLayout
from sqlviz_inference.result import InferenceResult

from sqlviz_api.dependencies import DbDep
from sqlviz_api.serialization import json_safe

router = APIRouter(tags=["demo"])

_DEMO_QUERIES: list[str] = [
    (
        "SELECT SUM(amount) AS total_revenue "
        "FROM (VALUES (15000.0), (12000.0), (15000.0)) t(amount)"
    ),
    (
        "SELECT month, SUM(revenue) AS monthly_revenue "
        "FROM (VALUES "
        "(1, 15000.0), (2, 12000.0), (3, 18000.0), "
        "(4, 16000.0), (5, 21000.0), (6, 19000.0)) "
        "AS t(month, revenue) "
        "GROUP BY month ORDER BY month"
    ),
    (
        "SELECT category, SUM(sales) AS total_sales "
        "FROM (VALUES "
        "('Electronics', 45000.0), ('Clothing', 28000.0), "
        "('Food', 15000.0), ('Books', 8000.0)) "
        "AS t(category, sales) "
        "GROUP BY category ORDER BY category"
    ),
    (
        "SELECT region, SUM(revenue) AS regional_revenue "
        "FROM (VALUES "
        "('North', 35000.0), ('South', 28000.0), "
        "('East', 22000.0), ('West', 31000.0)) "
        "AS t(region, revenue) "
        "GROUP BY region ORDER BY regional_revenue DESC "
        "LIMIT 4"
    ),
]


def _layout_to_dict(
    layout: DashboardLayout,
    panel_data: dict[str, list[dict[str, object]]],
) -> dict[str, Any]:
    """Serialize DashboardLayout to a JSON-safe dict including query result rows.

    Uses InferenceResult.to_dict() (dataclasses.asdict) for each panel's
    inference_result. The `data` key carries the raw query result rows so
    the frontend can render KPI values and chart series without a separate
    per-panel fetch.
    """
    return {
        "rows": [
            {
                "panels": [
                    {
                        "panel_id": dp.panel_id,
                        "final_col_span": dp.final_col_span,
                        "col_offset": dp.col_offset,
                        "row_index": dp.row_index,
                        "data": panel_data.get(dp.panel_id, []),
                        "inference_result": dp.inference_result.to_dict(),
                    }
                    for dp in row.panels
                ]
            }
            for row in layout.rows
        ]
    }



def _run_queries(
    db: Any,
    queries: list[str],
    id_prefix: str,
) -> tuple[list[tuple[str, InferenceResult]], dict[str, list[dict[str, object]]]]:
    """Execute SQL queries, infer each result, return (panels, data_map)."""
    panels_for_compose: list[tuple[str, InferenceResult]] = []
    panel_data: dict[str, list[dict[str, object]]] = {}
    for i, sql in enumerate(queries):
        db.execute(sql)
        desc = db.description or []
        col_names = [str(d[0]) for d in desc]
        rows_raw = db.fetchall()
        data: list[dict[str, object]] = [
            {k: json_safe(v) for k, v in zip(col_names, row)}
            for row in rows_raw
        ]
        schema = [ColumnSchema(name=str(d[0]), type=str(d[1])) for d in desc]
        result = sqlviz_inference.infer(sql, data=data, schema=schema)
        panel_id = f"{id_prefix}-{i}"
        panel_data[panel_id] = data
        panels_for_compose.append((panel_id, result))
    return panels_for_compose, panel_data


@router.get("/api/v1/demo/dashboard")
def demo_dashboard(db: DbDep) -> JSONResponse:
    """Execute 4 demo SQL queries, compose via DashboardEngine, return layout."""
    panels, panel_data = _run_queries(db, _DEMO_QUERIES, "demo")
    layout = DashboardEngine().compose(panels)
    return JSONResponse(content=_layout_to_dict(layout, panel_data))


@router.get("/api/v1/demo/sql")
def demo_sql() -> dict[str, str]:
    """Return the 4 demo queries as a single editor-ready SQL string.

    Queries are separated by semicolons so the frontend can seed the Monaco
    editor in demo mode and auto-run the example dashboard.
    """
    return {"sql": ";\n\n".join(_DEMO_QUERIES)}
