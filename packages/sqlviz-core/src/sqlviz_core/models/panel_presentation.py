"""Policy for persisted panel titles and axis labels."""

from typing import Literal

PresentationField = Literal["title", "x_label", "y_label"]
MAX_PRESENTATION_TEXT_LENGTH = 512


def normalize_presentation_value(field: PresentationField, value: str | None) -> str | None:
    """Validate before writes; only null or an exact empty string restore automatic."""
    if not isinstance(field, str) or field not in {"title", "x_label", "y_label"}:
        raise ValueError("Unknown presentation field")
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("Presentation value must be a string or null")
    if value == "":
        return None
    if not value.strip() or len(value) > MAX_PRESENTATION_TEXT_LENGTH:
        raise ValueError(
            "Presentation text must be nonblank and at most "
            f"{MAX_PRESENTATION_TEXT_LENGTH} characters",
        )
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        raise ValueError("Presentation text must be valid UTF-8") from None
    return value
