from __future__ import annotations


def confidence_gap(normalized_scores: dict[str, float]) -> float:
    """
    Confidence gap = best_score - second_best_score.
    Higher gap → more certain inference. Returns [0.0, 1.0].
    """
    if len(normalized_scores) < 2:
        return 1.0
    sorted_scores = sorted(normalized_scores.values(), reverse=True)
    return sorted_scores[0] - sorted_scores[1]


def quality_label(
    raw_score: float,
    thresholds: dict[str, float] | None = None,
) -> str:
    """
    Convert raw_score to a quality label.
    high:   raw_score > 0.70
    medium: raw_score > 0.35
    low:    raw_score <= 0.35
    Thresholds can be overridden from thresholds.yaml.
    """
    if thresholds is None:
        thresholds = {"high": 0.70, "medium": 0.35}

    if raw_score > thresholds["high"]:
        return "high"
    elif raw_score > thresholds["medium"]:
        return "medium"
    else:
        return "low"


def should_apply_fallback(
    raw_score: float,
    min_threshold: float = 0.35,
) -> bool:
    """True if best raw_score is below threshold → apply table fallback."""
    return raw_score < min_threshold
