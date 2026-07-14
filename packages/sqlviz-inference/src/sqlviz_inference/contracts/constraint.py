from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ConstraintViolation:
    chart_type: str
    rule_name: str
    rule_type: str   # "hard" (eliminates) | "soft" (penalizes)
    reason: str
    penalty: float = 0.0   # 0.0 for hard rules; >0 for soft rules


@dataclass
class ConstraintReport:
    """
    Audit trail of every rule ConstraintEngine evaluated.
    Hard violations eliminate candidates; soft violations penalize scores.
    Consumed by ExplanationEngine V2 to produce analyst-language explanations.
    """

    eliminated: list[ConstraintViolation] = field(default_factory=list)
    penalized: list[ConstraintViolation] = field(default_factory=list)
    rules_checked: int = 0
