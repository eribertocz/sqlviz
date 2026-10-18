"""Strict authoring transport; revision tokens are expected state, not credentials."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from sqlviz_api.sql_execution_contract import DefinitionRevision
from sqlviz_api.sql_script_contract import PanelRef, SqlIdentityChoice, SqlScriptParseRequest

ScriptRevision = Annotated[
    str, Field(pattern=r"^sql-script-v1:[0-9a-f]{64}$", min_length=78, max_length=78)
]


class SqlCommitRequest(SqlScriptParseRequest):
    expected_revision: ScriptRevision
    decisions: list[SqlIdentityChoice] = Field(max_length=512)


class SqlScriptPanelResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    id: str
    name: str
    sql_content: str
    sort_order: int


class SqlScriptBindingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    statement_index: int = Field(ge=0, le=255)
    panel_id: PanelRef
    start_offset: int = Field(ge=0)
    end_offset: int = Field(ge=1)


class SqlPublicationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    version: Literal[1] = 1
    revision: int = Field(ge=1, le=2**63 - 1)
    source: str
    bindings: list[SqlScriptBindingResponse] = Field(max_length=256)


class SqlSnapshotResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    version: Literal[1] = 1
    dashboard_id: str
    revision: ScriptRevision
    definition_revision: DefinitionRevision | None
    draft_source: str
    panels: list[SqlScriptPanelResponse] = Field(max_length=256)
    publication: SqlPublicationResponse | None
    publication_status: Literal["absent", "confirmed", "incompatible"]
    last_run_at: str | None
    last_run_sql: str | None


class CreatedSqlPanelResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    creation_key: PanelRef
    panel_id: PanelRef


class SqlCommitResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    version: Literal[1] = 1
    snapshot: SqlSnapshotResponse
    created_panels: list[CreatedSqlPanelResponse] = Field(max_length=256)
