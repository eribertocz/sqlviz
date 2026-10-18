"""HTTP contracts for analysis; SQL engine types never cross the boundary."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field
from sqlviz_core.models.sql_script import MAX_SQL_SCRIPT_BYTES


class SqlScriptParseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    sql: str = Field(max_length=MAX_SQL_SCRIPT_BYTES)


class SqlStatementResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    sql: str
    start_offset: int = Field(ge=0)
    end_offset: int = Field(ge=0)


class SqlScriptParseResponse(BaseModel):
    version: Literal[1] = 1
    dialect: Literal["duckdb"] = "duckdb"
    statements: list[SqlStatementResponse]


PanelRef = Annotated[str, Field(min_length=1, max_length=256)]


class KeepSqlIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    kind: Literal["keep"]
    statement_index: int = Field(ge=0, le=255)
    panel_id: PanelRef


class CreateSqlIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    kind: Literal["create"]
    statement_index: int = Field(ge=0, le=255)
    creation_key: PanelRef


class RemoveSqlIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    kind: Literal["remove"]
    panel_id: PanelRef


SqlIdentityChoice = Annotated[
    KeepSqlIdentity | CreateSqlIdentity | RemoveSqlIdentity,
    Field(discriminator="kind"),
]


class SqlReconcileRequest(SqlScriptParseRequest):
    dashboard_id: PanelRef | None = None
    expected_panel_ids: list[PanelRef] = Field(max_length=256)
    decisions: list[SqlIdentityChoice] = Field(max_length=512)


class SqlReconciledStatement(SqlStatementResponse):
    statement_index: int
    kind: Literal["keep", "create"]
    panel_id: str | None = None
    creation_key: str | None = None


class SqlReconcileResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    version: Literal[1] = 1
    source: str
    complete: bool
    statements: list[SqlReconciledStatement]
    removed_panel_ids: list[str]
    unresolved_statement_indexes: list[int]
    unresolved_panel_ids: list[str]
