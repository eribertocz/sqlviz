from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ChartScore:
    """
    10-dimension score from ScoringModel (Fase C).
    Score = positives − negatives (see DOC10 §6.8).
    Each dimension individually visible for explanation and debugging.
    """

    # Positive dimensions
    semantic_fit: float = 0.0
    task_fit: float = 0.0
    perceptual_accuracy: float = 0.0
    readability: float = 0.0           # populated by ReadabilityModel (step 8 → step 9)
    information_density: float = 0.0
    business_relevance: float = 0.0

    # Negative dimensions
    cognitive_load: float = 0.0
    visual_clutter: float = 0.0
    ambiguity: float = 0.0
    interaction_cost: float = 0.0


@dataclass
class ChartCandidate:
    """
    A chart candidate with full decomposed score, produced after
    ConstraintEngine filters and ScoringModel ranks.
    """

    chart_type: str
    score: ChartScore = field(default_factory=ChartScore)
    rank: int = 0                        # 1 = winner after scoring
    eliminated_by_rule: str | None = None   # set if hard constraint eliminated it
