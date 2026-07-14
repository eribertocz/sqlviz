from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SemanticRelation:
    source_column: str
    target_column: str
    relation_type: str   # "lte" | "derived_from" | "ratio_of" | …
    expression: str      # human-readable: "cobrado <= facturado"


@dataclass
class SemanticProfile:
    """
    Connects columns with business concepts and their relationships.
    V0.2: YAML-backed relation map. Full knowledge graph is V0.3.
    """

    column_concepts: dict[str, str] = field(default_factory=dict)   # col → concept
    relations: list[SemanticRelation] = field(default_factory=list)
