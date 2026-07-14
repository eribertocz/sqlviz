from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CandidateReadability:
    """
    Readability assessment for a single chart candidate.
    Translates cardinality, label length, and series count into
    concrete layout constraints (Cleveland & McGill, Heer & Bostock).
    """

    chart_type: str
    col_span_min: int = 4
    col_span_preferred: int = 6
    col_span_max: int = 12
    height_px_recommended: int = 360
    legibility_score: float = 1.0   # 0–1; feeds into ScoringModel readability dim


@dataclass
class ReadabilityResult:
    """Output of ReadabilityModel — one entry per surviving candidate."""

    by_candidate: list[CandidateReadability] = field(default_factory=list)
