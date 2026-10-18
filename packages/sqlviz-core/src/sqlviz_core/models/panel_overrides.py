"""Manual panel choices, independent of inference recommendations and HTTP."""

import re

from .chart_types import CHART_TYPES

COL_SPAN_MIN = 1
COL_SPAN_MAX = 12
HEIGHT_PX_MIN = 120
HEIGHT_PX_MAX = 900


def validate_override(field_name: str, value: str | None) -> str | int | None:
    """Validate before any write. Null explicitly restores automatic sizing."""
    if field_name not in {"chart_type", "col_span", "height_px"}:
        raise ValueError("Unknown override field")
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("Override value must be a string or null")
    if field_name == "chart_type":
        # Dataset compatibility is evaluated separately from identifier validity.
        if value not in CHART_TYPES:
            raise ValueError("Unsupported chart type")
        return value
    lower, upper = (
        (COL_SPAN_MIN, COL_SPAN_MAX) if field_name == "col_span"
        else (HEIGHT_PX_MIN, HEIGHT_PX_MAX)
    )
    if len(value) > 4 or re.fullmatch(r"[0-9]+", value) is None:
        raise ValueError("Panel dimension must be an unsigned integer string")
    number = int(value)
    if not lower <= number <= upper:
        raise ValueError(f"Panel dimension must be between {lower} and {upper}")
    return number


def valid_dimension(field_name: str, value: object) -> bool:
    """Ignore invalid historical overrides when rendering; never mutate the file."""
    if type(value) is not int:
        return False
    if field_name == "col_span":
        return COL_SPAN_MIN <= value <= COL_SPAN_MAX
    if field_name == "height_px":
        return HEIGHT_PX_MIN <= value <= HEIGHT_PX_MAX
    return False
