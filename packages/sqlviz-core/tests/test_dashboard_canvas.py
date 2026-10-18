"""Manual geometry never changes SQL identity or silently hides conflicting panels."""

from dataclasses import FrozenInstanceError, replace

import pytest
from sqlviz_core.models.dashboard_canvas import (
    MAX_CANVAS_EXTENT_PX,
    MAX_CANVAS_PANELS,
    CanvasValidationError,
    DashboardCanvas,
    PanelMinimum,
    PanelPlacement,
    assess_canvas_fit,
    move_panel,
    resize_panel,
    validate_canvas,
)


def sample(mode="scroll"):
    return DashboardCanvas(mode=mode, placements=(
        PanelPlacement("revenue", 0, 0, 6, 240),
        PanelPlacement("cost", 6, 0, 6, 320),
        PanelPlacement("detail", 0, 336, 12, 240),
    ))


@pytest.mark.parametrize("changes", [
    {"column": -1}, {"column": 12}, {"column": True}, {"column": 1.0},
    {"column_span": 0}, {"column_span": 13}, {"column_span": "6"},
    {"top_px": -1}, {"top_px": 0.5}, {"top_px": True},
    {"height_px": 119}, {"height_px": 0}, {"height_px": None},
    {"height_px": MAX_CANVAS_EXTENT_PX + 1},
    {"panel_id": ""}, {"panel_id": " \n"}, {"panel_id": "\ud800"},
    {"panel_id": "é" * 129}, {"panel_id": 1},
])
def test_invalid_geometry_and_ids_are_rejected_without_coercion(changes):
    original = PanelPlacement("p", 0, 0, 12, 120)
    invalid = replace(original, **changes)
    with pytest.raises(CanvasValidationError):
        validate_canvas(DashboardCanvas(placements=(invalid,)))
    assert original == PanelPlacement("p", 0, 0, 12, 120)


@pytest.mark.parametrize("changes,code", [
    ({"version": 2}, "unsupported_version"), ({"version": True}, "unsupported_version"),
    ({"mode": "automatic"}, "invalid_mode"), ({"mode": []}, "invalid_mode"),
    ({"gap_px": -1}, "invalid_geometry"), ({"gap_px": True}, "invalid_geometry"),
    ({"padding_px": -1}, "invalid_geometry"),
    ({"placements": []}, "invalid_placements"),
    ({"placements": ({"panel_id": "p"},)}, "invalid_placement"),
])
def test_invalid_document_is_rejected_with_predictable_code(changes, code):
    with pytest.raises(CanvasValidationError) as error:
        validate_canvas(replace(DashboardCanvas(), **changes))
    assert error.value.code == code


def test_duplicate_identity_and_excessive_panel_count_are_rejected():
    panel = PanelPlacement("p", 0, 0, 12, 120)
    with pytest.raises(CanvasValidationError, match="twice"):
        validate_canvas(DashboardCanvas(placements=(panel, panel)))
    with pytest.raises(CanvasValidationError) as error:
        validate_canvas(DashboardCanvas(placements=tuple(
            replace(panel, panel_id=str(i), top_px=i * 136) for i in range(MAX_CANVAS_PANELS + 1)
        )))
    assert error.value.code == "invalid_placements"


def test_column_boundaries_and_vertical_gap_are_exact():
    validate_canvas(sample())
    with pytest.raises(CanvasValidationError) as error:
        validate_canvas(DashboardCanvas(placements=(PanelPlacement("p", 11, 0, 2, 120),)))
    assert error.value.code == "outside_grid"
    # One pixel less than the required gap is a collision; no panel is hidden.
    with pytest.raises(CanvasValidationError) as error:
        move_panel(sample(), "detail", column=0, top_px=335)
    assert error.value.code == "collision"


def test_side_by_side_panels_can_have_different_heights_and_vertical_positions():
    canvas = DashboardCanvas(placements=(
        PanelPlacement("a", 0, 0, 6, 600), PanelPlacement("b", 6, 73, 6, 121),
    ))
    validate_canvas(canvas)


@pytest.mark.parametrize("tall_column", [0, 6])
@pytest.mark.parametrize("mode", ["scroll", "screen"])
def test_tall_panel_can_span_two_stacked_neighbors_on_either_side(tall_column, mode):
    stacked_column = 6 - tall_column
    # Two 300 px panels with a 16 px gap align with one 616 px panel.
    canvas = DashboardCanvas(mode=mode, placements=(
        PanelPlacement("tall", tall_column, 0, 6, 616),
        PanelPlacement("upper", stacked_column, 0, 6, 300),
        PanelPlacement("lower", stacked_column, 316, 6, 300),
    ))
    validate_canvas(canvas)
    fit = assess_canvas_fit(canvas, available_width_px=1280, available_height_px=648)
    assert fit.fits and fit.required_height_px == 648

    # The tall neighbor must not force the lower panel below its own bottom.
    assert canvas.placements[2].top_px < canvas.placements[0].height_px
    with pytest.raises(CanvasValidationError) as error:
        move_panel(canvas, "lower", column=stacked_column, top_px=315)
    assert error.value.code == "collision"
    assert canvas.placements[2] == PanelPlacement("lower", stacked_column, 316, 6, 300)


def test_move_changes_only_position_preserving_identity_order_and_neighbors():
    original = sample()
    moved = move_panel(original, "revenue", column=0, top_px=600)
    assert moved.placements[0] == replace(original.placements[0], top_px=600)
    assert moved.placements[1:] == original.placements[1:]
    assert [p.panel_id for p in moved.placements] == [p.panel_id for p in original.placements]
    assert original == sample()


def test_resize_preserves_exact_height_and_does_not_inherit_the_legacy_900px_cap():
    original = DashboardCanvas(placements=(PanelPlacement("p", 0, 0, 12, 120),))
    resized = resize_panel(original, "p", column_span=7, height_px=1703)
    assert resized.placements[0] == PanelPlacement("p", 0, 0, 7, 1703)
    assert original.placements[0].height_px == 120
    with pytest.raises(FrozenInstanceError):
        resized.placements[0].height_px = 200


@pytest.mark.parametrize("operation", ["move", "resize"])
def test_collision_rejects_the_whole_change_and_preserves_original(operation):
    original = sample()
    with pytest.raises(CanvasValidationError) as error:
        if operation == "move":
            move_panel(original, "revenue", column=6, top_px=0)
        else:
            resize_panel(original, "revenue", column_span=7, height_px=240)
    assert error.value.code == "collision"
    assert original == sample()


def test_missing_panel_and_oversized_extent_are_explicit():
    with pytest.raises(CanvasValidationError) as error:
        move_panel(sample(), "missing", column=0, top_px=0)
    assert error.value.code == "unknown_panel"
    with pytest.raises(CanvasValidationError) as error:
        validate_canvas(DashboardCanvas(placements=(
            PanelPlacement("p", 0, MAX_CANVAS_EXTENT_PX - 120, 12, 120),
        )))
    assert error.value.code == "extent_exceeded"


def test_screen_checks_actual_workspace_height_without_scaling_or_clipping():
    canvas = sample("screen")
    fits = assess_canvas_fit(canvas, available_width_px=1280, available_height_px=608)
    assert fits.required_height_px == 608 and fits.fits and fits.fallback is None
    small = assess_canvas_fit(canvas, available_width_px=1280, available_height_px=607)
    assert not small.fits and small.fallback == "scroll"
    assert small.issues[0].code == "canvas_height"
    assert small.issues[0].required_px == 608 and small.issues[0].available_px == 607
    assert canvas == sample("screen")


def test_scroll_allows_vertical_growth_without_discarding_author_positions():
    canvas = sample()
    fit = assess_canvas_fit(canvas, available_width_px=1280, available_height_px=100)
    assert fit.fits and fit.required_height_px == 608
    assert canvas.placements[2].top_px == 336


def test_renderer_minimums_check_actual_span_width_including_gaps_and_padding():
    canvas = DashboardCanvas(mode="screen", placements=(PanelPlacement("p", 0, 0, 6, 240),))
    # (1200 - 32 - 11*16)/12 = 82.666...; six columns + five gaps = 576.
    fit = assess_canvas_fit(canvas, available_width_px=1200, available_height_px=272,
                            minimums={"p": PanelMinimum(576, 240)})
    assert fit.fits
    small = assess_canvas_fit(canvas, available_width_px=1200, available_height_px=272,
                              minimums={"p": PanelMinimum(577, 241)})
    assert [issue.code for issue in small.issues] == ["panel_width", "panel_height"]
    assert all(issue.panel_id == "p" for issue in small.issues)
    assert small.fallback == "reflow"  # Vertical scroll alone cannot fix this.


def test_impossible_grid_width_is_reported_and_cannot_be_fixed_with_vertical_scroll():
    fit = assess_canvas_fit(sample("screen"), available_width_px=208, available_height_px=608)
    assert not fit.fits and fit.fallback == "reflow"
    assert fit.issues[0].code == "canvas_width"


@pytest.mark.parametrize("size", [0, -1, True, None, "1200", float("nan"), float("inf"),
                                 MAX_CANVAS_EXTENT_PX + 1, 10**1000])
def test_invalid_viewports_are_rejected_without_overflow(size):
    with pytest.raises(CanvasValidationError) as error:
        assess_canvas_fit(sample(), available_width_px=size, available_height_px=800)
    assert error.value.code == "invalid_viewport"


@pytest.mark.parametrize("minimums", [
    {"missing": PanelMinimum(100, 120)}, {"revenue": PanelMinimum(True, 120)},
    {"revenue": PanelMinimum(100, 0)}, {"revenue": {"width_px": 100}},
])
def test_invalid_or_stale_content_requirements_do_not_silently_pass(minimums):
    with pytest.raises(CanvasValidationError):
        assess_canvas_fit(sample(), available_width_px=1280, available_height_px=800,
                          minimums=minimums)


def test_empty_canvas_is_a_valid_starting_document():
    canvas = DashboardCanvas()
    validate_canvas(canvas)
    assert assess_canvas_fit(canvas, available_width_px=1280, available_height_px=800).fits
