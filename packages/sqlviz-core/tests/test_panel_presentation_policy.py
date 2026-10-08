"""Presentation text validation is independent of HTTP and DuckDB."""

import pytest
from sqlviz_core.models.panel_presentation import normalize_presentation_value


@pytest.mark.parametrize("field", ["title", "x_label", "y_label"])
@pytest.mark.parametrize("value", [None, ""])
def test_explicit_clear_restores_automatic(field, value):
    assert normalize_presentation_value(field, value) is None


@pytest.mark.parametrize("field", ["view_title", "updated_at", "", None, 3, []])
def test_unknown_or_invalid_fields_are_rejected(field):
    with pytest.raises(ValueError, match="Unknown presentation field"):
        normalize_presentation_value(field, "Revenue")


@pytest.mark.parametrize("value", [True, 3, 2.5, [], {}, " \n", "\ud800", "x" * 513])
def test_invalid_values_are_rejected_without_coercion(value):
    with pytest.raises(ValueError):
        normalize_presentation_value("title", value)


def test_limits_count_characters_and_preserve_exact_text():
    assert normalize_presentation_value("y_label", "é" * 512) == "é" * 512
    assert normalize_presentation_value("title", "  Ventas · 2026  ") == "  Ventas · 2026  "
