"""Panel CRUD — /api/v1/panels.

A panel belongs to exactly one dashboard and carries the SQL content
that will be executed and inferred in Phase 4.2.

Creating a panel with a non-existent dashboard_id returns 404:
the dashboard is a resource that must exist before panels can belong to it.
"""

from __future__ import annotations

import dataclasses
import re
import uuid
from datetime import datetime, timezone
from typing import Any

import duckdb
import sqlviz_inference
from fastapi import APIRouter, Body, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlviz_core.models import ColumnSchema
from sqlviz_inference.dashboard.dashboard_classifier import classify_dashboard
from sqlviz_inference.filters.domain import build_domain_query
from sqlviz_inference.filters.neutralize import neutralize_filters
from sqlviz_storage.brain_db import get_brain_connection
from sqlviz_storage.override_system import apply_override, store_inference

from sqlviz_api.dependencies import DbDep
from sqlviz_api.models import (
    PanelCreate,
    PanelOverrideRequest,
    PanelResponse,
    PanelUpdate,
)
from sqlviz_api.serialization import json_safe

_VARIABLE_RE = re.compile(r"\$(\w+)")


def _is_empty_filter_value(value: Any) -> bool:
    """True when a filter value means "All" (no filtering on this dimension).

    "All" is represented by an empty value: None, the empty string (what the
    dropdown/date/search controls emit for their "All" option), or an empty
    list (a multiselect with nothing picked). Note that ``0`` and ``False`` are
    NOT empty — they are legitimate numeric/toggle selections that must filter.
    """
    if value is None:
        return True
    if isinstance(value, str):
        return value == ""
    if isinstance(value, (list, tuple)):
        return len(value) == 0
    return False


def _rewrite_in_clauses_for_lists(sql: str, variables: dict[str, Any]) -> str:
    """Rewrite `col IN ($var)` to `col IN $var` for every list-valued variable.

    DuckDB binds a list parameter as a single array value, so `IN ($var)`
    (parens around the placeholder) raises a Conversion Error trying to cast
    the array to the column's scalar type — the parens make DuckDB treat it
    as a one-element scalar list rather than an array to test membership
    against. `IN $var` (no parens) is the form DuckDB accepts for array
    parameters, so multiselect filters (list-valued $var) need the rewrite;
    scalar variables are left untouched since `IN ($var)` never appears for
    them from the FilterEngine-generated controls.
    """
    for name, value in variables.items():
        if isinstance(value, list):
            sql = re.sub(
                r"\bIN\s*\(\s*\$" + re.escape(name) + r"\s*\)",
                f"IN ${name}",
                sql,
                flags=re.IGNORECASE,
            )
    return sql


class ExecuteBody(BaseModel):
    variables: dict[str, Any] = Field(default_factory=dict)


class FilterDomainBody(BaseModel):
    column: str
    kind: str  # "distinct" | "range"

router = APIRouter(prefix="/api/v1/panels", tags=["panels"])

_SELECT = (
    "SELECT id, dashboard_id, name, sql_content, sort_order, created_at, updated_at,"
    " fingerprint,"
    " inferred_chart_type, selected_chart_type, chart_user_override,"
    " inferred_col_span,   selected_col_span,   col_span_user_override,"
    " inferred_height_px,  selected_height_px,  height_user_override "
    "FROM panels"
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")



def _row_to_response(row: tuple[Any, ...]) -> PanelResponse:
    return PanelResponse(
        id=row[0],
        dashboard_id=row[1],
        name=row[2],
        sql_content=row[3],
        sort_order=row[4],
        created_at=row[5],
        updated_at=row[6],
        fingerprint=row[7],
        inferred_chart_type=row[8],
        selected_chart_type=row[9],
        chart_user_override=row[10],
        inferred_col_span=row[11],
        selected_col_span=row[12],
        col_span_user_override=row[13],
        inferred_height_px=row[14],
        selected_height_px=row[15],
        height_user_override=row[16],
    )


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
    row = db.execute(
        f"{_SELECT} WHERE id = ?", [panel_id]
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Panel '{panel_id}' not found")
    return _row_to_response(row)


@router.get("", response_model=list[PanelResponse])
def list_panels(
    db: DbDep,
    dashboard_id: str | None = Query(default=None),
) -> list[PanelResponse]:
    """List panels, optionally filtered by dashboard_id."""
    if dashboard_id is not None:
        rows = db.execute(
            f"{_SELECT} WHERE dashboard_id = ? ORDER BY sort_order, created_at",
            [dashboard_id],
        ).fetchall()
    else:
        rows = db.execute(
            f"{_SELECT} ORDER BY sort_order, created_at"
        ).fetchall()
    return [_row_to_response(r) for r in rows]


@router.post("", response_model=PanelResponse, status_code=201)
def create_panel(body: PanelCreate, db: DbDep) -> PanelResponse:
    _require_dashboard(db, body.dashboard_id)

    panel_id = str(uuid.uuid4())
    now = _now()
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
def get_panel(panel_id: str, db: DbDep) -> PanelResponse:
    return _fetch_one(db, panel_id)


@router.patch("/{panel_id}", response_model=PanelResponse)
def update_panel(panel_id: str, body: PanelUpdate, db: DbDep) -> PanelResponse:
    _fetch_one(db, panel_id)  # raises 404 if missing

    updates: dict[str, str | int] = {}
    if body.name is not None:
        updates["name"] = body.name
    if body.sql_content is not None:
        updates["sql_content"] = body.sql_content
    if body.sort_order is not None:
        updates["sort_order"] = body.sort_order
    updates["updated_at"] = _now()

    set_clause = ", ".join(f"{col} = ?" for col in updates)
    db.execute(
        f"UPDATE panels SET {set_clause} WHERE id = ?",
        [*updates.values(), panel_id],
    )
    return _fetch_one(db, panel_id)


@router.delete("/{panel_id}", status_code=204)
def delete_panel(panel_id: str, db: DbDep) -> None:
    _fetch_one(db, panel_id)  # raises 404 if missing
    db.execute("DELETE FROM panels WHERE id = ?", [panel_id])


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


def _inference_only_response(
    sql: str,
    db: DbDep,
    brain: Any,
    debug: bool,
) -> JSONResponse:
    """Render the filter bar without data when the query can't be executed.

    Reached only when "All"/no values cannot be neutralized (SQL sqlglot can't
    parse, or a $variable outside a boolean predicate). Probes the query with
    every $variable bound to NULL to recover real column types — without this,
    FilterEngine sees no schema, so every $variable defaults to VARCHAR and
    numeric/date columns render as plain text controls (and range pairs never
    merge). NULL-bound execution is safe: comparisons short-circuit to NULL, so
    it returns 0 rows and leaks nothing.
    """
    schema: list[ColumnSchema] = []
    try:
        probe_vars = dict.fromkeys(_VARIABLE_RE.findall(sql))
        db.execute(sql, probe_vars)
        schema = [ColumnSchema(name=str(d[0]), type=str(d[1])) for d in db.description or []]
    except duckdb.Error:
        pass  # fall back to schema-less inference — no worse than before

    result = sqlviz_inference.infer(sql, schema=schema, brain_conn=brain, debug=debug)
    result = dataclasses.replace(
        result,
        fallback_applied=True,
        fallback_reason="Set filter values to see data",
    )
    return JSONResponse(content={"inference_result": result.to_dict(), "data": []})


@router.post("/{panel_id}/execute")
def execute_panel(
    panel_id: str,
    db: DbDep,
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
    panel = _fetch_one(db, panel_id)
    sql = panel.sql_content
    raw_vars: dict[str, Any] = body.variables if body else {}

    brain = get_brain_connection()

    # "All" semantics: a filter whose value is empty (None / "" / []) — or one
    # the client never sent — must not filter. We neutralize its predicate so
    # the panel returns every row for that dimension. This is what lets both the
    # dropdown "All" option and the very first Run (no values chosen yet) render
    # real data instead of an empty chart.
    sql_var_names = list(dict.fromkeys(_VARIABLE_RE.findall(sql)))
    active_vars = {
        name: raw_vars[name]
        for name in sql_var_names
        if name in raw_vars and not _is_empty_filter_value(raw_vars[name])
    }
    all_vars = [name for name in sql_var_names if name not in active_vars]

    # "Reveal" case: the panel has $variables but the user has chosen no value
    # for any of them (first Run, or every filter on "All"). Here the query is
    # a means to reveal the filter bar, so a query that cannot execute (missing
    # table, etc.) must still return the controls — never a hard 422.
    is_reveal = bool(sql_var_names) and not active_vars

    run_sql = sql
    if all_vars:
        neutralized = neutralize_filters(sql, all_vars)
        if neutralized is None:
            # Cannot safely strip the $placeholders (unparseable SQL, or a
            # variable used outside a boolean predicate). Fall back to
            # inference-only so the filter bar still renders; data stays empty
            # until every variable is given a concrete value.
            return _inference_only_response(sql, db, brain, debug)
        run_sql = neutralized

    # Bind only variables that survive neutralization: a range like
    # `col BETWEEN $a AND $b` collapses to TRUE when either bound is "All", so
    # its other bound is gone from run_sql and must not be bound.
    remaining = set(_VARIABLE_RE.findall(run_sql))
    bind_vars = {k: v for k, v in active_vars.items() if k in remaining}

    try:
        if bind_vars:
            db.execute(_rewrite_in_clauses_for_lists(run_sql, bind_vars), bind_vars)
        else:
            db.execute(run_sql)
    except duckdb.ParserException:
        result = sqlviz_inference.infer(sql, brain_conn=brain, debug=debug)
        result = dataclasses.replace(
            result,
            fallback_applied=True,
            fallback_reason="SQL syntax error — query could not be parsed",
        )
        return JSONResponse(content={"inference_result": result.to_dict(), "data": []})
    except duckdb.Error as exc:
        # First Run / all-"All": reveal the filter bar instead of failing hard.
        if is_reveal:
            return _inference_only_response(sql, db, brain, debug)
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    desc = db.description or []
    col_names = [str(d[0]) for d in desc]
    rows_raw = db.fetchall()

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
    store_inference(
        db,
        panel_id=panel_id,
        fingerprint=result.fingerprint,
        chart_type=result.chart_winner,
        col_span=result.col_span,
        height_px=result.panel_height_px,
        intent_type=result.intent_winner,
    )

    # Re-classify the parent dashboard from all its executed panels.
    _update_dashboard_classification(db, panel_id, col_names)

    return JSONResponse(content={"inference_result": result.to_dict(), "data": data})


@router.post("/{panel_id}/filter-domain")
def filter_domain(
    panel_id: str,
    body: FilterDomainBody,
    db: DbDep,
) -> JSONResponse:
    """Return the domain of a filter column so the UI can render a rich control.

    kind="distinct" → {"values": [...]}  (dropdown / multiselect / checkboxes)
    kind="range"    → {"min": lo, "max": hi}  (slider bounds)

    Best-effort: any failure to parse/execute returns an empty domain, and the
    frontend falls back to a plain text/number input. Never raises 5xx for a
    query it simply cannot introspect.
    """
    panel = _fetch_one(db, panel_id)
    empty: dict[str, Any] = (
        {"values": []} if body.kind == "distinct" else {"min": None, "max": None}
    )

    query = build_domain_query(panel.sql_content, body.column, body.kind)
    if query is None:
        return JSONResponse(content=empty)

    try:
        rows = db.execute(query).fetchall()
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
) -> PanelResponse:
    """Apply a user correction to a panel's inferred field.

    Writes selected_* and *_user_override in the .sqlviz file.
    Persists the pattern to brain.duckdb so future executions of the
    same SQL fingerprint return the user-preferred value.

    field_name: "chart_type" | "col_span" | "height_px"
    user_value: the corrected value (always a string; cast in OverrideSystem)

    Returns the updated PanelResponse.
    """
    _fetch_one(db, panel_id)  # raises 404 if missing
    brain = get_brain_connection()
    try:
        apply_override(db, brain, panel_id, body.field_name, body.user_value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _fetch_one(db, panel_id)
