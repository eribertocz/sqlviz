"""Transactional folder hierarchy and dashboard placement in a project."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone

import duckdb
from sqlviz_core.models.folders import (
    Folder,
    FolderChanges,
    FolderError,
    validate_folder_changes,
    validate_folder_parent,
)

from sqlviz_storage.transactions import project_transaction

FOLDER_TREE_REVISION_KEY = "folder_tree_revision"
_SELECT = "SELECT id, name, parent_id, sort_order, created_at FROM folders"


class FolderWriteConflict(Exception):
    """A conflicting metadata write was rolled back; refresh and retry."""


@contextmanager
def folder_tree_write(db: duckdb.DuckDBPyConnection) -> Iterator[None]:
    """Fence the whole tree before validation to prevent concurrent write skew.

    The revision is an internal metadata value, created lazily in the same
    transaction. Every folder mutation and dashboard placement participates.
    Analytical requests do not acquire this fence. No application-global lock
    or schema change is needed.
    """
    try:
        with project_transaction(db):
            row = db.execute(
                "SELECT value FROM _sqlviz_meta WHERE key = ?", [FOLDER_TREE_REVISION_KEY],
            ).fetchone()
            if row is None:
                db.execute("INSERT INTO _sqlviz_meta VALUES (?, '1')", [FOLDER_TREE_REVISION_KEY])
            else:
                try:
                    revision = int(row[0])
                    if revision < 0:
                        raise ValueError
                except (TypeError, ValueError):
                    raise FolderError(
                        "folder_hierarchy_invalid", "Folder hierarchy revision is invalid",
                    ) from None
                db.execute(
                    "UPDATE _sqlviz_meta SET value = ? WHERE key = ?",
                    [str(revision + 1), FOLDER_TREE_REVISION_KEY],
                )
            yield
    except (duckdb.TransactionException, duckdb.ConstraintException) as exc:
        raise FolderWriteConflict("Folder write conflicted; refresh and retry") from exc


class FolderRepository:
    def __init__(self, db: duckdb.DuckDBPyConnection) -> None:
        self._db = db

    def get(self, folder_id: str) -> Folder:
        row = self._db.execute(f"{_SELECT} WHERE id = ?", [folder_id]).fetchone()
        if row is None:
            raise FolderError("folder_not_found", "Folder not found")
        return Folder(*row)

    def list(self) -> list[Folder]:
        return [Folder(*row) for row in self._db.execute(
            f"{_SELECT} ORDER BY sort_order, created_at, id",
        ).fetchall()]

    def _validate_parent(self, parent_id: str | None, *, folder_id: str | None = None) -> None:
        if parent_id is None:
            return
        parents = dict(self._db.execute("SELECT id, parent_id FROM folders").fetchall())
        validate_folder_parent(parent_id, parents, folder_id=folder_id)

    def create(self, name: str, parent_id: str | None = None, sort_order: int = 0) -> Folder:
        validate_folder_changes({"name": name, "parent_id": parent_id, "sort_order": sort_order})
        folder_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        parent_id = parent_id or None
        with folder_tree_write(self._db):
            self._validate_parent(parent_id, folder_id=folder_id)
            self._db.execute(
                "INSERT INTO folders (id, name, parent_id, sort_order, created_at) "
                "VALUES (?, ?, ?, ?, ?)", [folder_id, name, parent_id, sort_order, created_at],
            )
        return Folder(folder_id, name, parent_id, sort_order, created_at)

    def update(self, folder_id: str, changes: FolderChanges) -> Folder:
        validate_folder_changes(changes)
        if not changes:
            return self.get(folder_id)
        with folder_tree_write(self._db):
            self.get(folder_id)
            values = dict(changes)
            if "parent_id" in changes:
                parent_id = changes["parent_id"] or None
                self._validate_parent(parent_id, folder_id=folder_id)
                values["parent_id"] = parent_id
            # Names were whitelisted by core before interpolation.
            assignments = ", ".join(f"{column} = ?" for column in values)
            self._db.execute(
                f"UPDATE folders SET {assignments} WHERE id = ?", [*values.values(), folder_id],
            )
            result = self.get(folder_id)
        return result

    def delete(self, folder_id: str) -> None:
        with folder_tree_write(self._db):
            self.get(folder_id)
            self._db.execute(
                "UPDATE dashboards SET folder_id = NULL WHERE folder_id = ?", [folder_id],
            )
            self._db.execute("UPDATE folders SET parent_id = NULL WHERE parent_id = ?", [folder_id])
            self._db.execute("DELETE FROM folders WHERE id = ?", [folder_id])

    @contextmanager
    def dashboard_placement(self, folder_id: str | None) -> Iterator[None]:
        """Validate destination and commit the caller's dashboard write atomically."""
        with folder_tree_write(self._db):
            self._validate_parent(folder_id)
            yield
