"""Pydantic request/response models for sqlviz-api.

Pydantic lives ONLY at the HTTP boundary (this package).
sqlviz-storage and sqlviz-inference use plain dataclasses — DOC3 Section 8.
"""

from __future__ import annotations

from pydantic import BaseModel

# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


# ── Shares ───────────────────────────────────────────────────────────────────

class ShareCreate(BaseModel):
    mode: str  # "private" | "password" | "public"
    password: str | None = None


class ShareCreateResponse(BaseModel):
    id: str
    dashboard_id: str
    token: str
    mode: str
    created_at: str


class ShareRevokeRequest(BaseModel):
    revoked: bool


class UnlockRequest(BaseModel):
    password: str


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardCreate(BaseModel):
    name: str
    folder_id: str | None = None
    connection_id: str | None = None
    sort_order: int = 0


class DashboardUpdate(BaseModel):
    name: str | None = None
    folder_id: str | None = None
    connection_id: str | None = None
    sort_order: int | None = None


class DashboardResponse(BaseModel):
    id: str
    name: str
    folder_id: str | None
    connection_id: str | None
    sort_order: int
    created_at: str
    updated_at: str
    dashboard_hint: str | None = None
    dashboard_domain: str | None = None


# ── Folder ───────────────────────────────────────────────────────────────────

class FolderCreate(BaseModel):
    name: str
    parent_id: str | None = None
    sort_order: int = 0


class FolderUpdate(BaseModel):
    name: str | None = None
    parent_id: str | None = None
    sort_order: int | None = None


class FolderResponse(BaseModel):
    id: str
    name: str
    parent_id: str | None
    sort_order: int
    created_at: str


# ── Panel ─────────────────────────────────────────────────────────────────────

class PanelCreate(BaseModel):
    dashboard_id: str
    name: str
    sql_content: str = ""
    sort_order: int = 0


class PanelUpdate(BaseModel):
    name: str | None = None
    sql_content: str | None = None
    sort_order: int | None = None


class PanelResponse(BaseModel):
    id: str
    dashboard_id: str
    name: str
    sql_content: str
    sort_order: int
    created_at: str
    updated_at: str
    # V0.2 Fase E — override fields (None when panel has never been executed)
    fingerprint: str | None = None
    inferred_chart_type: str | None = None
    selected_chart_type: str | None = None
    chart_user_override: str | None = None
    inferred_col_span: int | None = None
    selected_col_span: int | None = None
    col_span_user_override: int | None = None
    inferred_height_px: int | None = None
    selected_height_px: int | None = None
    height_user_override: int | None = None


class PanelOverrideRequest(BaseModel):
    field_name: str   # "chart_type" | "col_span" | "height_px"
    user_value: str   # always passed as string; OverrideSystem casts as needed
