"""Dashboard CRUD — /api/v1/dashboards."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException

from sqlviz_api.dependencies import DbDep
from sqlviz_api.models import DashboardCreate, DashboardResponse, DashboardUpdate

router = APIRouter(prefix="/api/v1/dashboards", tags=["dashboards"])

_SELECT = (
    "SELECT id, name, folder_id, connection_id, sort_order, created_at, updated_at,"
    " dashboard_hint, dashboard_domain "
    "FROM dashboards"
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _row_to_response(row: tuple[Any, ...]) -> DashboardResponse:
    return DashboardResponse(
        id=row[0],
        name=row[1],
        folder_id=row[2],
        connection_id=row[3],
        sort_order=row[4],
        created_at=row[5],
        updated_at=row[6],
        dashboard_hint=row[7],
        dashboard_domain=row[8],
    )


def _fetch_one(db: DbDep, dashboard_id: str) -> DashboardResponse:
    row = db.execute(
        f"{_SELECT} WHERE id = ?", [dashboard_id]
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Dashboard '{dashboard_id}' not found")
    return _row_to_response(row)


@router.post("", response_model=DashboardResponse, status_code=201)
def create_dashboard(body: DashboardCreate, db: DbDep) -> DashboardResponse:
    dashboard_id = str(uuid.uuid4())
    now = _now()
    db.execute(
        "INSERT INTO dashboards "
        "(id, name, folder_id, connection_id, sql_content, sort_order, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, '', ?, ?, ?)",
        [dashboard_id, body.name, body.folder_id, body.connection_id, body.sort_order, now, now],
    )
    return DashboardResponse(
        id=dashboard_id,
        name=body.name,
        folder_id=body.folder_id,
        connection_id=body.connection_id,
        sort_order=body.sort_order,
        created_at=now,
        updated_at=now,
    )


@router.get("", response_model=list[DashboardResponse])
def list_dashboards(db: DbDep) -> list[DashboardResponse]:
    rows = db.execute(
        f"{_SELECT} ORDER BY sort_order, created_at"
    ).fetchall()
    return [_row_to_response(r) for r in rows]


@router.get("/{dashboard_id}", response_model=DashboardResponse)
def get_dashboard(dashboard_id: str, db: DbDep) -> DashboardResponse:
    return _fetch_one(db, dashboard_id)


@router.patch("/{dashboard_id}", response_model=DashboardResponse)
def update_dashboard(
    dashboard_id: str, body: DashboardUpdate, db: DbDep
) -> DashboardResponse:
    _fetch_one(db, dashboard_id)  # raises 404 if missing

    updates: dict[str, str | int] = {}
    if body.name is not None:
        updates["name"] = body.name
    if body.folder_id is not None:
        updates["folder_id"] = body.folder_id
    if body.connection_id is not None:
        updates["connection_id"] = body.connection_id
    if body.sort_order is not None:
        updates["sort_order"] = body.sort_order
    updates["updated_at"] = _now()

    set_clause = ", ".join(f"{col} = ?" for col in updates)
    db.execute(
        f"UPDATE dashboards SET {set_clause} WHERE id = ?",
        [*updates.values(), dashboard_id],
    )
    return _fetch_one(db, dashboard_id)


@router.delete("/{dashboard_id}", status_code=204)
def delete_dashboard(dashboard_id: str, db: DbDep) -> None:
    _fetch_one(db, dashboard_id)  # raises 404 if missing
    db.execute("DELETE FROM dashboards WHERE id = ?", [dashboard_id])
