"""Author-only, read-only SQL analysis, independent of project connections."""

from dataclasses import asdict

from fastapi import APIRouter

from sqlviz_api.dependencies import SqlScriptsDep
from sqlviz_api.sql_script_contract import (
    SqlScriptParseRequest,
    SqlScriptParseResponse,
    SqlStatementResponse,
)

router = APIRouter(prefix="/api/v1/sql", tags=["sql"])


@router.post("/parse", response_model=SqlScriptParseResponse)
def parse_sql_script(body: SqlScriptParseRequest, scripts: SqlScriptsDep) -> SqlScriptParseResponse:
    return SqlScriptParseResponse(statements=[
        SqlStatementResponse(**asdict(statement)) for statement in scripts.parse(body.sql)
    ])
