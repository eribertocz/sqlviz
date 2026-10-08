"""Manual dashboard geometry, independent of SQL, inference, HTTP and the DOM.

Columns use a fixed twelve-column grid; vertical coordinates are CSS pixels.
This internal contract does not replace the current composed layout or PATCH API.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Literal, TypedDict

from .panel_overrides import COL_SPAN_MAX, HEIGHT_PX_MIN

CANVAS_VERSION = 1
CANVAS_COLUMNS = COL_SPAN_MAX
MAX_CANVAS_PANELS = 256
# An operational document budget, not a recommended chart height.
MAX_CANVAS_EXTENT_PX = 1_000_000

CanvasMode = Literal["scroll", "screen"]


class _PlacementChanges(TypedDict, total=False):
    column: int
    top_px: int
    column_span: int
    height_px: int


class CanvasValidationError(ValueError):
    """A candidate is rejected as a whole; the previous layout is unchanged."""

    def __init__(self, code: str, message: str, panel_id: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.panel_id = panel_id


@dataclass(frozen=True)
class PanelPlacement:
    panel_id: str
    column: int
    top_px: int
    column_span: int
    height_px: int


@dataclass(frozen=True)
class DashboardCanvas:
    placements: tuple[PanelPlacement, ...] = ()
    mode: CanvasMode = "scroll"
    gap_px: int = 16
    padding_px: int = 16
    version: int = CANVAS_VERSION


@dataclass(frozen=True)
class PanelMinimum:
    """Measured content requirements supplied by a renderer, not inferred here."""

    width_px: int
    height_px: int


@dataclass(frozen=True)
class CanvasFitIssue:
    code: Literal["canvas_width", "canvas_height", "panel_width", "panel_height"]
    required_px: float
    available_px: float
    panel_id: str | None = None


@dataclass(frozen=True)
class CanvasFit:
    required_height_px: int
    issues: tuple[CanvasFitIssue, ...]

    @property
    def fits(self) -> bool:
        return not self.issues

    @property
    def fallback(self) -> Literal["scroll", "reflow"] | None:
        # Vertical scroll cannot repair a panel that is too narrow/short.
        if any(issue.code != "canvas_height" for issue in self.issues):
            return "reflow"
        return "scroll" if self.issues else None


def _integer(value: int, lower: int, upper: int, name: str) -> None:
    if type(value) is not int or not lower <= value <= upper:
        raise CanvasValidationError("invalid_geometry", f"{name} is outside its integer bounds")


def validate_canvas(canvas: DashboardCanvas) -> None:
    """Validate all placements without moving, compacting or resizing any panel."""
    if type(canvas.version) is not int or canvas.version != CANVAS_VERSION:
        raise CanvasValidationError("unsupported_version", "Unsupported canvas version")
    if not isinstance(canvas.mode, str) or canvas.mode not in {"scroll", "screen"}:
        raise CanvasValidationError("invalid_mode", "Canvas mode must be scroll or screen")
    _integer(canvas.gap_px, 0, MAX_CANVAS_EXTENT_PX, "Gap")
    _integer(canvas.padding_px, 0, MAX_CANVAS_EXTENT_PX // 2, "Padding")
    if type(canvas.placements) is not tuple or len(canvas.placements) > MAX_CANVAS_PANELS:
        raise CanvasValidationError("invalid_placements", "Placements must be a bounded tuple")
    seen: set[str] = set()
    for panel in canvas.placements:
        if not isinstance(panel, PanelPlacement):
            raise CanvasValidationError("invalid_placement", "Expected a panel placement")
        if not isinstance(panel.panel_id, str) or not panel.panel_id.strip():
            raise CanvasValidationError("invalid_panel_id", "Panel ID must contain text")
        try:
            encoded_id = panel.panel_id.encode("utf-8")
        except UnicodeEncodeError:
            raise CanvasValidationError(
                "invalid_panel_id", "Panel ID must be valid UTF-8",
            ) from None
        if len(encoded_id) > 256:
            raise CanvasValidationError("invalid_panel_id", "Panel ID exceeds its byte budget")
        if panel.panel_id in seen:
            raise CanvasValidationError("duplicate_panel", "Panel ID appears twice", panel.panel_id)
        seen.add(panel.panel_id)
        _integer(panel.column, 0, CANVAS_COLUMNS - 1, "Column")
        _integer(panel.column_span, 1, CANVAS_COLUMNS, "Column span")
        _integer(panel.top_px, 0, MAX_CANVAS_EXTENT_PX, "Top")
        _integer(panel.height_px, HEIGHT_PX_MIN, MAX_CANVAS_EXTENT_PX, "Height")
        if panel.column + panel.column_span > CANVAS_COLUMNS:
            raise CanvasValidationError(
                "outside_grid", "Panel exceeds twelve columns", panel.panel_id,
            )
        if panel.top_px + panel.height_px + canvas.padding_px * 2 > MAX_CANVAS_EXTENT_PX:
            raise CanvasValidationError("extent_exceeded", "Canvas exceeds its pixel budget")
    for index, first in enumerate(canvas.placements):
        for second in canvas.placements[index + 1:]:
            intersects_columns = (
                first.column < second.column + second.column_span
                and second.column < first.column + first.column_span
            )
            intersects_vertical_space = (
                first.top_px < second.top_px + second.height_px + canvas.gap_px
                and second.top_px < first.top_px + first.height_px + canvas.gap_px
            )
            if intersects_columns and intersects_vertical_space:
                raise CanvasValidationError(
                    "collision", "Panels overlap or lack the required gap", second.panel_id,
                )


def _change_panel(
    canvas: DashboardCanvas, panel_id: str, changes: _PlacementChanges,
) -> DashboardCanvas:
    validate_canvas(canvas)
    if not any(panel.panel_id == panel_id for panel in canvas.placements):
        raise CanvasValidationError("unknown_panel", "Panel is absent from this canvas", panel_id)
    candidate = replace(canvas, placements=tuple(
        replace(panel, **changes) if panel.panel_id == panel_id else panel
        for panel in canvas.placements
    ))
    validate_canvas(candidate)
    return candidate


def move_panel(
    canvas: DashboardCanvas, panel_id: str, *, column: int, top_px: int,
) -> DashboardCanvas:
    """Propose a move without changing panel identity, size or document ordering."""
    return _change_panel(canvas, panel_id, {"column": column, "top_px": top_px})


def resize_panel(
    canvas: DashboardCanvas, panel_id: str, *, column_span: int, height_px: int,
) -> DashboardCanvas:
    """Propose an exact size; never silently clamp or displace neighboring panels."""
    return _change_panel(canvas, panel_id, {"column_span": column_span, "height_px": height_px})


def assess_canvas_fit(
    canvas: DashboardCanvas, *, available_width_px: float, available_height_px: float,
    minimums: Mapping[str, PanelMinimum] | None = None,
) -> CanvasFit:
    """Assess the actual workspace; report a fallback without changing author intent.

    Screen mode checks the authored content's extent, not a scaled screenshot.
    Filling the viewport, responsive layouts and renderer measurements are later
    adapters; they must not be confused with this pure feasibility check.
    """
    validate_canvas(canvas)
    for value in (available_width_px, available_height_px):
        if (type(value) not in (int, float) or not 0 < value <= MAX_CANVAS_EXTENT_PX
                or not math.isfinite(value)):
            raise CanvasValidationError(
                "invalid_viewport", "Workspace size must be finite and positive",
            )
    requirements = minimums if minimums is not None else {}
    ids = {panel.panel_id for panel in canvas.placements}
    if not requirements.keys() <= ids:
        raise CanvasValidationError("unknown_panel", "Minimum references an absent panel")
    for requirement in requirements.values():
        if not isinstance(requirement, PanelMinimum):
            raise CanvasValidationError("invalid_minimum", "Expected a measured panel minimum")
        _integer(requirement.width_px, 1, MAX_CANVAS_EXTENT_PX, "Minimum width")
        _integer(requirement.height_px, 1, MAX_CANVAS_EXTENT_PX, "Minimum height")
    required_height = max((p.top_px + p.height_px for p in canvas.placements), default=0)
    required_height += canvas.padding_px * 2
    issues: list[CanvasFitIssue] = []
    gaps_and_padding = canvas.padding_px * 2 + canvas.gap_px * (CANVAS_COLUMNS - 1)
    column_width = (available_width_px - gaps_and_padding) / CANVAS_COLUMNS
    if canvas.placements and column_width <= 0:
        issues.append(CanvasFitIssue("canvas_width", gaps_and_padding + 1, available_width_px))
    else:
        for panel in canvas.placements:
            minimum = requirements.get(panel.panel_id)
            if minimum is None:
                continue
            panel_width = column_width * panel.column_span + canvas.gap_px * (panel.column_span - 1)
            if panel_width < minimum.width_px:
                issues.append(CanvasFitIssue(
                    "panel_width", minimum.width_px, panel_width, panel.panel_id,
                ))
            if panel.height_px < minimum.height_px:
                issues.append(CanvasFitIssue(
                    "panel_height", minimum.height_px, panel.height_px, panel.panel_id,
                ))
    if canvas.mode == "screen" and required_height > available_height_px:
        issues.append(CanvasFitIssue("canvas_height", required_height, available_height_px))
    return CanvasFit(required_height, tuple(issues))
