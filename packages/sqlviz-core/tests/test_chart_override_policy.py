"""Reject unknown identifiers before persistence, independently of HTTP."""

import pytest
from sqlviz_core.models.chart_types import CHART_TYPES
from sqlviz_core.models.panel_overrides import validate_override


@pytest.mark.parametrize("chart", CHART_TYPES)
def test_supported_identifiers_are_preserved(chart):
    assert validate_override("chart_type", chart) == chart


@pytest.mark.parametrize("value", ["", " ", "BAR", " bar", "bar ", "funnel", "unknown",
                                  "\ud800", "x" * 65, 1, True, [], {}])
def test_invalid_identifiers_and_types_are_rejected(value):
    with pytest.raises(ValueError):
        validate_override("chart_type", value)


def test_null_means_follow_future_inference():
    assert validate_override("chart_type", None) is None
