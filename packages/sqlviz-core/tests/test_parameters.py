"""Shared parameter contract has no HTTP, SQL engine or renderer dependency."""

from __future__ import annotations

from dataclasses import replace

import pytest
from sqlviz_core.models.parameters import (
    ParameterError,
    ParameterLimits,
    is_all,
    validate_parameters,
)


@pytest.mark.parametrize(
    "value", ["A", 0, 5, 1.25, False, True, None, "", [], ["A", "B"], [1, 2.5], [False, True]]
)
def test_preserves_supported_values_and_types(value):
    result = validate_parameters({"Filter": value})
    assert result == {"filter": value}
    assert type(result["filter"]) is type(value)


@pytest.mark.parametrize(
    "value",
    [
        {"secret": "canary"},
        [[1]],
        [None],
        ["1", 1],
        [True, 1],
        float("nan"),
        float("inf"),
        2**127,
        -(2**127) - 1,
        "\ud800",
    ],
)
def test_invalid_values_are_rejected_without_echo(value):
    with pytest.raises(ParameterError) as failure:
        validate_parameters({"filter": value})
    assert failure.value.code == "parameter_type"
    assert failure.value.variable == "filter"
    assert "canary" not in str(failure.value)


@pytest.mark.parametrize("name", ["1", "?", "$filter", "region name", "x;DELETE", "", "a.b"])
def test_names_cannot_be_positional_or_sql_fragments(name):
    with pytest.raises(ParameterError) as failure:
        validate_parameters({name: 1})
    assert failure.value.code == "parameter_name"
    assert failure.value.variable is None


def test_case_collisions_are_rejected():
    with pytest.raises(ParameterError):
        validate_parameters({"Region": "A", "region": "B"})


def test_lists_are_owned_by_validated_result():
    values = {"regions": ["A"]}
    checked = validate_parameters(values)
    values["regions"].append("B")
    assert checked == {"regions": ["A"]}


@pytest.mark.parametrize(
    ("limit", "values"),
    [
        (ParameterLimits(max_variables=1), {"a": 1, "b": 2}),
        (ParameterLimits(max_name_bytes=2), {"long": 1}),
        (ParameterLimits(max_string_bytes=2), {"a": "\u20ac"}),
        (ParameterLimits(max_list_items=1), {"a": [1, 2]}),
        (ParameterLimits(max_total_items=2), {"a": [1, 2], "b": 3}),
        (ParameterLimits(max_total_bytes=4), {"a": "x"}),
    ],
)
def test_budgets_cover_all_supplied_values(limit, values):
    with pytest.raises(ParameterError) as failure:
        validate_parameters(values, limit)
    assert failure.value.code == "parameter_limit"


@pytest.mark.parametrize("field", ParameterLimits.__dataclass_fields__)
def test_nonpositive_budgets_fail_at_configuration(field):
    with pytest.raises(ValueError):
        replace(ParameterLimits(), **{field: 0})


@pytest.mark.parametrize("value", [None, "", []])
def test_empty_values_mean_all(value):
    assert is_all(value)


@pytest.mark.parametrize("value", [0, False, " ", [""], "0"])
def test_zero_false_and_whitespace_are_selections(value):
    assert not is_all(value)
