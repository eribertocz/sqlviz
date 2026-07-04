from __future__ import annotations

from typing import Any


def compute(data: list[dict[str, Any]]) -> list[float]:
    """
    Compute result shape features (dims 35-37).
    Returns [dim35, dim36, dim37].
    """
    if not data:
        return [0.0, 0.0, 0.0]

    row_count = len(data)
    col_count = len(data[0])

    return [
        1.0 if row_count == 1 else 0.0,                        # dim 35
        1.0 if col_count == 1 else 0.0,                        # dim 36
        1.0 if row_count > 20 and col_count > 5 else 0.0,      # dim 37
    ]
