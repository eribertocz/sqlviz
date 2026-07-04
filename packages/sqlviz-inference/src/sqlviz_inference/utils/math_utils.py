from __future__ import annotations

import math


def compute_mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def compute_stddev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = compute_mean(values)
    variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(variance)


def compute_trend_strength(values: list[float]) -> float:
    """
    R² of linear regression on values. Measures goodness-of-fit to a line.
    Returns [0.0, 1.0]. See Section 16.2 — strength != direction.
    """
    n = len(values)
    if n < 3:
        return 0.0

    x = list(range(n))
    x_mean = sum(x) / n
    y_mean = sum(values) / n

    ss_xy = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
    ss_xx = sum((x[i] - x_mean) ** 2 for i in range(n))

    if ss_xx == 0:
        return 0.0

    b = ss_xy / ss_xx
    a = y_mean - b * x_mean

    y_pred = [a + b * xi for xi in x]
    ss_res = sum((values[i] - y_pred[i]) ** 2 for i in range(n))
    ss_tot = sum((values[i] - y_mean) ** 2 for i in range(n))

    if ss_tot == 0:
        # All values equal: undefined R² — no trend information (§16.16)
        return 0.0

    return max(0.0, 1.0 - ss_res / ss_tot)


def compute_trend_direction(values: list[float]) -> float:
    """
    Normalized slope direction of a linear trend (DOC5 §16.2).
    Returns [0.0, 1.0]: 0.0 = declining, 0.5 = flat, 1.0 = growing.
    """
    n = len(values)
    if n < 3:
        return 0.5

    x = list(range(n))
    x_mean = sum(x) / n
    y_mean = sum(values) / n

    ss_xy = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
    ss_xx = sum((x[i] - x_mean) ** 2 for i in range(n))

    if ss_xx == 0:
        return 0.5

    slope = ss_xy / ss_xx

    if y_mean == 0:
        return 0.5

    relative_slope = slope / abs(y_mean)
    normalized = 1.0 / (1.0 + math.exp(-10 * relative_slope))
    return max(0.0, min(1.0, normalized))


def compute_skewness(values: list[float]) -> float:
    """
    Skewness of a distribution: (1/n) * Σ((xᵢ - μ) / σ)³.
    |skewness| < 1 → symmetric. |skewness| > 2 → highly skewed.
    """
    n = len(values)
    if n < 3:
        return 0.0
    mean = compute_mean(values)
    std = compute_stddev(values)
    if std == 0:
        return 0.0
    return sum(((v - mean) / std) ** 3 for v in values) / n


def compute_kurtosis(values: list[float]) -> float:
    """
    Excess kurtosis: (1/n) * Σ((xᵢ - μ) / σ)⁴ - 3.
    kurtosis > 3 → heavy tails. kurtosis < -1 → flat.
    """
    n = len(values)
    if n < 4:
        return 0.0
    mean = compute_mean(values)
    std = compute_stddev(values)
    if std == 0:
        return 0.0
    return sum(((v - mean) / std) ** 4 for v in values) / n - 3


def has_statistical_outliers(
    values: list[float], z_threshold: float = 3.0
) -> bool:
    """True if any value has Z-score > z_threshold (>1% of values)."""
    if len(values) < 4:
        return False
    mean = compute_mean(values)
    std = compute_stddev(values)
    if std == 0:
        return False
    outlier_count = sum(
        1 for v in values if abs((v - mean) / std) > z_threshold
    )
    return (outlier_count / len(values)) > 0.01


def pearson_r(x: list[float], y: list[float]) -> float:
    """Pearson correlation coefficient in [-1.0, 1.0]."""
    n = len(x)
    if n < 3 or len(y) != n:
        return 0.0
    x_mean = compute_mean(x)
    y_mean = compute_mean(y)
    numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
    denom_x = sum((x[i] - x_mean) ** 2 for i in range(n))
    denom_y = sum((y[i] - y_mean) ** 2 for i in range(n))
    denominator = math.sqrt(denom_x * denom_y)
    if denominator == 0:
        return 0.0
    return max(-1.0, min(1.0, numerator / denominator))


def compute_cardinality_ratio(values: list[object]) -> float:
    """unique_values / total_values → [0, 1]."""
    if not values:
        return 0.0
    return len(set(str(v) for v in values)) / len(values)


def softmax(scores: dict[str, float]) -> dict[str, float]:
    """
    Numerically stable softmax. Values sum to 1.0.
    NOTE: In V0 these are normalized_scores, not true probabilities.
    """
    if not scores:
        return {}
    max_score = max(scores.values())
    exp_scores = {k: math.exp(v - max_score) for k, v in scores.items()}
    total = sum(exp_scores.values())
    if total == 0:
        return {k: 1.0 / len(scores) for k in scores}
    return {k: v / total for k, v in exp_scores.items()}


def min_max_normalize(scores: dict[str, float]) -> dict[str, float]:
    """
    Min-max normalization — honest relative ranking.
    Does not create artificial winners above a threshold.
    """
    if not scores:
        return {}
    min_s = min(scores.values())
    max_s = max(scores.values())
    if max_s == min_s:
        return {k: 1.0 if max_s > 0 else 0.0 for k in scores}
    return {k: (v - min_s) / (max_s - min_s) for k, v in scores.items()}
