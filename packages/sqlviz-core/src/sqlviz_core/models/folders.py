"""Folder values and hierarchy rules, independent of HTTP and persistence."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, TypedDict

FolderErrorCode = Literal[
    "folder_not_found", "folder_parent_not_found", "folder_cycle",
    "folder_hierarchy_invalid", "folder_values_invalid",
]


class FolderError(Exception):
    def __init__(self, code: FolderErrorCode, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class Folder:
    id: str
    name: str
    parent_id: str | None
    sort_order: int
    created_at: str


class FolderChanges(TypedDict, total=False):
    name: str
    parent_id: str | None
    sort_order: int


def validate_folder_changes(changes: FolderChanges) -> None:
    if not changes.keys() <= {"name", "parent_id", "sort_order"}:
        raise FolderError("folder_values_invalid", "Unknown folder field")
    if "name" in changes:
        name = changes["name"]
        if not isinstance(name, str) or not name.strip():
            raise FolderError("folder_values_invalid", "Folder name must not be blank")
    if "parent_id" in changes:
        parent = changes["parent_id"]
        if parent is not None and not isinstance(parent, str):
            raise FolderError("folder_values_invalid", "Folder parent must be a string or null")
    if "sort_order" in changes:
        order = changes["sort_order"]
        if type(order) is not int or not -(2**31) <= order < 2**31:
            raise FolderError("folder_values_invalid", "Folder sort order must be a 32-bit integer")


def validate_folder_parent(
    parent_id: str | None,
    parents: Mapping[str, str | None],
    *,
    folder_id: str | None = None,
) -> None:
    """Walk the destination's ancestry iteratively, including malformed legacy chains.

    Only the proposed ancestry is validated. Detaching a malformed folder to
    root is an explicit repair; unrelated historical corruption is not rewritten.
    """
    seen: set[str] = set()
    current = parent_id
    while current is not None:
        if current == folder_id:
            raise FolderError(
                "folder_cycle", "A folder cannot be moved into itself or a descendant",
            )
        if current in seen:
            raise FolderError("folder_hierarchy_invalid", "Destination hierarchy contains a cycle")
        if current not in parents:
            if current == parent_id:
                raise FolderError("folder_parent_not_found", "Destination folder does not exist")
            raise FolderError(
                "folder_hierarchy_invalid", "Destination hierarchy has a missing ancestor",
            )
        seen.add(current)
        current = parents[current]
