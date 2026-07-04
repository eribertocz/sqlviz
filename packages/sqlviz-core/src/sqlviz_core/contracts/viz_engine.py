from __future__ import annotations

from typing import Protocol

from sqlviz_core.models import ChartSpec, ColumnSchema


class VizEngineContract(Protocol):
    """Contract that every visualization engine must satisfy.

    Implementations registered in VizEngineRegistry.
    V0.1: ECharts only. V0.2+: Plotly. (DOC3 Section 7).
    Adding a new engine never requires changing this contract.
    """

    name: str
    supported_charts: list[str]

    def build_spec(
        self,
        chart_type: str,
        data: list[dict[str, object]],
        columns: list[ColumnSchema],
    ) -> ChartSpec: ...

    def supports(self, chart_type: str) -> bool: ...
