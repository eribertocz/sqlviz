"""Compose endpoint — POST /api/v1/compose.

Accepts a list of {panel_id, inference_result} items and returns a
DashboardLayout produced by DashboardEngine.compose(). Raw query data
is NOT included in the response — callers enrich with data from the
execute endpoint responses.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlviz_inference.dashboard import DashboardEngine
from sqlviz_inference.result import InferenceResult

from sqlviz_api.dependencies import DbDep

router = APIRouter(tags=["compose"])


class ComposeItem(BaseModel):
    panel_id: str
    inference_result: dict[str, Any]


def _pinned_spans(db: DbDep, panel_ids: list[str]) -> dict[str, int]:
    """Widths the user pinned, read here rather than trusted from the caller.

    The KPI shelf overrides the width of the panels it centres, so it needs to
    know which ones the user set by hand. Looking that up server-side means no
    caller can forget to pass it — the admin app and a shared viewer both go
    through this endpoint, and only one of them would have been updated.
    """
    if not panel_ids:
        return {}
    placeholders = ", ".join("?" for _ in panel_ids)
    rows = db.execute(
        f"SELECT id, col_span_user_override FROM panels WHERE id IN ({placeholders})",
        panel_ids,
    ).fetchall()
    return {r[0]: r[1] for r in rows if r[1] is not None}


@router.post("/api/v1/compose")
def compose_layout(body: list[ComposeItem], db: DbDep) -> JSONResponse:
    """Compose a DashboardLayout from provided InferenceResults.

    KPI Shelf centering (DOC5 §16.34) and narrative ordering (DOC5 §15)
    are applied by DashboardEngine. The caller enriches each panel with
    data from the execute response before rendering.
    """
    panels: list[tuple[str, InferenceResult]] = []
    for item in body:
        ir = InferenceResult(**item.inference_result)
        panels.append((item.panel_id, ir))

    layout = DashboardEngine().compose(
        panels,
        pinned_spans=_pinned_spans(db, [item.panel_id for item in body]),
    )

    # Return original ir dicts unchanged (no re-serialization drift)
    ir_by_id = {item.panel_id: item.inference_result for item in body}

    return JSONResponse(content={
        "rows": [
            {
                "panels": [
                    {
                        "panel_id": dp.panel_id,
                        "final_col_span": dp.final_col_span,
                        "col_offset": dp.col_offset,
                        "row_index": dp.row_index,
                        "data": [],
                        "inference_result": ir_by_id.get(dp.panel_id, {}),
                    }
                    for dp in row.panels
                ]
            }
            for row in layout.rows
        ]
    })
