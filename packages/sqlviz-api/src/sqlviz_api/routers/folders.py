"""Folder CRUD; deletion moves direct contents to root and preserves their data."""

from __future__ import annotations

from fastapi import APIRouter
from sqlviz_core.models.folders import Folder, FolderChanges

from sqlviz_api.dependencies import FoldersDep
from sqlviz_api.models import FolderCreate, FolderResponse, FolderUpdate

router = APIRouter(prefix="/api/v1/folders", tags=["folders"])


def _response(folder: Folder) -> FolderResponse:
    return FolderResponse.model_validate(folder, from_attributes=True)


@router.post("", response_model=FolderResponse, status_code=201)
def create_folder(body: FolderCreate, folders: FoldersDep) -> FolderResponse:
    return _response(folders.create(body.name, body.parent_id, body.sort_order))


@router.get("", response_model=list[FolderResponse])
def list_folders(folders: FoldersDep) -> list[FolderResponse]:
    return [_response(folder) for folder in folders.list()]


@router.get("/{folder_id}", response_model=FolderResponse)
def get_folder(folder_id: str, folders: FoldersDep) -> FolderResponse:
    return _response(folders.get(folder_id))


@router.patch("/{folder_id}", response_model=FolderResponse)
def update_folder(folder_id: str, body: FolderUpdate, folders: FoldersDep) -> FolderResponse:
    changes: FolderChanges = {}
    if body.name is not None:
        changes["name"] = body.name
    if "parent_id" in body.model_fields_set:
        changes["parent_id"] = body.parent_id
    if body.sort_order is not None:
        changes["sort_order"] = body.sort_order
    return _response(folders.update(folder_id, changes))


@router.delete("/{folder_id}", status_code=204)
def delete_folder(folder_id: str, folders: FoldersDep) -> None:
    folders.delete(folder_id)
