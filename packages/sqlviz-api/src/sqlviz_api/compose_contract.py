"""Composition wire contract. Pydantic stays at the HTTP boundary.

The engine receives ordinary dataclasses; clients receive their original wire
result, including omitted optional fields. Composition never re-runs inference.
"""

from __future__ import annotations

import math
from typing import Annotated, Any, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    ModelWrapValidatorHandler,
    PrivateAttr,
    RootModel,
    model_validator,
)
from sqlviz_core.models.panel_overrides import (
    COL_SPAN_MAX,
    COL_SPAN_MIN,
    HEIGHT_PX_MAX,
    HEIGHT_PX_MIN,
)
from sqlviz_inference.contracts.explanation import Explanation
from sqlviz_inference.contracts.layout import DashboardRole, LayoutDeclaration
from sqlviz_inference.profile.data_profile import ColumnProfile, DataProfile
from sqlviz_inference.result import InferenceResult
from sqlviz_inference.spec.visual_spec import VisualSpec

MAX_COMPOSE_PANELS = 256
ColumnSpan = Annotated[int, Field(ge=COL_SPAN_MIN, le=COL_SPAN_MAX)]
PanelHeight = Annotated[int, Field(ge=HEIGHT_PX_MIN, le=HEIGHT_PX_MAX)]
NonNegativeInt = Annotated[int, Field(ge=0)]
Name = Annotated[str, Field(min_length=1, max_length=128)]


class _Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class ColumnProfileInput(_Contract):
    name: str
    type: str
    cardinality: NonNegativeInt
    null_count: NonNegativeInt
    null_fraction: Annotated[float, Field(ge=0, le=1)]
    max_label_length: NonNegativeInt
    mean_label_length: Annotated[float, Field(ge=0)]
    is_numeric: bool


class DataProfileInput(_Contract):
    row_count: NonNegativeInt
    col_count: NonNegativeInt
    single_row: bool
    wide_table: bool
    column_profiles: list[ColumnProfileInput] = Field(default_factory=list)

    def to_domain(self) -> DataProfile:
        return DataProfile(
            row_count=self.row_count,
            col_count=self.col_count,
            single_row=self.single_row,
            wide_table=self.wide_table,
            column_profiles=[ColumnProfile(**item.model_dump()) for item in self.column_profiles],
        )


class VisualSpecInput(_Contract):
    chart_type: Name
    x_field: str | None
    y_fields: list[str]
    orientation: Literal["vertical", "horizontal", "none"]
    sort_order: Literal["asc", "desc", "none"]
    color_field: str | None
    stack: bool
    number_format: Literal["default", "percent", "currency"]
    tooltip_fields: list[str] = Field(default_factory=list)
    schema_version: Literal["1"] = "1"
    # Presentation labels are added by the API after inference.
    x_label: str | None = None
    y_label: str | None = None

    def to_domain(self) -> VisualSpec:
        return VisualSpec(**self.model_dump(exclude={"x_label", "y_label"}))


class LayoutDeclarationInput(_Contract):
    # Inference currently emits an empty ID here; ComposeItem owns identity.
    panel_id: str
    col_span_min: ColumnSpan = 4
    col_span_preferred: ColumnSpan = 6
    col_span_max: ColumnSpan = 12
    height_px_min: PanelHeight = 240
    height_px_preferred: PanelHeight = 360
    height_px_max: PanelHeight = 600

    @model_validator(mode="after")
    def ordered_ranges(self) -> Self:
        if not self.col_span_min <= self.col_span_preferred <= self.col_span_max:
            raise ValueError("Column spans must satisfy min <= preferred <= max")
        if not self.height_px_min <= self.height_px_preferred <= self.height_px_max:
            raise ValueError("Panel heights must satisfy min <= preferred <= max")
        return self


class DashboardRoleInput(_Contract):
    panel_id: str
    role: Literal[
        "resumen_ejecutivo", "historia_principal", "explicacion_secundaria",
        "diagnostico", "tabla_de_detalle", "control",
    ] = "historia_principal"
    priority: int = 5


class ExplanationInput(_Contract):
    chart_winner: Name
    intent: Name
    reason_main: str
    reason_secondary: str
    alternatives_considered: list[str]
    alternatives_rejected: list[dict[str, str]]
    redundancy_note: str | None = None
    full_text: str = ""


class CompositionInferenceInput(_Contract):
    rules_version: str
    feature_vector_version: str
    engine_version: str
    intent_winner: Name
    intent_raw_score: float
    intent_normalized_score: float
    intent_confidence_gap: float
    intent_quality: str
    intent_alternatives: list[dict[str, JsonValue]]
    chart_winner: Name
    chart_raw_score: float
    chart_normalized_score: float
    chart_confidence_gap: float
    chart_quality: str
    chart_alternatives: list[dict[str, JsonValue]]
    col_span: ColumnSpan
    row_span: Annotated[int, Field(ge=1, le=3)]
    layout_importance: float
    panel_height_px: PanelHeight
    trend_direction_label: Literal["growing", "declining", "flat", "unknown"]
    filter_controls: list[dict[str, JsonValue]]
    title: str
    title_confidence: float
    fallback_applied: bool
    fallback_reason: str
    explanation: list[dict[str, JsonValue]]
    score_trace: dict[str, JsonValue]
    fingerprint: str
    feature_vector: list[float]
    errors: list[str]
    elapsed_ms: Annotated[float, Field(ge=0)]
    data_profile: DataProfileInput | None = None
    visual_spec: VisualSpecInput | None = None
    layout_declaration: LayoutDeclarationInput | None = None
    dashboard_role: DashboardRoleInput | None = None
    explanation_v2: ExplanationInput | None = None
    feedback_preferred_chart: Name | None = None
    chart_engine_winner: Name | None = None
    chart_user_override: Name | None = None
    trace_id: str = ""
    execution_state: Literal["success", "warning", "degraded", "failed"] = "success"
    module_timings: dict[str, Annotated[float, Field(ge=0)]] | None = None
    result_schema_version: Literal["1"] = "1"

    _wire_result: dict[str, Any] = PrivateAttr(default_factory=dict)

    @model_validator(mode="wrap")
    @classmethod
    def validate_wire(
        cls, value: Any, handler: ModelWrapValidatorHandler[Self],
    ) -> Self:
        # Opaque diagnostics also have to be JSON-serializable. Python's JSON
        # parser accepts NaN/Infinity; JSONResponse correctly refuses them.
        pending = [value]
        while pending:
            item = pending.pop()
            if isinstance(item, float) and not math.isfinite(item):
                raise ValueError("Inference results must contain only finite numbers")
            if isinstance(item, dict):
                pending.extend(item.values())
            elif isinstance(item, list):
                pending.extend(item)
        result = handler(value)
        if isinstance(value, dict):
            result._wire_result = value.copy()
        return result

    def wire_result(self) -> dict[str, Any]:
        return self._wire_result

    def to_domain(self) -> InferenceResult:
        values = self.model_dump()
        values["data_profile"] = self.data_profile.to_domain() if self.data_profile else None
        values["visual_spec"] = self.visual_spec.to_domain() if self.visual_spec else None
        for name, contract, domain in (
            ("layout_declaration", self.layout_declaration, LayoutDeclaration),
            ("dashboard_role", self.dashboard_role, DashboardRole),
            ("explanation_v2", self.explanation_v2, Explanation),
        ):
            values[name] = domain(**contract.model_dump()) if contract is not None else None
        return InferenceResult(**values)


class ComposeItem(_Contract):
    panel_id: Name
    inference_result: CompositionInferenceInput


class ComposeRequest(RootModel[list[ComposeItem]]):
    root: Annotated[list[ComposeItem], Field(max_length=MAX_COMPOSE_PANELS)]

    @model_validator(mode="after")
    def unique_panel_ids(self) -> Self:
        ids = [item.panel_id for item in self.root]
        if len(ids) != len(set(ids)):
            raise ValueError("Each panel_id must appear only once in a composition")
        if any(not panel_id.strip() for panel_id in ids):
            raise ValueError("Panel IDs cannot be blank")
        return self
