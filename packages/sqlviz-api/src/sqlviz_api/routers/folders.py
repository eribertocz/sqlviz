"""Folder CRUD — /api/v1/folders.

Folders provide the tree structure shown in the Sidebar (DOC6).
The `parent_id` column is a self-reference; NULL means the folder
sits at the root level.

Design decision — DELETE cascades to root, not to trash:
    When a folder is deleted, its direct child dashboards have their
    folder_id set to NULL (moved to root), and its direct child folders
    have their parent_id set to NULL (also moved to root).
    Nothing is deleted except the folder itself.
    Rationale: dashboards and sub-folders are independent objects
    that the user created intentionally; deleting a container must not
    silently destroy content.

Note: the `folders` table has no `updated_at` column (schema Phase 3.1).
FolderResponse therefore does not include an updated_at field.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from sqlviz_api.dependencies import DbDep
from sqlviz_api.models import FolderCreate, FolderResponse, FolderUpdate

router = APIRouter(prefix="/api/v1/folders", tags=["folders"])

_SELECT = (
    "SELECT id, name, parent_id, sort_order, created_at "
    "FROM folders"
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _row_to_response(
    row: tuple[str, str, str | None, int, str]
) -> FolderResponse:
    return FolderResponse(
        id=row[0],
        name=row[1],
        parent_id=row[2],
        sort_order=row[3],
        created_at=row[4],
    )


def _fetch_one(db: DbDep, folder_id: str) -> FolderResponse:
    row = db.execute(
        f"{_SELECT} WHERE id = ?", [folder_id]
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Folder '{folder_id}' not found")
    return _row_to_response(row)


@router.post("", response_model=FolderResponse, status_code=201)
def create_folder(body: FolderCreate, db: DbDep) -> FolderResponse:
    folder_id = str(uuid.uuid4())
    now = _now()
    db.execute(
        "INSERT INTO folders (id, name, parent_id, sort_order, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        [folder_id, body.name, body.parent_id, body.sort_order, now],
    )
    return FolderResponse(
        id=folder_id,
        name=body.name,
        parent_id=body.parent_id,
        sort_order=body.sort_order,
        created_at=now,
    )


@router.get("", response_model=list[FolderResponse])
def list_folders(db: DbDep) -> list[FolderResponse]:
    rows = db.execute(
        f"{_SELECT} ORDER BY sort_order, created_at"
    ).fetchall()
    return [_row_to_response(r) for r in rows]


@router.get("/{folder_id}", response_model=FolderResponse)
def get_folder(folder_id: str, db: DbDep) -> FolderResponse:
    return _fetch_one(db, folder_id)


@router.patch("/{folder_id}", response_model=FolderResponse)
def update_folder(folder_id: str, body: FolderUpdate, db: DbDep) -> FolderResponse:
    _fetch_one(db, folder_id)  # raises 404 if missing

    updates: dict[str, str | int] = {}
    if body.name is not None:
        updates["name"] = body.name
    if body.parent_id is not None:
        updates["parent_id"] = body.parent_id
    if body.sort_order is not None:
        updates["sort_order"] = body.sort_order

    if updates:
        set_clause = ", ".join(f"{col} = ?" for col in updates)
        db.execute(
            f"UPDATE folders SET {set_clause} WHERE id = ?",
            [*updates.values(), folder_id],
        )

    return _fetch_one(db, folder_id)


@router.delete("/{folder_id}", status_code=204)
def delete_folder(folder_id: str, db: DbDep) -> None:
    """Delete a folder and orphan its contents to root.

    Dashboards with folder_id = folder_id → folder_id set to NULL.
    Child folders with parent_id = folder_id → parent_id set to NULL.
    The folder itself is then deleted.
    All three operations run in a single transaction.
    """
    _fetch_one(db, folder_id)  # raises 404 if missing

    db.begin()
    try:
        db.execute(
            "UPDATE dashboards SET folder_id = NULL WHERE folder_id = ?",
            [folder_id],
        )
        db.execute(
            "UPDATE folders SET parent_id = NULL WHERE parent_id = ?",
            [folder_id],
        )
        db.execute("DELETE FROM folders WHERE id = ?", [folder_id])
        db.commit()
    except Exception:
        db.rollback()
        raise
