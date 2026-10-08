"""HTTP contracts for analysis; SQL engine types never cross the boundary."""

from __future__ import annotations

from typing import Literal

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
