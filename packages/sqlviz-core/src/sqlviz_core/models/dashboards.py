"""Dashboard patch policy, independent of HTTP and persistence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict

MAX_DASHBOARD_NAME_LENGTH = 256
MAX_DASHBOARD_ID_LENGTH = 256
MAX_DASHBOARD_DESCRIPTION_LENGTH = 16_384
MAX_DASHBOARD_SQL_BYTES = 1024 * 1024


@dataclass(frozen=True)
class Dashboard:
    id: str
    name: str
    folder_id: str | None
    connection_id: str | None
    sort_order: int
    created_at: str
    updated_at: str
    dashboard_hint: str | None = None
    dashboard_domain: str | None = None
    description: str | None = None
    sql_content: str = ""
    last_run_at: str | None = None
    last_run_sql: str | None = None


class DashboardChanges(TypedDict, total=False):
    name: str
    folder_id: str | None
    connection_id: str | None
    sort_order: int
    description: str | None
    sql_content: str
    last_run_at: str | None
    last_run_sql: str | None


def normalize_dashboard_changes(changes: DashboardChanges) -> DashboardChanges:
    """Validate all supplied fields before writes; preserve omission and exact SQL."""
    nullable = {"folder_id", "connection_id", "description", "last_run_at", "last_run_sql"}
    allowed = nullable | {"name", "sort_order", "sql_content"}
    if not changes.keys() <= allowed:
        raise ValueError("Unknown dashboard field")
    for key, value in changes.items():
        if value is None:
            if key not in nullable:
                raise ValueError(f"{key} must not be null")
            continue
        if key == "sort_order":
            if type(value) is not int or not -(2**31) <= value < 2**31:
                raise ValueError("sort_order must be a 32-bit integer")
            continue
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string")
        try:
            text_bytes = len(value.encode("utf-8"))
        except UnicodeEncodeError:
            raise ValueError(f"{key} must be valid UTF-8 text") from None
        if key == "name" and (not value.strip() or len(value) > MAX_DASHBOARD_NAME_LENGTH):
            raise ValueError(
                f"name must contain text and be at most {MAX_DASHBOARD_NAME_LENGTH} characters",
            )
        if key in {"folder_id", "connection_id"} and (
            len(value) > MAX_DASHBOARD_ID_LENGTH or (value and not value.strip())
        ):
            raise ValueError(
                f"{key} must be nonblank and at most {MAX_DASHBOARD_ID_LENGTH} characters",
            )
        if key == "description" and len(value) > MAX_DASHBOARD_DESCRIPTION_LENGTH:
            raise ValueError(
                f"description must be at most {MAX_DASHBOARD_DESCRIPTION_LENGTH} characters",
            )
        if key in {"sql_content", "last_run_sql"} and text_bytes > MAX_DASHBOARD_SQL_BYTES:
            raise ValueError(f"{key} must be at most {MAX_DASHBOARD_SQL_BYTES} UTF-8 bytes")
        if key == "last_run_at":
            try:
                timestamp = datetime.fromisoformat(value)
            except ValueError:
                raise ValueError("last_run_at must be an ISO timestamp with a timezone") from None
            if "T" not in value or timestamp.utcoffset() is None:
                raise ValueError("last_run_at must be an ISO timestamp with a timezone")
    normalized = changes.copy()
    # Retain existing clients' empty-string clearing of placement/description;
    # an empty SQL draft or last-run SQL remains an exact empty string.
    if normalized.get("folder_id") == "":
        normalized["folder_id"] = None
    if normalized.get("connection_id") == "":
        normalized["connection_id"] = None
    if normalized.get("description") == "":
        normalized["description"] = None
    return normalized
