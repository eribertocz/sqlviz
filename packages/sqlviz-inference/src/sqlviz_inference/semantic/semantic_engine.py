from __future__ import annotations

from typing import Any

from ..context import RuntimeContext
from ..parser.ast_helpers import get_column_names_from_select
from ..utils.yaml_loader import yaml_loader
from .fuzzy_match import match_column_name

# Semantic class → feature vector dimension
SEMANTIC_TO_DIM: dict[str, int] = {
    "METRIC_REVENUE":       30,
    "TEMPORAL_DIMENSION":   31,
    "GEOGRAPHIC_DIMENSION": 32,
    "PRODUCT_ENTITY":       33,
    "CUSTOMER_ENTITY":      34,
}

KPI_SEMANTIC_CLASSES = {"METRIC_REVENUE", "METRIC_COUNT", "METRIC_PROFIT"}
DIMENSION_CLASSES = {
    "TEMPORAL_DIMENSION", "GEOGRAPHIC_DIMENSION",
    "PRODUCT_ENTITY", "CUSTOMER_ENTITY",
}


class SemanticEngine:
    """
    Classifies column names into semantic categories.
    Fills feature vector dims 30-34.
    Uses semantic_dictionary.yaml — no hardcoded patterns in Python.
    """

    def __init__(self) -> None:
        self._dictionary: dict[str, Any] | None = None

    @property
    def dictionary(self) -> dict[str, Any]:
        if self._dictionary is None:
            self._dictionary = yaml_loader.load("semantic_dictionary.yaml")
        return self._dictionary

    def run(self, context: RuntimeContext) -> RuntimeContext:
        try:
            return self._classify(context)
        except Exception as e:
            return context.with_error("SemanticEngine", str(e))

    def _classify(self, context: RuntimeContext) -> RuntimeContext:
        fv = context.feature_vector[:]
        semantic_classes: dict[str, str] = {}

        # Classify schema columns (when schema is available)
        for col in context.schema:
            sem_class = match_column_name(col.name, self.dictionary)
            if sem_class:
                semantic_classes[col.name] = sem_class
                dim = SEMANTIC_TO_DIM.get(sem_class)
                if dim is not None:
                    fv[dim] = 1.0

        # Classify column names from the SELECT clause — runs even without
        # schema so that SQL-only calls (no schema provided) still get
        # semantic signal from column names visible in the query itself.
        if context.ast is not None:
            for col_name in get_column_names_from_select(context.ast):
                if col_name not in semantic_classes:
                    sem_class = match_column_name(col_name, self.dictionary)
                    if sem_class:
                        semantic_classes[col_name] = sem_class
                        dim = SEMANTIC_TO_DIM.get(sem_class)
                        if dim is not None:
                            fv[dim] = 1.0

        context.feature_vector = fv

        if "semantic" not in context.score_trace:
            context.score_trace["semantic"] = {}
        context.score_trace["semantic"]["column_classes"] = semantic_classes

        return context

    def classify_column(self, column_name: str) -> str | None:
        """Classify a single column name against the semantic dictionary."""
        return match_column_name(column_name, self.dictionary)
