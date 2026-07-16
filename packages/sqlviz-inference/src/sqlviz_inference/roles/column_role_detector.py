from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..contracts.column_roles import ColumnRole, ColumnRoles
from ..semantic.fuzzy_match import match_column_name
from ..utils.sqlviz_logging import get_logger
from ..utils.yaml_loader import yaml_loader

_log = get_logger("column_role_detector")

if TYPE_CHECKING:
    from ..context import RuntimeContext

_NUMERIC_TYPES = frozenset({
    "TINYINT", "SMALLINT", "INTEGER", "INT", "BIGINT",
    "HUGEINT", "FLOAT", "DOUBLE", "DECIMAL", "NUMERIC", "REAL",
})

_TEMPORAL_TYPES = frozenset({
    "DATE", "TIMESTAMP", "TIMESTAMP_TZ", "TIMESTAMPTZ", "TIME", "INTERVAL",
})

_ID_SUFFIXES = ("_id", "_key")
_ID_EXACT = frozenset({"id", "pk"})

_RANK_NAMES = frozenset({
    "rank", "rn", "row_num", "row_number", "position", "pos", "orden", "ranking",
})
_RANK_PREFIXES = ("rank_", "ranking_")

_PERCENTAGE_NAMES = frozenset({
    "pct", "percent", "percentage", "porcent", "porcentaje",
    "ratio", "rate", "tasa", "cuota",
})
_PERCENTAGE_SUFFIXES = ("_pct", "_percent", "_rate", "_ratio", "_tasa")

_TEMPORAL_SEM_CLASS = "TEMPORAL_DIMENSION"
_METRIC_SEM_CLASSES = frozenset({"METRIC_REVENUE", "METRIC_COUNT", "METRIC_PROFIT"})
_CATEGORY_SEM_CLASSES = frozenset({"GEOGRAPHIC_DIMENSION", "PRODUCT_ENTITY", "CUSTOMER_ENTITY"})


class ColumnRoleDetector:
    """
    Assigns a semantic role to each schema column.

    Priority order (first match wins):
    1. ID — by name suffix (_id, _key) or exact name (id, pk)
    2. Time — by physical type (DATE/TIMESTAMP) or semantic dictionary match
    3. Rank — by name pattern (rank, rn, row_num, …)
    4. Percentage — by name pattern (pct, ratio, rate, …)
    5. Metric — numeric types that aren't IDs/ranks/percentages
    6. Category — named entities (geographic, product, customer) by dict match
    7. Dimension — fallback for non-numeric, non-temporal columns
    """

    def __init__(self) -> None:
        self._dictionary: dict[str, Any] | None = None

    @property
    def dictionary(self) -> dict[str, Any]:
        if self._dictionary is None:
            self._dictionary = yaml_loader.load("semantic_dictionary.yaml")
        return self._dictionary

    def build(self, schema: list[Any]) -> ColumnRoles:
        roles = [
            ColumnRole(name=col.name, role=self._detect(col.name, col.type))
            for col in schema
        ]
        return ColumnRoles(roles=roles)

    def run(self, context: RuntimeContext) -> RuntimeContext:
        try:
            context.column_roles = self.build(context.schema)
        except Exception as e:
            _log.warning("%s", e, extra={"trace_id": context.trace_id})
            context.errors.append(f"ColumnRoleDetector: {e}")
        return context

    def _detect(self, name: str, col_type: str) -> str:
        name_lower = name.lower()
        normalized_type = col_type.upper().split("(")[0].strip()

        # 1. ID by name (highest priority — prevents customer_id being classified as metric)
        if self._is_id(name_lower):
            return "id"

        # 2. Temporal by physical type
        if normalized_type in _TEMPORAL_TYPES:
            return "time"

        # 3. Temporal by semantic dictionary (catches VARCHAR "mes", "trimestre", "anio", etc.)
        sem_class = match_column_name(name, self.dictionary)
        if sem_class == _TEMPORAL_SEM_CLASS:
            return "time"

        # 4. Rank by name
        if self._is_rank(name_lower):
            return "rank"

        # 5. Percentage by name
        if self._is_percentage(name_lower):
            return "percentage"

        # 6. Metric: numeric types that passed all name-based checks above
        if normalized_type in _NUMERIC_TYPES:
            return "metric"

        # 7. Named category (geographic, product, customer entities)
        if sem_class in _CATEGORY_SEM_CLASSES:
            return "category"

        # 8. Metric by semantic class (VARCHAR metric column — rare edge case)
        if sem_class in _METRIC_SEM_CLASSES:
            return "metric"

        # 9. Dimension fallback
        return "dimension"

    def _is_id(self, name_lower: str) -> bool:
        if name_lower in _ID_EXACT:
            return True
        return any(name_lower.endswith(s) for s in _ID_SUFFIXES)

    def _is_rank(self, name_lower: str) -> bool:
        if name_lower in _RANK_NAMES:
            return True
        return any(name_lower.startswith(p) for p in _RANK_PREFIXES)

    def _is_percentage(self, name_lower: str) -> bool:
        if name_lower in _PERCENTAGE_NAMES:
            return True
        return any(name_lower.endswith(s) for s in _PERCENTAGE_SUFFIXES)
