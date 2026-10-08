"""Prepare filter bindings without text substitution or renderer heuristics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlglot import exp
from sqlviz_core.models.parameters import (
    ParameterLimits,
    ParameterValue,
    is_all,
    validate_parameters,
)
from sqlviz_inference.filters.neutralize import neutralize_filters
from sqlviz_inference.filters.parameters import parameter_names

from sqlviz_api.services.queries import QueryService


@dataclass(frozen=True)
class FilterPlan:
    sql: str | None
    bindings: dict[str, ParameterValue]
    names: tuple[str, ...]
    reveal: bool


class ParameterService:
    def __init__(self, limits: ParameterLimits | None = None):
        self.limits = limits or ParameterLimits()

    def prepare(
        self,
        sql: str,
        values: dict[str, Any],
        queries: QueryService,
    ) -> FilterPlan:
        # Check every supplied value, including extras, before dropping values
        # from other panels. Existing dashboards can share a global filter map.
        parameters = validate_parameters(values, self.limits)
        tree = queries.validate(sql)
        names = parameter_names(tree)
        # Validate SQL names too: positional '?' and '$1' have no filter UI.
        validate_parameters(dict.fromkeys(names), self.limits)
        active = {
            name: parameters[name]
            for name in names
            if name in parameters and not is_all(parameters[name])
        }
        empty = [name for name in names if name not in active]
        run_sql = neutralize_filters(sql, empty) if empty else sql
        if run_sql is None:
            return FilterPlan(None, {}, tuple(names), bool(names) and not active)
        run_tree = queries.validate(run_sql)
        surviving = set(parameter_names(run_tree))
        bindings = {name: value for name, value in active.items() if name in surviving}
        changed = False
        for node in run_tree.find_all(exp.In):
            items = node.expressions
            if len(items) == 1 and isinstance(items[0], exp.Placeholder):
                if isinstance(bindings.get(items[0].name.lower()), list):
                    node.set("field", items[0].copy())
                    node.set("expressions", [])
                    changed = True
        return FilterPlan(
            run_tree.sql(dialect="duckdb") if changed else run_sql,
            bindings,
            tuple(names),
            bool(names) and not active,
        )
