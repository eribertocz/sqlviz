"""Transport-independent contract for named analytical parameter values."""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TypeAlias, cast

ParameterScalar: TypeAlias = str | int | float | bool
ParameterValue: TypeAlias = ParameterScalar | list[ParameterScalar] | None
_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


@dataclass(frozen=True)
class ParameterLimits:
    max_variables: int = 64
    max_name_bytes: int = 64
    max_string_bytes: int = 4096
    max_list_items: int = 500
    max_total_items: int = 2048
    max_total_bytes: int = 64 * 1024

    def __post_init__(self) -> None:
        if any(
            value <= 0
            for value in (
                self.max_variables,
                self.max_name_bytes,
                self.max_string_bytes,
                self.max_list_items,
                self.max_total_items,
                self.max_total_bytes,
            )
        ):
            raise ValueError("Parameter limits must be positive")


class ParameterError(ValueError):
    """Contains a field name and reason, never its submitted value."""

    def __init__(self, code: str, detail: str, variable: str | None = None):
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.variable = variable


def _scalar(value: object, name: str, limits: ParameterLimits) -> str:
    kind = type(value)
    if kind is str:
        try:
            size = len(cast(str, value).encode("utf-8"))
        except UnicodeEncodeError:
            raise ParameterError("parameter_type", "Text must be valid Unicode", name) from None
        if size > limits.max_string_bytes:
            raise ParameterError("parameter_limit", "Parameter text is too large", name)
        return "text"
    if kind is bool:
        return "boolean"
    if kind is int:
        if not -(2**127) <= cast(int, value) < 2**127:
            raise ParameterError("parameter_type", "Integer exceeds the supported range", name)
        return "number"
    if kind is float:
        if not math.isfinite(cast(float, value)):
            raise ParameterError("parameter_type", "Numbers must be finite", name)
        return "number"
    raise ParameterError("parameter_type", "Use text, numbers, booleans or a flat list", name)


def validate_parameters(
    values: Mapping[str, object],
    limits: ParameterLimits | None = None,
) -> dict[str, ParameterValue]:
    """Validate without coercion; return owned lists and canonical ASCII names.

    Names are case insensitive as in DuckDB. Empty scalar values and empty lists
    remain intact: the filter planner decides whether they mean All.
    """
    limits = limits or ParameterLimits()
    if len(values) > limits.max_variables:
        raise ParameterError("parameter_limit", "Too many parameters")
    result: dict[str, ParameterValue] = {}
    total_items = 0
    for name, value in values.items():
        if not isinstance(name, str) or not _NAME.fullmatch(name):
            raise ParameterError("parameter_name", "Use a named $parameter identifier")
        if len(name.encode("utf-8")) > limits.max_name_bytes:
            raise ParameterError("parameter_limit", "Parameter name is too long")
        canonical = name.lower()
        if canonical in result:
            raise ParameterError("parameter_name", "Duplicate parameter name", canonical)
        if isinstance(value, list):
            if len(value) > limits.max_list_items:
                raise ParameterError("parameter_limit", "Parameter list is too large", canonical)
            kinds = {_scalar(item, canonical, limits) for item in value}
            if len(kinds) > 1:
                raise ParameterError(
                    "parameter_type", "List items must have the same kind", canonical
                )
            total_items += len(value)
            result[canonical] = cast(list[ParameterScalar], value.copy())
        elif value is None:
            total_items += 1
            result[canonical] = None
        else:
            _scalar(value, canonical, limits)
            total_items += 1
            result[canonical] = cast(ParameterScalar, value)
        if total_items > limits.max_total_items:
            raise ParameterError("parameter_limit", "Too many parameter values")
    size = len(json.dumps(result, ensure_ascii=False, allow_nan=False).encode("utf-8"))
    if size > limits.max_total_bytes:
        raise ParameterError("parameter_limit", "Parameters exceed the total size limit")
    return result


def is_all(value: ParameterValue) -> bool:
    return value is None or value == "" or isinstance(value, list) and not value
