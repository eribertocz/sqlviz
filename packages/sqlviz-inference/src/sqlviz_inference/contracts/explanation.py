from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Explanation:
    """
    Analyst-language explanation produced by ExplanationEngine V2 (DOC10 §6.16).

    Structured to support UI rendering (collapsible panel) and testing
    (reason_main and alternatives_rejected are independently assertable).

    full_text is the assembled Spanish explanation ready to display.
    """

    chart_winner: str
    intent: str
    reason_main: str
    reason_secondary: str
    alternatives_considered: list[str]       # scored but not winner (chart_type strings)
    alternatives_rejected: list[dict[str, str]]  # [{chart, reason}] hard-eliminated
    redundancy_note: str | None = None       # set externally if panel is redundant
    full_text: str = field(default="")
