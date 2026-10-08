"""Dashboard CRUD — /api/v1/dashboards."""

from __future__ import annotations

import uuid
from dataclasses import asdict
from datetime import datetime, timezone

from fastapi import APIRouter
from sqlviz_core.models.dashboards import Dashboard
from sqlviz_storage.dashboard_repository import DashboardRepository

from sqlviz_api.dependencies import DashboardDeletionDep, DbDep, FoldersDep
from sqlviz_api.models import DashboardCreate, DashboardResponse, DashboardUpdate

router = APIRouter(prefix="/api/v1/dashboards", tags=["dashboards"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _to_response(dashboard: Dashboard) -> DashboardResponse:
    return DashboardResponse(**asdict(dashboard))


def _fetch_one(db: DbDep, dashboard_id: str) -> DashboardResponse:
    return _to_response(DashboardRepository(db).get(dashboard_id))


@router.post("", response_model=DashboardResponse, status_code=201)
def create_dashboard(body: DashboardCreate, db: DbDep, folders: FoldersDep) -> DashboardResponse:
    dashboard_id = str(uuid.uuid4())
    now = _now()
    folder_id = body.folder_id or None
    with folders.dashboard_placement(folder_id):
        db.execute(
            "INSERT INTO dashboards "
            "(id, name, folder_id, connection_id, sql_content, sort_order, "
            "created_at, updated_at, description) "
            "VALUES (?, ?, ?, ?, '', ?, ?, ?, ?)",
            [dashboard_id, body.name, folder_id, body.connection_id,
             body.sort_order, now, now, body.description],
        )
    return DashboardResponse(
        id=dashboard_id,
        name=body.name,
        folder_id=folder_id,
        connection_id=body.connection_id,
        sort_order=body.sort_order,
        created_at=now,
        updated_at=now,
        description=body.description,
    )


@router.get("", response_model=list[DashboardResponse])
def list_dashboards(db: DbDep) -> list[DashboardResponse]:
    return [_to_response(dashboard) for dashboard in DashboardRepository(db).list()]


@router.get("/{dashboard_id}", response_model=DashboardResponse)
def get_dashboard(dashboard_id: str, db: DbDep) -> DashboardResponse:
    return _fetch_one(db, dashboard_id)


@router.patch("/{dashboard_id}", response_model=DashboardResponse)
def update_dashboard(
    dashboard_id: str, body: DashboardUpdate, db: DbDep,
) -> DashboardResponse:
    return _to_response(DashboardRepository(db).update(dashboard_id, body.changes()))


@router.delete("/{dashboard_id}", status_code=204)
def delete_dashboard(dashboard_id: str, deletion: DashboardDeletionDep) -> None:
    deletion.delete(dashboard_id)
