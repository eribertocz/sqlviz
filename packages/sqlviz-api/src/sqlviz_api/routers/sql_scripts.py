"""Author-only analysis: independent parsing and read-only project reconciliation."""

from dataclasses import asdict

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from sqlviz_core.models.sql_reconciliation import (
    CreateSqlPanel,
    ExistingSqlPanel,
    KeepSqlPanel,
    RemoveSqlPanel,
    SqlIdentityDecision,
    SqlPanelUpdate,
    SqlReconciliationError,
    reconcile_sql_script,
)
from sqlviz_storage.dashboard_repository import DashboardRepository
from sqlviz_storage.panel_repository import PanelRepository
from sqlviz_storage.transactions import project_transaction

from sqlviz_api.dependencies import DbDep, SqlScriptsDep
from sqlviz_api.sql_script_contract import (
    CreateSqlIdentity,
    KeepSqlIdentity,
    SqlReconciledStatement,
    SqlReconcileRequest,
    SqlReconcileResponse,
    SqlScriptParseRequest,
    SqlScriptParseResponse,
    SqlStatementResponse,
)

router = APIRouter(prefix="/api/v1/sql", tags=["sql"])


@router.post("/parse", response_model=SqlScriptParseResponse)
def parse_sql_script(body: SqlScriptParseRequest, scripts: SqlScriptsDep) -> SqlScriptParseResponse:
    return SqlScriptParseResponse(
        statements=[
            SqlStatementResponse(**asdict(statement)) for statement in scripts.parse(body.sql)
        ]
    )


@router.post("/reconcile", response_model=SqlReconcileResponse)
def preview_sql_reconciliation(
    body: SqlReconcileRequest,
    scripts: SqlScriptsDep,
    db: DbDep,
) -> SqlReconcileResponse | JSONResponse:
    """Read-only preflight; a complete proposal is not a write or concurrency lease."""
    statements = scripts.parse(body.sql)
    with project_transaction(db):
        if body.dashboard_id is not None:
            DashboardRepository(db).get(body.dashboard_id)
            panels = PanelRepository(db).list(body.dashboard_id)
        else:
            panels = []
        actual_ids = {panel.id for panel in panels}
        if len(set(body.expected_panel_ids)) != len(body.expected_panel_ids) or actual_ids != set(
            body.expected_panel_ids
        ):
            raise HTTPException(409, "Panel snapshot changed. Reload the dashboard and retry.")
        previous = tuple(ExistingSqlPanel(panel.id, panel.sql_content) for panel in panels)
    decisions: list[SqlIdentityDecision] = []
    for choice in body.decisions:
        if isinstance(choice, KeepSqlIdentity):
            decisions.append(KeepSqlPanel(choice.statement_index, choice.panel_id))
        elif isinstance(choice, CreateSqlIdentity):
            decisions.append(CreateSqlPanel(choice.statement_index, choice.creation_key))
        else:
            decisions.append(RemoveSqlPanel(choice.panel_id))
    try:
        plan = reconcile_sql_script(body.sql, statements, previous, decisions)
    except SqlReconciliationError as exc:
        return JSONResponse(status_code=422, content={"code": exc.code, "detail": exc.detail})
    resolved: list[SqlReconciledStatement] = []
    for item in plan.statements:
        resolved.append(
            SqlReconciledStatement(
                **asdict(item.statement),
                statement_index=item.statement_index,
                kind="keep" if isinstance(item, SqlPanelUpdate) else "create",
                panel_id=item.panel_id if isinstance(item, SqlPanelUpdate) else None,
                creation_key=None if isinstance(item, SqlPanelUpdate) else item.creation_key,
            )
        )
    return SqlReconcileResponse(
        source=plan.source,
        complete=plan.complete,
        statements=resolved,
        removed_panel_ids=list(plan.removed_panel_ids),
        unresolved_statement_indexes=list(plan.unresolved_statement_indexes),
        unresolved_panel_ids=list(plan.unresolved_panel_ids),
    )
