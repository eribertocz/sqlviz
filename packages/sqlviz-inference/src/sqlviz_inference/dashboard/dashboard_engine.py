from __future__ import annotations

from dataclasses import dataclass, field

from ..result import InferenceResult

# KPI Shelf v0.1 — (span, col_offset) by row size (DOC5 §16.34)
_KPI_SHELF: dict[int, tuple[int, int]] = {
    1: (4, 4),  # centered: 4 empty + KPI + 4 empty
    2: (4, 2),  # centered: 2+KPI+KPI+2
    3: (4, 0),  # fills exactly: 4+4+4
    4: (3, 0),  # fills exactly: 3+3+3+3
}

# Narrative priority — mirrors analyst storytelling order
INTENT_PRIORITY: dict[str, int] = {
    "trend":        1,
    "comparison":   2,
    "ranking":      3,
    "composition":  4,
    "distribution": 5,
    "correlation":  6,
    "anomaly":      7,
    "cohort":       8,
    "retention":    9,
    "funnel":       10,
    "detail":       11,  # always last
}


@dataclass
class DashboardPanel:
    """A panel ready to render, with final position info."""
    inference_result: InferenceResult
    panel_id: str
    final_col_span: int
    row_index: int
    col_offset: int = 0  # leading empty columns before the first panel in a KPI row


@dataclass
class DashboardRow:
    panels: list[DashboardPanel] = field(default_factory=list)

    @property
    def total_span(self) -> int:
        return sum(p.final_col_span for p in self.panels)


@dataclass
class DashboardLayout:
    rows: list[DashboardRow] = field(default_factory=list)

    @property
    def panel_count(self) -> int:
        return sum(len(r.panels) for r in self.rows)


class DashboardEngine:
    """
    Composes N independently-inferred panels into a coherent
    dashboard layout.

    This is the module that fulfills SQLviz's core promise:
    "write multiple SQL queries → get a complete dashboard."

    Input:  list of (panel_id, InferenceResult) tuples
    Output: DashboardLayout
    """

    def compose(
        self,
        panels: list[tuple[str, InferenceResult]],
    ) -> DashboardLayout:
        if not panels:
            return DashboardLayout(rows=[])

        kpi_panels = [(pid, r) for pid, r in panels if r.chart_winner == "kpi"]
        other_panels = [(pid, r) for pid, r in panels if r.chart_winner != "kpi"]

        rows: list[DashboardRow] = []

        # Rule 1 — Group KPIs together in leading rows
        if kpi_panels:
            rows.extend(self._build_kpi_rows(kpi_panels))

        # Rule 2 — Narrative ordering for the rest
        ordered_others = self._order_by_narrative(other_panels)

        # Rule 3 & 4 — Row packing (full-width panels never share a row)
        rows.extend(self._pack_into_rows(ordered_others, start_row=len(rows)))

        return DashboardLayout(rows=rows)

    def _build_kpi_rows(
        self,
        kpi_panels: list[tuple[str, InferenceResult]],
    ) -> list[DashboardRow]:
        """Group KPIs into centered rows — KPI Shelf v0.1 (DOC5 §16.34)."""
        rows: list[DashboardRow] = []
        chunk_size = 4
        row_idx = 0

        for i in range(0, len(kpi_panels), chunk_size):
            chunk = kpi_panels[i : i + chunk_size]
            span, offset = _KPI_SHELF[len(chunk)]
            dashboard_panels = [
                DashboardPanel(
                    inference_result=result,
                    panel_id=pid,
                    final_col_span=span,
                    row_index=row_idx,
                    col_offset=offset if j == 0 else 0,
                )
                for j, (pid, result) in enumerate(chunk)
            ]
            rows.append(DashboardRow(panels=dashboard_panels))
            row_idx += 1

        return rows

    def _order_by_narrative(
        self,
        panels: list[tuple[str, InferenceResult]],
    ) -> list[tuple[str, InferenceResult]]:
        """Sort panels by analyst storytelling priority (Rule 2)."""
        return sorted(
            panels,
            key=lambda item: INTENT_PRIORITY.get(item[1].intent_winner, 99),
        )

    def _pack_into_rows(
        self,
        panels: list[tuple[str, InferenceResult]],
        start_row: int,
    ) -> list[DashboardRow]:
        """
        Pack panels into rows of up to 12 columns (Rules 3 & 4).
        Full-width panels (col_span == 12) always get their own row.
        """
        rows: list[DashboardRow] = []
        current_row = DashboardRow()
        row_idx = start_row

        for pid, result in panels:
            panel = DashboardPanel(
                inference_result=result,
                panel_id=pid,
                final_col_span=result.col_span,
                row_index=row_idx,
            )

            # Rule 4 — full-width panels never share a row
            if result.col_span == 12:
                if current_row.panels:
                    rows.append(current_row)
                    row_idx += 1
                    current_row = DashboardRow()
                panel.row_index = row_idx
                rows.append(DashboardRow(panels=[panel]))
                row_idx += 1
                continue

            # Rule 3 — pack into current row if it fits
            if current_row.total_span + panel.final_col_span <= 12:
                panel.row_index = row_idx
                current_row.panels.append(panel)
            else:
                rows.append(current_row)
                row_idx += 1
                panel.row_index = row_idx
                current_row = DashboardRow(panels=[panel])

        if current_row.panels:
            rows.append(current_row)

        return rows
