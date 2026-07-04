"""Panel CRUD — /api/v1/panels.

A panel belongs to exactly one dashboard and carries the SQL content
that will be executed and inferred in Phase 4.2.

Creating a panel with a non-existent dashboard_id returns 404:
the dashboard is a resource that must exist before panels can belong to it.
"""

from __future__ import annotations

import dataclasses
import re
import uuid
from datetime import datetime, timezone
from typing import Any

import duckdb
import sqlviz_inference
from fastapi import APIRouter, Body, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlviz_core.models import ColumnSchema

from sqlviz_api.dependencies import DbDep
from sqlviz_api.models import PanelCreate, PanelResponse, PanelUpdate
from sqlviz_api.serialization import json_safe

_VARIABLE_RE = re.compile(r"\$(\w+)")


class ExecuteBody(BaseModel):
    variables: dict[str, Any] = Field(default_factory=dict)

router = APIRouter(prefix="/api/v1/panels", tags=["panels"])

_SELECT = (
    "SELECT id, dashboard_id, name, sql_content, sort_order, created_at, updated_at "
    "FROM panels"
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")



def _row_to_response(
    row: tuple[str, str, str, str, int, str, str]
) -> PanelResponse:
    return PanelResponse(
        id=row[0],
        dashboard_id=row[1],
        name=row[2],
        sql_content=row[3],
        sort_order=row[4],
        created_at=row[5],
        updated_at=row[6],
    )


def _require_dashboard(db: DbDep, dashboard_id: str) -> None:
    row = db.execute(
        "SELECT id FROM dashboards WHERE id = ?", [dashboard_id]
    ).fetchone()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Dashboard '{dashboard_id}' not found",
        )


def _fetch_one(db: DbDep, panel_id: str) -> PanelResponse:
    row = db.execute(
        f"{_SELECT} WHERE id = ?", [panel_id]
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Panel '{panel_id}' not found")
    return _row_to_response(row)


@router.get("", response_model=list[PanelResponse])
def list_panels(
    db: DbDep,
    dashboard_id: str | None = Query(default=None),
) -> list[PanelResponse]:
    """List panels, optionally filtered by dashboard_id."""
    if dashboard_id is not None:
        rows = db.execute(
            f"{_SELECT} WHERE dashboard_id = ? ORDER BY sort_order, created_at",
            [dashboard_id],
        ).fetchall()
    else:
        rows = db.execute(
            f"{_SELECT} ORDER BY sort_order, created_at"
        ).fetchall()
    return [_row_to_response(r) for r in rows]


@router.post("", response_model=PanelResponse, status_code=201)
def create_panel(body: PanelCreate, db: DbDep) -> PanelResponse:
    _require_dashboard(db, body.dashboard_id)

    panel_id = str(uuid.uuid4())
    now = _now()
    db.execute(
        "INSERT INTO panels "
        "(id, dashboard_id, name, sql_content, sort_order, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        [panel_id, body.dashboard_id, body.name, body.sql_content, body.sort_order, now, now],
    )
    return PanelResponse(
        id=panel_id,
        dashboard_id=body.dashboard_id,
        name=body.name,
        sql_content=body.sql_content,
        sort_order=body.sort_order,
        created_at=now,
        updated_at=now,
    )


@router.get("/{panel_id}", response_model=PanelResponse)
def get_panel(panel_id: str, db: DbDep) -> PanelResponse:
    return _fetch_one(db, panel_id)


@router.patch("/{panel_id}", response_model=PanelResponse)
def update_panel(panel_id: str, body: PanelUpdate, db: DbDep) -> PanelResponse:
    _fetch_one(db, panel_id)  # raises 404 if missing

    updates: dict[str, str | int] = {}
    if body.name is not None:
        updates["name"] = body.name
    if body.sql_content is not None:
        updates["sql_content"] = body.sql_content
    if body.sort_order is not None:
        updates["sort_order"] = body.sort_order
    updates["updated_at"] = _now()

    set_clause = ", ".join(f"{col} = ?" for col in updates)
    db.execute(
        f"UPDATE panels SET {set_clause} WHERE id = ?",
        [*updates.values(), panel_id],
    )
    return _fetch_one(db, panel_id)


@router.delete("/{panel_id}", status_code=204)
def delete_panel(panel_id: str, db: DbDep) -> None:
    _fetch_one(db, panel_id)  # raises 404 if missing
    db.execute("DELETE FROM panels WHERE id = ?", [panel_id])


@router.post("/{panel_id}/execute")
def execute_panel(
    panel_id: str,
    db: DbDep,
    body: ExecuteBody | None = Body(default=None),
) -> JSONResponse:
    """Execute a panel's SQL and return {inference_result, data}.

    Accepts an optional body with {variables: {name: value}} for $variable
    substitution (filter controls, Phase 5.7).

    SQL with $variables but no values provided → 200 with fallback_applied=True
    (inference runs on SQL structure; filter_controls are populated so the UI
    can show the filter bar).

    SQL syntax error → 200 with fallback_applied=True + empty data.
    Missing table (CatalogException) → 422. Panel not found → 404.
    """
    panel = _fetch_one(db, panel_id)
    sql = panel.sql_content
    variables: dict[str, Any] = body.variables if body else {}

    # If SQL has $params but no values are provided, run inference-only so the
    # frontend can display the filter bar before any data is fetched.
    if _VARIABLE_RE.search(sql) and not variables:
        result = sqlviz_inference.infer(sql)
        result = dataclasses.replace(
            result,
            fallback_applied=True,
            fallback_reason="Set filter values to see data",
        )
        return JSONResponse(content={"inference_result": result.to_dict(), "data": []})

    try:
        if variables:
            db.execute(sql, variables)
        else:
            db.execute(sql)
    except duckdb.ParserException:
        result = sqlviz_inference.infer(sql)
        result = dataclasses.replace(
            result,
            fallback_applied=True,
            fallback_reason="SQL syntax error — query could not be parsed",
        )
        return JSONResponse(content={"inference_result": result.to_dict(), "data": []})
    except duckdb.CatalogException as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except duckdb.Error as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    desc = db.description or []
    col_names = [str(d[0]) for d in desc]
    rows_raw = db.fetchall()

    data: list[dict[str, object]] = [
        {k: json_safe(v) for k, v in zip(col_names, row)}
        for row in rows_raw
    ]
    schema = [ColumnSchema(name=str(d[0]), type=str(d[1])) for d in desc]

    result = sqlviz_inference.infer(sql, data=data, schema=schema)
    return JSONResponse(content={"inference_result": result.to_dict(), "data": data})
