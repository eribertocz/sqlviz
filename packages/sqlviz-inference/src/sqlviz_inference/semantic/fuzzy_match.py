from __future__ import annotations

import re
from typing import Any


def normalize_name(name: str) -> str:
    """
    Normalize a column name for dictionary matching.
    Handles snake_case, camelCase, spaces, and accented characters.
    """
    # Convert camelCase to snake_case (insert _ before uppercase letters)
    name = re.sub(r"([A-Z])", r"_\1", name).lower()
    # Replace every non-alphanumeric character with underscore
    name = re.sub(r"[^a-z0-9]", "_", name)
    # Remove leading/trailing underscores
    name = name.strip("_")
    # Collapse consecutive underscores
    name = re.sub(r"_+", "_", name)
    return name


def match_column_name(
    column_name: str,
    dictionary: dict[str, Any],
) -> str | None:
    """
    Match a column name against the semantic dictionary.
    Returns the semantic class name, or None if no match.

    Matching strategy (in order, first match wins):
    1. Exact match (both sides normalized, case-insensitive)
    2. Contains match (normalized column name contains normalized pattern)
    """
    normalized = normalize_name(column_name)

    # Split into underscore-separated tokens for word-level contains matching.
    # This prevents "count" from matching "country", "income" from matching
    # "income_statement_total", etc.
    tokens = set(normalized.split("_"))

    for semantic_class, patterns in dictionary.items():
        # 1. Exact match (full normalized name equals normalized pattern)
        for pattern in patterns.get("exact", []):
            if normalized == normalize_name(str(pattern)):
                return str(semantic_class)

        # 2. Contains match (pattern appears as a complete token in the name)
        for pattern in patterns.get("contains", []):
            if normalize_name(str(pattern)) in tokens:
                return str(semantic_class)

    return None
