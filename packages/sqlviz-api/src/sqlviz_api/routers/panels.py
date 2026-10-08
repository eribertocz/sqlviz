"""Panel CRUD — /api/v1/panels.

A panel belongs to exactly one dashboard and carries the SQL content
that will be executed and inferred in Phase 4.2.

Creating a panel with a non-existent dashboard_id returns 404:
the dashboard is a resource that must exist before panels can belong to it.
"""

from __future__ import annotations

import dataclasses
import uuid
from datetime import datetime, timezone
from typing import Any

import duckdb
import sqlviz_inference
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlviz_core.models import ColumnSchema
from sqlviz_core.models.panels import Panel
from sqlviz_inference.dashboard.dashboard_classifier import classify_dashboard
from sqlviz_inference.filters.domain import build_domain_query
from sqlviz_inference.filters.parameters import filter_parameter_names
from sqlviz_storage.brain_db import get_brain_connection
from sqlviz_storage.dashboard_repository import dashboard_write
from sqlviz_storage.override_system import (
    apply_layout_overrides,
    apply_override,
    clear_override,
    store_inference,
)
from sqlviz_storage.panel_repository import PanelRepository
from sqlviz_storage.panel_view_overrides import (
    apply_view_overrides,
    get_view_overrides,
    set_view_override,
)

from sqlviz_api.dependencies import DbDep, ParametersDep, QueriesDep
from sqlviz_api.models import (
    ExecuteBody,
    FilterDomainBody,
    PanelCreate,
    PanelOverrideRequest,
    PanelResponse,
    PanelUpdate,
    PanelViewOverrideRequest,
)
from sqlviz_api.security import (
    AdminDep,
    ReaderDep,
    require_dashboard_access,
    require_panel_access,
    require_reader,
)
from sqlviz_api.serialization import json_safe
from sqlviz_api.services.access import AccessDenied
from sqlviz_api.services.parameters import FilterPlan
from sqlviz_api.services.query_policy import validate_viewer_query

router = APIRouter(
    prefix="/api/v1/panels", tags=["panels"], dependencies=[Depends(require_reader)],
)


def _require_viewer_query(sql: str) -> None:
    """Statement policy only; analytical engine isolation is separate work."""
    try:
        validate_viewer_query(sql)
    except AccessDenied as exc:
        raise HTTPException(exc.status_code, exc.detail) from None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _to_response(panel: Panel) -> PanelResponse:
    return PanelResponse(**dataclasses.asdict(panel))


def _require_dashboard(db: DbDep, dashboard_id: str) -> None:
    row = db.execute(
        "SELECT id FROM dashboards WHERE id = ?", [dashboard_id]
    ).fetchone()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Dashboard '{dashboard_id}' not found",
        )


def _fetch_one(db: DbDep, panel_id: str) -> PanelResponse:
    return _to_response(PanelRepository(db).get(panel_id))


@router.get("", response_model=list[PanelResponse])
def list_panels(
    db: DbDep,
    principal: ReaderDep,
    dashboard_id: str | None = Query(default=None),
) -> list[PanelResponse]:
    """List panels, optionally filtered by dashboard_id."""
    if not principal.is_admin:
        if dashboard_id is None:
            raise HTTPException(403, "Viewer requests require a dashboard_id")
        require_dashboard_access(principal, dashboard_id)
        _require_dashboard(db, dashboard_id)
    return [_to_response(panel) for panel in PanelRepository(db).list(dashboard_id)]


@router.post("", response_model=PanelResponse, status_code=201)
def create_panel(body: PanelCreate, db: DbDep, _admin: AdminDep) -> PanelResponse:
    panel_id = str(uuid.uuid4())
    now = _now()
    with dashboard_write(db, body.dashboard_id):
        db.execute(
            "INSERT INTO panels "
            "(id, dashboard_id, name, sql_content, sort_order, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            [panel_id, body.dashboard_id, body.name, body.sql_content, body.sort_order, now, now],
        )
    return PanelResponse(
        id=panel_id,
        dashboard_id=body.dashboard_id,
        name=body.name,
        sql_content=body.sql_content,
        sort_order=body.sort_order,
        created_at=now,
        updated_at=now,
    )


@router.get("/{panel_id}", response_model=PanelResponse)
def get_panel(panel_id: str, db: DbDep, principal: ReaderDep) -> PanelResponse:
    require_panel_access(db, principal, panel_id)
    return _fetch_one(db, panel_id)


@router.patch("/{panel_id}", response_model=PanelResponse)
def update_panel(panel_id: str, body: PanelUpdate, db: DbDep, _admin: AdminDep) -> PanelResponse:
    return _to_response(PanelRepository(db).update(panel_id, body.changes()))


@router.delete("/{panel_id}", status_code=204)
def delete_panel(panel_id: str, db: DbDep, _admin: AdminDep) -> None:
    PanelRepository(db).delete(panel_id)


def _update_dashboard_classification(
    db: DbDep,
    panel_id: str,
    col_names: list[str],
) -> None:
    """Classify the parent dashboard from all its executed panels.

    Runs after every successful panel execution so the sidebar icon stays
    current.  Errors are swallowed — classification is best-effort.
    """
    try:
        row = db.execute(
            "SELECT dashboard_id FROM panels WHERE id = ?", [panel_id]
        ).fetchone()
        if not row:
            return
        dashboard_id: str = row[0]

        # Collect intent_winner for all panels that have been executed.
        panel_rows = db.execute(
            "SELECT inferred_intent_type, sql_content "
            "FROM panels WHERE dashboard_id = ? AND inferred_intent_type IS NOT NULL",
            [dashboard_id],
        ).fetchall()

        panel_intents = [r[0] for r in panel_rows]
        all_sql = " ".join(r[1] or "" for r in panel_rows)

        if not panel_intents:
            return

        classification = classify_dashboard(panel_intents, col_names, all_sql)
        db.execute(
            "UPDATE dashboards "
            "SET dashboard_hint = ?, dashboard_domain = ?, updated_at = ? "
            "WHERE id = ?",
            [classification.hint, classification.domain, _now(), dashboard_id],
        )
    except Exception:
        pass  # classification is non-critical; never block the execute response


def _render_contract(
    db: DbDep,
    panel: PanelResponse,
    result: Any,
) -> dict[str, Any]:
    """Overlay every persisted user override onto an inference_result dict.

    One place, because the layout is composed from this dict alone — the admin
    app and a shared link both render whatever it says. Any return path that
    skips it silently reverts the panel to inferred values.
    """
    return apply_layout_overrides(
        apply_view_overrides(result.to_dict(), get_view_overrides(db, panel.id)),
        panel.col_span_user_override,
        panel.height_user_override,
    )


def _inference_only_response(
    sql: str,
    db: DbDep,
    brain: Any,
    debug: bool,
    panel: PanelResponse,
    queries: QueriesDep,
) -> JSONResponse:
    """Render the filter bar without data when the query can't be executed.

    Reached only when "All"/no values cannot be neutralized (SQL sqlglot can't
    parse, or a $variable outside a boolean predicate). Probes the query with
    every $variable bound to NULL to recover real column types — without this,
    FilterEngine sees no schema, so every $variable defaults to VARCHAR and
    numeric/date columns render as plain text controls (and range pairs never
    merge). The probe binds NULL in the isolated analytical catalog and uses
    LIMIT 0: a NULL predicate alone would not guarantee an empty result.
    """
    schema: list[ColumnSchema] = []
    try:
        probe_vars = dict.fromkeys(filter_parameter_names(sql))
        probe = queries.execute(db, sql, probe_vars, schema_only=True)
        schema = [ColumnSchema(name=name, type=kind) for name, kind in probe.columns]
    except duckdb.Error:
        pass  # fall back to schema-less inference — no worse than before

    result = sqlviz_inference.infer(sql, schema=schema, brain_conn=brain, debug=debug)
    result = dataclasses.replace(
        result,
        fallback_applied=True,
        fallback_reason="Set filter values to see data",
    )
    return JSONResponse(content={
        "inference_result": _render_contract(db, panel, result),
        "data": [],
    })


@router.post("/{panel_id}/execute")
def execute_panel(
    panel_id: str,
    db: DbDep,
    principal: ReaderDep,
    queries: QueriesDep,
    parameters: ParametersDep,
    body: ExecuteBody | None = Body(default=None),
    debug: bool = Query(default=False),
) -> JSONResponse:
    """Execute a panel's SQL and return {inference_result, data}.

    Accepts an optional body with {variables: {name: value}} for $variable
    substitution (filter controls, Phase 5.7).

    Empty/absent variables mean "All": their predicate is neutralized (see
    neutralize_filters) so the query returns every row for that dimension. A
    panel with $variables and no values therefore renders real data on the very
    first Run, and picking a dropdown's "All" option shows the unfiltered data.

    Query that can't be neutralized (unparseable, or a $variable used outside a
    boolean predicate) → 200 with fallback_applied=True + empty data, so the
    filter bar still renders.
    SQL syntax error → 200 with fallback_applied=True + empty data.
    Missing table (CatalogException) → 422. Panel not found → 404.
    """
    require_panel_access(db, principal, panel_id)
    panel = _fetch_one(db, panel_id)
    sql = panel.sql_content
    raw_vars: dict[str, Any] = body.variables if body else {}

    # Validate the saved SQL before filter rewriting can discard a statement.
    # Invalid author syntax keeps the existing inference fallback downstream.
    try:
        plan = parameters.prepare(sql, raw_vars, queries)
    except duckdb.ParserException:
        plan = FilterPlan(sql, {}, (), False)
    if not principal.is_admin:
        _require_viewer_query(sql)
        debug = False
    brain = get_brain_connection() if principal.is_admin else None

    # "All" semantics: a filter whose value is empty (None / "" / []) — or one
    # the client never sent — must not filter. We neutralize its predicate so
    # the panel returns every row for that dimension. This is what lets both the
    # dropdown "All" option and the very first Run (no values chosen yet) render
    # real data instead of an empty chart.
    # "Reveal" case: the panel has $variables but the user has chosen no value
    # for any of them (first Run, or every filter on "All"). Here the query is
    # a means to reveal the filter bar, so a query that cannot execute (missing
    # table, etc.) must still return the controls — never a hard 422.
    is_reveal = plan.reveal
    if plan.sql is None:
        # A variable outside a predicate cannot safely mean All. Render its
        # controls without data until a concrete value is supplied.
        return _inference_only_response(sql, db, brain, debug, panel, queries)

    try:
        execution = queries.execute(
            db, plan.sql, plan.bindings,
        )
    except duckdb.ParserException:
        result = sqlviz_inference.infer(sql, brain_conn=brain, debug=debug)
        result = dataclasses.replace(
            result,
            fallback_applied=True,
            fallback_reason="SQL syntax error — query could not be parsed",
        )
        return JSONResponse(content={
            "inference_result": _render_contract(db, panel, result),
            "data": [],
        })
    except duckdb.Error as exc:
        # First Run / all-"All": reveal the filter bar instead of failing hard.
        if is_reveal:
            return _inference_only_response(sql, db, brain, debug, panel, queries)
        if plan.bindings:
            raise HTTPException(
                status_code=422, detail="SQL could not execute with these filter values"
            ) from None
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    desc = execution.columns
    col_names = [d[0] for d in desc]
    rows_raw = execution.rows

    data: list[dict[str, object]] = [
        {k: json_safe(v) for k, v in zip(col_names, row)}
        for row in rows_raw
    ]
    schema = [ColumnSchema(name=str(d[0]), type=str(d[1])) for d in desc]

    result = sqlviz_inference.infer(
        sql, data=data, schema=schema, brain_conn=brain,
        chart_override=panel.chart_user_override,
        debug=debug,
    )

    # Persist inferred values to panels table (never overwrites existing overrides)
    if principal.is_admin:
        store_inference(
            db,
            panel_id=panel_id,
            fingerprint=result.fingerprint,
            chart_type=result.chart_winner,
            col_span=result.col_span,
            height_px=result.panel_height_px,
            intent_type=result.intent_winner,
        )
        _update_dashboard_classification(db, panel_id, col_names)

    return JSONResponse(content={
        "inference_result": _render_contract(db, panel, result),
        "data": data,
    })


@router.post("/{panel_id}/filter-domain")
def filter_domain(
    panel_id: str,
    body: FilterDomainBody,
    db: DbDep,
    principal: ReaderDep,
    queries: QueriesDep,
) -> JSONResponse:
    """Return the domain of a filter column so the UI can render a rich control.

    kind="distinct" → {"values": [...]}  (dropdown / multiselect / checkboxes)
    kind="range"    → {"min": lo, "max": hi}  (slider bounds)

    Best-effort: any failure to parse/execute returns an empty domain, and the
    frontend falls back to a plain text/number input. Never raises 5xx for a
    query it simply cannot introspect.
    """
    require_panel_access(db, principal, panel_id)
    panel = _fetch_one(db, panel_id)
    if not principal.is_admin:
        _require_viewer_query(panel.sql_content)
    empty: dict[str, Any] = (
        {"values": []} if body.kind == "distinct" else {"min": None, "max": None}
    )

    query = build_domain_query(panel.sql_content, body.column, body.kind)
    if query is None:
        return JSONResponse(content=empty)

    try:
        rows = queries.execute(db, query).rows
    except duckdb.Error:
        return JSONResponse(content=empty)

    if body.kind == "distinct":
        return JSONResponse(
            content={"values": [json_safe(r[0]) for r in rows]}
        )

    if not rows or rows[0][0] is None:
        return JSONResponse(content={"min": None, "max": None})
    lo, hi = rows[0]
    return JSONResponse(content={"min": json_safe(lo), "max": json_safe(hi)})


@router.patch("/{panel_id}/override", response_model=PanelResponse)
def override_panel(
    panel_id: str,
    body: PanelOverrideRequest,
    db: DbDep,
    _admin: AdminDep,
) -> PanelResponse:
    """Apply a user correction to a panel's inferred field.

    Writes selected_* and *_user_override in the .sqlviz file.
    Persists the pattern to brain.duckdb so future executions of the
    same SQL fingerprint return the user-preferred value.

    field_name: "chart_type" | "col_span" | "height_px"
    user_value: the corrected value (always a string; cast in OverrideSystem),
                or null to clear the override and follow inference again.

    Returns the updated PanelResponse.
    """
    _fetch_one(db, panel_id)  # raises 404 if missing
    try:
        if body.user_value is None:
            clear_override(db, panel_id, body.field_name)
        else:
            apply_override(db, get_brain_connection, panel_id, body.field_name, body.user_value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (duckdb.TransactionException, duckdb.ConstraintException):
        raise HTTPException(
            status_code=409, detail="Panel changed concurrently; reload and try again",
        ) from None
    return _fetch_one(db, panel_id)


@router.patch("/{panel_id}/view-override", status_code=200)
def set_panel_view_override(
    panel_id: str,
    body: PanelViewOverrideRequest,
    db: DbDep,
    _admin: AdminDep,
) -> dict[str, str]:
    """Set a presentation override (panel title / axis label) on a panel.

    Persisted on the panel and overlaid onto the render contract by execute,
    so it shows in the admin app AND in shared viewers. field:
    "title" | "x_label" | "y_label"; value "" clears it.
    """
    _fetch_one(db, panel_id)  # raises 404 if missing
    try:
        set_view_override(db, panel_id, body.field, body.value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"status": "ok"}
