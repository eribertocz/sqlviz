"""Domain-level PATCH semantics without HTTP, DuckDB or Pydantic."""

from __future__ import annotations

from typing import cast

import pytest
from sqlviz_core.models.dashboards import (
    MAX_DASHBOARD_DESCRIPTION_LENGTH,
    MAX_DASHBOARD_ID_LENGTH,
    MAX_DASHBOARD_NAME_LENGTH,
    MAX_DASHBOARD_SQL_BYTES,
    DashboardChanges,
    normalize_dashboard_changes,
)


@pytest.mark.parametrize("field", ["name", "sort_order", "sql_content"])
def test_required_values_cannot_be_cleared(field):
    with pytest.raises(ValueError, match="must not be null"):
        normalize_dashboard_changes(cast(DashboardChanges, {field: None}))


@pytest.mark.parametrize("field", [
    "folder_id", "connection_id", "description", "last_run_at", "last_run_sql",
])
def test_omission_and_null_remain_distinct(field):
    assert normalize_dashboard_changes({}) == {}
    changes = cast(DashboardChanges, {field: None})
    assert normalize_dashboard_changes(changes) == changes


@pytest.mark.parametrize("changes", [
    {"name": ""}, {"name": " \t\n"}, {"name": 42}, {"name": "\ud800"},
    {"sort_order": True}, {"sort_order": 1.0}, {"sort_order": "1"},
    {"sort_order": -(2**31) - 1}, {"sort_order": 2**31},
    {"folder_id": []}, {"connection_id": {}}, {"connection_id": " "},
    {"description": False}, {"sql_content": ["SELECT 1"]},
    {"last_run_at": "not-a-date"}, {"last_run_at": "2026-10-07"},
    {"last_run_at": "2026-10-07T12:00:00"}, {"last_run_sql": 123},
    {"updated_at": "2026-10-07T12:00:00Z"},
])
def test_invalid_changes_are_rejected_without_coercion(changes):
    with pytest.raises(ValueError):
        normalize_dashboard_changes(cast(DashboardChanges, changes))


@pytest.mark.parametrize("field, limit", [
    ("name", MAX_DASHBOARD_NAME_LENGTH),
    ("folder_id", MAX_DASHBOARD_ID_LENGTH),
    ("connection_id", MAX_DASHBOARD_ID_LENGTH),
    ("description", MAX_DASHBOARD_DESCRIPTION_LENGTH),
])
def test_text_limits_accept_boundary_and_reject_overflow(field, limit):
    accepted = cast(DashboardChanges, {field: "a" * limit})
    assert normalize_dashboard_changes(accepted) == accepted
    with pytest.raises(ValueError):
        normalize_dashboard_changes(cast(DashboardChanges, {field: "a" * (limit + 1)}))


@pytest.mark.parametrize("field", ["sql_content", "last_run_sql"])
def test_sql_budget_counts_utf8_bytes_and_preserves_exact_draft(field):
    text = "é" * (MAX_DASHBOARD_SQL_BYTES // 2)
    accepted = cast(DashboardChanges, {field: text})
    assert normalize_dashboard_changes(accepted) == accepted
    with pytest.raises(ValueError, match="UTF-8 bytes"):
        normalize_dashboard_changes(cast(DashboardChanges, {field: text + "é"}))


@pytest.mark.parametrize("order", [-(2**31), 0, 2**31 - 1])
def test_sort_order_accepts_exact_database_bounds(order):
    assert normalize_dashboard_changes({"sort_order": order}) == {"sort_order": order}


def test_legacy_clearing_does_not_mutate_input_or_clear_empty_sql():
    changes: DashboardChanges = {
        "folder_id": "", "connection_id": "", "description": "",
        "sql_content": "", "last_run_sql": "",
    }
    assert normalize_dashboard_changes(changes) == {
        "folder_id": None, "connection_id": None, "description": None,
        "sql_content": "", "last_run_sql": "",
    }
    assert changes["folder_id"] == "" and changes["description"] == ""


@pytest.mark.parametrize("timestamp", [
    "2026-10-07T12:00:00Z", "2026-10-07T08:00:00.123-04:00",
])
def test_timestamp_preserves_author_representation(timestamp):
    assert normalize_dashboard_changes({"last_run_at": timestamp}) == {"last_run_at": timestamp}
