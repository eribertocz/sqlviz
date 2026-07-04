from __future__ import annotations

from ..context import FilterControl


def pair_range_filters(controls: list[FilterControl]) -> list[FilterControl]:
    """
    Detect pairs of filters on the same column that form a range
    (e.g. $desde and $hasta both filtering 'fecha') and merge them
    into a single range control.
    """
    by_column: dict[str, list[FilterControl]] = {}
    for c in controls:
        by_column.setdefault(c.column_name, []).append(c)

    result: list[FilterControl] = []
    processed: set[str] = set()

    for column_name, column_controls in by_column.items():
        if len(column_controls) == 2:
            c1, c2 = column_controls
            if c1.control_type == "date_picker" and c2.control_type == "date_picker":
                merged = FilterControl(
                    variable=f"{c1.variable},{c2.variable}",
                    label=c1.label,
                    control_type="date_range_picker",
                    column_name=column_name,
                    column_type=c1.column_type,
                    scope="global",
                )
                result.append(merged)
                processed.add(c1.variable)
                processed.add(c2.variable)
                continue
            elif c1.control_type == "numeric" and c2.control_type == "numeric":
                merged = FilterControl(
                    variable=f"{c1.variable},{c2.variable}",
                    label=c1.label,
                    control_type="range_slider",
                    column_name=column_name,
                    column_type=c1.column_type,
                    scope="global",
                )
                result.append(merged)
                processed.add(c1.variable)
                processed.add(c2.variable)
                continue

    for c in controls:
        if c.variable not in processed:
            result.append(c)

    return result
