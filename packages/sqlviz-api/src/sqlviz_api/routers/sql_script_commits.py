"""Author-only script snapshots and atomic definition commits."""

from typing import Annotated

from fastapi import APIRouter, Path
from sqlviz_storage.sql_script_repository import SqlScriptSnapshot

from sqlviz_api.dependencies import SqlAuthoringDep
from sqlviz_api.sql_commit_contract import (
    CreatedSqlPanelResponse,
    SqlCommitRequest,
    SqlCommitResponse,
    SqlPublicationResponse,
    SqlScriptBindingResponse,
    SqlScriptPanelResponse,
    SqlSnapshotResponse,
)
from sqlviz_api.sql_identity_adapter import identity_decisions

router = APIRouter(
    prefix="/api/v1/dashboards/{dashboard_id}/sql-script",
    tags=["sql"],
    responses={
        401: {"description": "Author session required"},
        403: {"description": "Author access required; share credentials cannot write"},
        404: {"description": "Dashboard not found"},
        413: {"description": "Request or stored script state exceeds supported limits"},
        500: {"description": "Invalid stored associations or unexpected server error"},
    },
)
DashboardId = Annotated[str, Path(min_length=1, max_length=256)]


def _snapshot_response(snapshot: SqlScriptSnapshot) -> SqlSnapshotResponse:
    publication = snapshot.publication
    return SqlSnapshotResponse(
        dashboard_id=snapshot.dashboard_id,
        revision=snapshot.revision,
        draft_source=snapshot.draft_source,
        panels=[
            SqlScriptPanelResponse(
                id=panel.id,
                name=panel.name,
                sql_content=panel.sql_content,
                sort_order=panel.sort_order,
            )
            for panel in sorted(
                snapshot.panels, key=lambda panel: (panel.sort_order, panel.created_at, panel.id)
            )
        ],
        publication=SqlPublicationResponse(
            revision=publication.revision,
            source=publication.source,
            bindings=[
                SqlScriptBindingResponse(
                    statement_index=index,
                    panel_id=binding.panel_id,
                    start_offset=binding.start_offset,
                    end_offset=binding.end_offset,
                )
                for index, binding in enumerate(publication.bindings)
            ],
        )
        if publication is not None
        else None,
    )


@router.get("", response_model=SqlSnapshotResponse)
def read_script_snapshot(
    dashboard_id: DashboardId, authoring: SqlAuthoringDep
) -> SqlSnapshotResponse:
    return _snapshot_response(authoring.read(dashboard_id))


@router.post(
    "/commit",
    response_model=SqlCommitResponse,
    responses={
        403: {"description": "Author access required or SQL violates the analytical read policy"},
        409: {"description": "Stale state or transaction conflict; refresh and review decisions"},
        422: {"description": "Invalid contract, SQL syntax or unresolved identity decisions"},
        429: {"description": "Native SQL analysis is busy; retry shortly"},
    },
)
def commit_script(
    dashboard_id: DashboardId, body: SqlCommitRequest, authoring: SqlAuthoringDep
) -> SqlCommitResponse:
    committed = authoring.commit(
        dashboard_id, body.expected_revision, body.sql, identity_decisions(body.decisions)
    )
    return SqlCommitResponse(
        snapshot=_snapshot_response(committed.snapshot),
        created_panels=[
            CreatedSqlPanelResponse(creation_key=key, panel_id=panel_id)
            for key, panel_id in committed.created_panels
        ],
    )
