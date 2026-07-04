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

router = APIRouter(tags=["compose"])


class ComposeItem(BaseModel):
    panel_id: str
    inference_result: dict[str, Any]


@router.post("/api/v1/compose")
def compose_layout(body: list[ComposeItem]) -> JSONResponse:
    """Compose a DashboardLayout from provided InferenceResults.

    KPI Shelf centering (DOC5 §16.34) and narrative ordering (DOC5 §15)
    are applied by DashboardEngine. The caller enriches each panel with
    data from the execute response before rendering.
    """
    panels: list[tuple[str, InferenceResult]] = []
    for item in body:
        ir = InferenceResult(**item.inference_result)
        panels.append((item.panel_id, ir))

    layout = DashboardEngine().compose(panels)

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
