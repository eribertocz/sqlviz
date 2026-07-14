from __future__ import annotations

from dataclasses import dataclass, field

VALID_ROLES = frozenset({
    "metric", "dimension", "time", "id",
    "percentage", "rank", "category",
})


@dataclass
class ColumnRole:
    name: str
    role: str   # one of VALID_ROLES


@dataclass
class ColumnRoles:
    """
    Role assignment for every column in the result.
    Built by ColumnRoleDetector using name + type + AST position.
    client_id INTEGER → "id", not "metric".
    """

    roles: list[ColumnRole] = field(default_factory=list)
