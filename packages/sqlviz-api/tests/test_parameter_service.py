"""Filter planning preserves SQL meaning and never interpolates a value."""

from __future__ import annotations

import pytest
from sqlviz_api.services.parameters import ParameterService
from sqlviz_api.services.queries import QueryService
from sqlviz_core.models.parameters import ParameterError
from sqlviz_inference.filters.parameters import filter_parameter_names


def prepare(sql, values):
    return ParameterService().prepare(sql, values, QueryService())


def test_literals_comments_dollar_strings_and_quoted_identifiers_are_not_parameters():
    sql = "SELECT '$literal' AS \"$identifier\", $$ $dollar $$ AS note, $real -- $comment\n"
    assert filter_parameter_names(sql) == ["real"]
    plan = prepare(sql, {"real": "canary-value"})
    assert plan.bindings == {"real": "canary-value"}
    assert "canary-value" not in plan.sql


def test_case_insensitive_names_share_one_binding():
    plan = prepare("SELECT $Region, $region", {"REGION": "A"})
    assert plan.names == ("region",)
    assert plan.bindings == {"region": "A"}


def test_all_neutralization_is_case_insensitive():
    plan = prepare("SELECT * FROM (VALUES ('A')) t(region) WHERE region=$Region", {})
    assert plan.reveal
    assert "$Region" not in plan.sql
    assert plan.bindings == {}


def test_list_adaptation_only_changes_the_real_membership_node():
    plan = prepare(
        "SELECT 'IN ($names)' AS note FROM (VALUES ('A')) t(name) WHERE name IN ($names)",
        {"names": ["A"]},
    )
    assert "'IN ($names)'" in plan.sql
    assert "name IN $names" in plan.sql
    assert plan.bindings == {"names": ["A"]}


def test_range_survivors_do_not_keep_removed_bindings():
    plan = prepare(
        "SELECT * FROM (VALUES (5, 'A')) t(price, region) "
        "WHERE price BETWEEN $lo AND $hi AND region=$region",
        {"lo": 3, "hi": "", "region": "A"},
    )
    assert plan.bindings == {"region": "A"}
    assert not plan.reveal


def test_projection_requires_concrete_value():
    plan = prepare("SELECT $value AS number", {})
    assert plan.sql is None
    assert plan.names == ("value",)


@pytest.mark.parametrize("sql", ["SELECT ?", "SELECT $1"])
def test_positional_parameters_have_no_filter_contract(sql):
    with pytest.raises(ParameterError):
        prepare(sql, {})


def test_extra_global_values_are_bounded_before_being_dropped():
    assert prepare("SELECT 42", {"other_panel": "A"}).bindings == {}
    with pytest.raises(ParameterError):
        prepare("SELECT 42", {"other_panel": {"nested": "canary"}})
