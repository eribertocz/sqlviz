from __future__ import annotations

from dataclasses import dataclass, field

from ..result import InferenceResult

# Actions that InformationGainEngine V2 recommends per redundant panel
_ACTION_REMOVE = "remove"
_ACTION_LOWER_PRIORITY = "lower_priority"
_ACTION_CONVERT_TO_TABLE = "convert_to_table"


@dataclass
class RedundancyReport:
    """
    Identifies panels that convey the same information as another panel.
    Reports only — does not automatically remove or reorder panels.
    The user decides what to do with redundancy (DOC10 §6.13).

    V2 (Fase F) adds `recommendations`: actionable suggestions per redundant panel.
    """

    redundant_pairs: list[tuple[str, str]] = field(default_factory=list)
    # (panel_id_a, panel_id_b): B is redundant given A

    recommendations: dict[str, str] = field(default_factory=dict)
    # {panel_id: action} where action ∈ {"remove","lower_priority","convert_to_table"}

    @property
    def redundancy_count(self) -> int:
        return len(self.redundant_pairs)

    @property
    def redundant_panel_ids(self) -> set[str]:
        return {b for _, b in self.redundant_pairs}

    def recommendation_for(self, panel_id: str) -> str | None:
        """Return the recommended action for panel_id, or None if not redundant."""
        return self.recommendations.get(panel_id)


class InformationGainEngine:
    """
    Detects panels that add no new information relative to panels
    already in the dashboard.

    Two panels are considered redundant when:
    1. They share the same SQL fingerprint (identical normalized query), OR
    2. They share the same intent_winner AND chart_winner AND have the same
       result shape (row_count + col_count), suggesting they visualize the
       same data with the same chart type.

    V2 (Fase F): also provides actionable recommendations per redundant panel:
      - Rule 1 (fingerprint) → "remove"  (exact same query — no added value)
      - Rule 2 (shape), chart != "table" → "convert_to_table"
      - Rule 2 (shape), chart == "table" → "lower_priority"
    """

    def analyze(
        self,
        panels: list[tuple[str, InferenceResult]],
    ) -> RedundancyReport:
        if len(panels) < 2:
            return RedundancyReport()

        seen_fingerprints: dict[str, str] = {}  # fingerprint → first panel_id
        seen_signatures: dict[tuple[str, str, int, int], str] = {}
        redundant_pairs: list[tuple[str, str]] = []
        recommendations: dict[str, str] = {}

        for panel_id, result in panels:
            # Rule 1: same fingerprint → recommend removal (identical data source)
            fp = result.fingerprint
            if fp and fp != "UNKNOWN":
                if fp in seen_fingerprints:
                    redundant_pairs.append((seen_fingerprints[fp], panel_id))
                    recommendations[panel_id] = _ACTION_REMOVE
                    continue
                seen_fingerprints[fp] = panel_id

            # Rule 2: same intent + chart + result shape
            dp = result.data_profile
            row_count = dp.row_count if dp else 0
            col_count = dp.col_count if dp else 0
            sig = (result.intent_winner, result.chart_winner, row_count, col_count)
            if row_count > 0 and sig in seen_signatures:
                if (seen_signatures[sig], panel_id) not in redundant_pairs:
                    redundant_pairs.append((seen_signatures[sig], panel_id))
                    # Action depends on chart type: non-table → convert; table → deprioritize
                    if result.chart_winner == "table":
                        recommendations[panel_id] = _ACTION_LOWER_PRIORITY
                    else:
                        recommendations[panel_id] = _ACTION_CONVERT_TO_TABLE
            elif row_count > 0:
                seen_signatures[sig] = panel_id

        return RedundancyReport(
            redundant_pairs=redundant_pairs,
            recommendations=recommendations,
        )
