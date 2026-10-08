"""Pydantic request/response models for sqlviz-api.

Pydantic lives ONLY at the HTTP boundary (this package).
sqlviz-storage and sqlviz-inference use plain dataclasses — DOC3 Section 8.
"""

from __future__ import annotations

from typing import Literal, Self, cast

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlviz_core.models.dashboards import (
    MAX_DASHBOARD_DESCRIPTION_LENGTH,
    MAX_DASHBOARD_ID_LENGTH,
    MAX_DASHBOARD_NAME_LENGTH,
    DashboardChanges,
    normalize_dashboard_changes,
)
from sqlviz_core.models.panel_overrides import validate_override
from sqlviz_core.models.panels import MAX_PANEL_NAME_LENGTH, PanelChanges, validate_panel_changes

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
    folder_id: str | None = Field(default=None, strict=True)
    connection_id: str | None = None
    sort_order: int = 0
    description: str | None = None


class DashboardUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    name: str | None = Field(default=None, min_length=1, max_length=MAX_DASHBOARD_NAME_LENGTH)
    folder_id: str | None = Field(default=None, max_length=MAX_DASHBOARD_ID_LENGTH)
    connection_id: str | None = Field(default=None, max_length=MAX_DASHBOARD_ID_LENGTH)
    sort_order: int | None = Field(default=None, ge=-(2**31), le=2**31 - 1)
    description: str | None = Field(default=None, max_length=MAX_DASHBOARD_DESCRIPTION_LENGTH)
    sql_content: str | None = None   # Draft editor text (auto-saved).
    last_run_at: str | None = None   # ISO timestamp of the last successful run.
    last_run_sql: str | None = None  # Exact SQL of the last successful run.
    # Omission preserves placement; null (or legacy "") moves to root.

    def changes(self) -> DashboardChanges:
        return normalize_dashboard_changes(
            cast(DashboardChanges, self.model_dump(exclude_unset=True)),
        )

    @model_validator(mode="after")
    def validate_changes(self) -> Self:
        self.changes()
        return self


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
    description: str | None = None
    sql_content: str = ""
    last_run_at: str | None = None
    last_run_sql: str | None = None


# ── Folder ───────────────────────────────────────────────────────────────────

class FolderCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    name: str = Field(min_length=1)
    parent_id: str | None = None
    sort_order: int = Field(default=0, ge=-(2**31), le=2**31 - 1)


class FolderUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    name: str | None = Field(default=None, min_length=1)
    parent_id: str | None = None
    sort_order: int | None = Field(default=None, ge=-(2**31), le=2**31 - 1)

    @model_validator(mode="after")
    def reject_null_required_fields(self) -> Self:
        for field in ("name", "sort_order"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} must not be null")
        return self


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
    model_config = ConfigDict(extra="forbid", strict=True)
    name: str | None = Field(default=None, min_length=1, max_length=MAX_PANEL_NAME_LENGTH)
    sql_content: str | None = None
    sort_order: int | None = Field(default=None, ge=-(2**31), le=2**31 - 1)

    def changes(self) -> PanelChanges:
        changes = cast(PanelChanges, self.model_dump(exclude_unset=True))
        validate_panel_changes(changes)
        return changes

    @model_validator(mode="after")
    def validate_changes(self) -> Self:
        self.changes()
        return self


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
    model_config = ConfigDict(extra="forbid", strict=True)
    field_name: Literal["chart_type", "col_span", "height_px"]
    # Always passed as a string; OverrideSystem casts as needed.
    # None clears the override ("reset to auto") — the field goes back to
    # following inference instead of being frozen at today's inferred value.
    user_value: str | None

    @model_validator(mode="after")
    def validate_value(self) -> Self:
        validate_override(self.field_name, self.user_value)
        return self


class PanelViewOverrideRequest(BaseModel):
    field: str            # "title" | "x_label" | "y_label"
    value: str | None = None   # "" / None clears the override


class ExecuteBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    # Keep raw JSON primitives intact; ParameterService enforces the shared
    # typed contract without Pydantic coercion or renderer-specific heuristics.
    variables: dict[str, object] = Field(default_factory=dict)


class FilterDomainBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    column: str = Field(min_length=1, max_length=128)
    kind: Literal["distinct", "range"]
