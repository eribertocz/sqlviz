"""Basic panel changes have the same policy without HTTP or DuckDB."""

from typing import cast

import pytest
from sqlviz_core.models.panels import (
    MAX_PANEL_NAME_LENGTH,
    MAX_PANEL_SQL_BYTES,
    PanelChanges,
    validate_panel_changes,
)


@pytest.mark.parametrize("changes", [
    {"name": None}, {"sql_content": None}, {"sort_order": None},
    {"name": ""}, {"name": " \n\t"}, {"name": 123}, {"name": "\ud800"},
    {"name": "x" * (MAX_PANEL_NAME_LENGTH + 1)},
    {"sql_content": False}, {"sql_content": []}, {"sql_content": "\udfff"},
    {"sort_order": True}, {"sort_order": 1.0}, {"sort_order": "1"},
    {"sort_order": -(2**31) - 1}, {"sort_order": 2**31},
    {"dashboard_id": "other"}, {"updated_at": "now"}, {"selected_chart_type": "bar"},
])
def test_invalid_fields_are_rejected_without_coercion(changes):
    before = changes.copy()
    with pytest.raises(ValueError):
        validate_panel_changes(cast(PanelChanges, changes))
    assert changes == before


@pytest.mark.parametrize("order", [-(2**31), 0, 2**31 - 1])
def test_exact_integer_bounds_are_accepted(order):
    validate_panel_changes({"sort_order": order})


def test_text_boundaries_count_sql_as_utf8_bytes():
    validate_panel_changes({"name": "é" * MAX_PANEL_NAME_LENGTH})
    text = "é" * (MAX_PANEL_SQL_BYTES // 2)
    validate_panel_changes({"sql_content": text})
    with pytest.raises(ValueError, match="UTF-8 bytes"):
        validate_panel_changes({"sql_content": text + "é"})


@pytest.mark.parametrize("sql", ["", " \n", "-- ñ\r\nSELECT 'a;b' AS label;\n"])
def test_omission_and_exact_text_are_preserved(sql):
    validate_panel_changes({})
    changes: PanelChanges = {"name": "  Revenue  ", "sql_content": sql}
    before = changes.copy()
    validate_panel_changes(changes)
    assert changes == before
