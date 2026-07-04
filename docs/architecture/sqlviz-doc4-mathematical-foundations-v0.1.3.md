# SQLviz — Mathematical & Statistical Foundations
**Version:** v0.1.1 (Draft)
**Status:** Work in Progress
**Last Updated:** 2026-06-08
**Changes from v0.1.0:** Added negative rules, YAML structure, Feature Vector versioning,
corrected softmax terminology, moved Learning and VSS to future versions,
added extensibility design for future features.

---

## Preface

This document defines the mathematical and statistical foundations
of the SQLviz Inference Engine.

Every inference SQLviz makes is based on these foundations.
No magic. No black boxes. No "the algorithm decided."
Every decision has a mathematical justification.

> "Every inference has a mathematical justification."
> This is a law of SQLviz, not a guideline.

This document is a prerequisite for:
- DOC 5 — Inference Engine Architecture
- DOC 8 — Construction Plan
- Any developer implementing inference engines

### Implementation Strategy

```
V0 (now):
→ 39 explicit features (well-measured)
→ Rule-based scoring with weights in YAML
→ Negative rules (penalties)
→ Fingerprint exact match
→ No learning yet

V1 (v0.2):
→ 128-dimension feature vector
→ Learning Engine (Bayesian + decay)
→ Benchmark-calibrated weights

V2 (v0.3+):
→ Vector similarity search (DuckDB VSS)
→ Thompson Sampling
→ Collective learning patterns

Why this order:
→ Get rule_score working well first
→ Build benchmark with 100-300 cases
→ Calibrate weights with real data
→ Only then add learning on top
```

---

## 1. Scoring Architecture

### 1.1 Normalized Score (not probability)

Every inference in SQLviz produces a normalized score, not a true probability.

```
normalized_score(C | features) ∈ [0.0, 1.0]

Where:
    C        = chart type or intent being evaluated
    features = feature vector extracted from SQL and data

Important distinction:
    normalized_score(Line) = 0.716 means:
    "Line has the highest relative score among candidates"
    NOT "71.6% probability that Line is correct"

True probability would require:
    → Calibrated training data
    → Verified on held-out benchmark
    → Currently not available in V0

In V0 we use:
    raw_score       → weighted sum of features
    normalized_score → raw scores scaled to [0,1]
    confidence_gap  → normalized_score(best) - normalized_score(second_best)
```

### 1.2 Score Normalization (min-max)

For V0, use min-max normalization instead of softmax:

```
normalized_score(C) = (raw_score(C) - min_score) / (max_score - min_score)

Where:
    min_score = min raw score across all candidates
    max_score = max raw score across all candidates

This is honest: scores are relative rankings, not probabilities.
```

### 1.3 Softmax (V1+)

When enough benchmark data exists to justify probabilistic interpretation:

```
softmax(sᵢ) = exp(sᵢ) / Σⱼ exp(sⱼ)

Example:
    raw scores:  Line=2.8, Bar=1.4, Pie=0.3, Table=0.1
    exp values:  16.44, 4.05, 1.35, 1.11
    sum:         22.95

    normalized:  Line=0.716, Bar=0.176, Pie=0.059, Table=0.048
    Sum = 1.000 ✓

Note: Values are normalized_scores, not true probabilities
until calibrated against benchmark data.
```

```python
import math

def softmax(scores: dict[str, float]) -> dict[str, float]:
    """Numerically stable softmax using max subtraction."""
    max_score = max(scores.values())
    exp_scores = {k: math.exp(v - max_score) for k, v in scores.items()}
    total = sum(exp_scores.values())
    return {k: v / total for k, v in exp_scores.items()}

def min_max_normalize(scores: dict[str, float]) -> dict[str, float]:
    """V0 normalization — honest relative ranking."""
    min_s = min(scores.values())
    max_s = max(scores.values())
    if max_s == min_s:
        return {k: 1.0 for k in scores}
    return {k: (v - min_s) / (max_s - min_s) for k, v in scores.items()}
```

### 1.4 Confidence Gap

```
confidence_gap = normalized_score(best) - normalized_score(second_best)

Thresholds:
    gap > 0.60 → high confidence → show only best result
    gap > 0.30 → medium confidence → show best + one alternative
    gap < 0.30 → low confidence → show best + two alternatives + explanation
```

---

## 2. Feature Vectors

### 2.1 Design Principles for Extensibility

The feature vector is designed to be extended without breaking existing code.

```
Rules for adding new features:
1. Always append to the end of the vector
   Never insert in the middle — breaks existing models

2. Use reserved dimensions for planned features
   Prevents index conflicts when features are added

3. New features start as 0.0 (neutral)
   Existing scoring is not affected

4. Document every dimension here
   No undocumented dimensions allowed

5. Version the feature vector
   V0 = dimensions 0-38 (active)
   V1 = dimensions 0-127 (active)
   Reserved = dimensions 38-127 in V0
```

### 2.2 Feature Vector V0 — 38 Dimensions (MVP)

> Note: this section originally specified 35 dimensions (0-34).
> The Result Shape features (dims 35-37, Addendum A3 below) were
> added during peer review and are part of the V0 baseline.
> The active V0 range is **0-38 (39 dimensions)**, not 0-34 or 0-37.
> (35 was the original design; 38 was the count after Addendum A3
> added Result Shape features; 39 is final after Section A4/16.2's
> trend_direction. This document and DOC 5 now both say 39 — see
> Appendix C below for the full version history.)

Active in V0. Well-measured, explicit, testeable.

```
Index  Range    Feature                        Notes
──────────────────────────────────────────────────────────────────
SQL Structural Features (0-17):
0      {0,1}   has_group_by
1      {0,1}   has_order_by
2      {0,1}   has_order_by_desc
3      {0,1}   has_limit
4      {0,1}   has_aggregation                (any agg function)
5      {0,1}   has_sum
6      {0,1}   has_count
7      {0,1}   has_avg
8      {0,1}   has_window_function
9      {0,1}   has_cte
10     {0,1}   has_join
11     {0,1}   has_where
12     [0,1]   group_by_column_count/5        (normalized, cap 1.0)
13     [0,1]   select_column_count/10         (normalized, cap 1.0)
14     {0,1}   has_subquery
15     {0,1}   has_partition_by
16     {0,1}   has_case_when
17     {0,1}   has_distinct

Column Type Features (18-24):
18     {0,1}   has_date_column
19     {0,1}   has_numeric_column
20     {0,1}   has_string_column
21     [0,1]   numeric_column_ratio           (numeric/total cols)
22     [0,1]   date_column_ratio
23     {0,1}   has_single_numeric_column      (KPI signal)
24     {0,1}   has_two_numeric_columns        (correlation signal)

Data Statistics (25-29):
25     [0,1]   row_count/10000                (normalized, cap 1.0)
26     [0,1]   cardinality_ratio              (unique/total rows)
27     [0,1]   temporal_cardinality/366       (date range coverage)
28     [0,1]   trend_strength                 (R²)
29     {0,1}   has_outliers                   (Z-score > 3)

Semantic Features (30-34):
30     {0,1}   has_revenue_metric
31     {0,1}   has_temporal_dimension
32     {0,1}   has_geographic_dimension
33     {0,1}   has_kpi_pattern                (1 row, 1 numeric col)
34     {0,1}   has_ranking_pattern            (ORDER DESC + LIMIT)
```

### 2.3 Feature Vector V1 — 128 Dimensions (V1+)

Extends V0. Dimensions 0-38 are identical to V0.

```
Index  Range    Feature                        Notes
──────────────────────────────────────────────────────────────────
(0-34 same as V0)

Extended SQL Features (35-49):
35     [0,1]   join_count/3
36     {0,1}   has_max_min
37     {0,1}   has_coalesce_nullif
38     {0,1}   has_date_trunc_extract
39     {0,1}   has_string_agg
40     {0,1}   has_array_agg
41-49  reserved

Extended Column Features (50-63):
50     {0,1}   has_boolean_column
51     [0,1]   string_column_ratio
52     {0,1}   has_id_column                  (semantic: identifier)
53     {0,1}   has_status_column              (semantic: status/state)
54-63  reserved

Extended Data Statistics (64-95):
64     [0,1]   max_category_count/100
65     [0,1]   numeric_skewness_normalized
66     [0,1]   numeric_kurtosis_normalized
67     [0,1]   seasonality_score
68     [0,1]   coefficient_of_variation
69     [0,1]   correlation_max                (max Pearson r)
70     [0,1]   hhi_score                      (Herfindahl Index)
71-95  reserved

Extended Semantic Features (96-127):
96     {0,1}   has_customer_entity
97     {0,1}   has_product_entity
98     {0,1}   has_funnel_pattern
99     {0,1}   has_cohort_pattern
100    {0,1}   has_retention_pattern
101    {0,1}   has_comparison_pattern
102    {0,1}   has_distribution_pattern
103-127 reserved
```

---

## 3. SQL Fingerprinting

### 3.1 Definition

A fingerprint is a normalized string that represents
the analytical pattern of a SQL query, independent of:
- Table names and column names
- Specific values
- Language (Spanish, English, etc.)

```
SQL 1: SELECT month, SUM(revenue) FROM sales GROUP BY month
SQL 2: SELECT fecha, SUM(ventas) FROM ventas GROUP BY fecha
SQL 3: SELECT d, SUM(v) FROM t GROUP BY d

All three → fingerprint: TIME_SUM_GROUP1_ORDER_ASC
```

### 3.2 Fingerprint Generation

```python
def generate_fingerprint(ast: sqlglot.Expression) -> str:
    patterns = []

    if _has_temporal_dimension(ast):
        patterns.append("TIME")

    agg_funcs = list(ast.find_all(sqlglot.exp.AggFunc))
    if agg_funcs:
        agg_names = sorted({type(a).__name__.upper() for a in agg_funcs})
        patterns.append("_".join(agg_names))

    if ast.find(sqlglot.exp.Group):
        group_count = _count_group_by_columns(ast)
        patterns.append(f"GROUP{group_count}")

    if ast.find(sqlglot.exp.Order):
        patterns.append("ORDER_DESC" if _has_order_by_desc(ast) else "ORDER_ASC")

    if ast.find(sqlglot.exp.Limit):
        patterns.append("LIMIT")

    if ast.find(sqlglot.exp.Window):
        patterns.append("WINDOW")

    if _is_single_metric(ast):
        patterns.append("KPI")

    return "_".join(patterns) if patterns else "UNKNOWN"

# Examples:
# SELECT SUM(revenue)                                → SUM_KPI
# SELECT month, SUM(rev) GROUP BY month              → TIME_SUM_GROUP1_ORDER_ASC
# SELECT cat, COUNT(*) GROUP BY cat ORDER DESC LIMIT → COUNT_GROUP1_ORDER_DESC_LIMIT
# SELECT a, b FROM t                                 → UNKNOWN
```

### 3.3 Fingerprint Lookup (V0 — exact match)

```python
# V0: exact fingerprint match
def lookup_historical(fingerprint: str, brain_conn) -> dict:
    result = brain_conn.execute("""
        SELECT chart_type, acceptance_rate, sample_count
        FROM fingerprint_patterns
        WHERE fingerprint = ?
        ORDER BY acceptance_rate DESC
        LIMIT 5
    """, [fingerprint]).fetchall()
    return result
```

### 3.4 Vector Similarity (V1+ only)

```
cosine_similarity(F1, F2) = (F1 · F2) / (|F1| × |F2|)

Threshold: similarity > 0.85 → patterns are similar

Implementation: DuckDB VSS extension
    INSTALL vss; LOAD vss;
    CREATE INDEX ON sql_patterns USING HNSW (vector);

NOT implemented in V0.
Reason: requires sufficient data volume to be meaningful.
Added in V1 after benchmark validation.
```

---

## 4. Weighted Linear Scoring

### 4.1 Positive Score

```
raw_score(intent) = Σᵢ wᵢ × fᵢ

Where:
    wᵢ = weight of feature i (from YAML, not hardcoded)
    fᵢ = value of feature i ∈ [0.0, 1.0]
    Σᵢ wᵢ = 1.0 (weights sum to 1)
```

### 4.2 Negative Rules (Penalties) — CRITICAL

Penalties prevent wrong charts from scoring falsely high.
Without penalties, Pie chart would appear in rankings,
temporal data, and high-cardinality scenarios.

```
penalized_score(C) = raw_score(C) - Σⱼ pⱼ × vⱼ

Where:
    pⱼ = penalty weight for condition j
    vⱼ = value of penalty condition j ∈ {0.0, 1.0}

Final score is clamped to [0.0, 1.0]:
    final = max(0.0, min(1.0, penalized_score(C)))
```

**Pie Chart Penalties:**
```
pie_score =
    + 0.40 × composition_intent
    + 0.30 × low_cardinality
    + 0.20 × part_to_whole_pattern
    + 0.10 × category_count_3_to_8
    - 0.50 × high_cardinality        ← PENALTY
    - 0.40 × ranking_intent          ← PENALTY
    - 0.40 × temporal_dimension      ← PENALTY
    - 0.30 × category_count_gt_8     ← PENALTY
    - 0.20 × correlation_intent      ← PENALTY
```

**KPI Chart Penalties:**
```
kpi_score =
    + 0.50 × is_single_metric
    + 0.30 × has_aggregation
    + 0.20 × no_group_by
    - 0.80 × has_group_by            ← PENALTY (KPI needs no dimension)
    - 0.60 × has_multiple_rows       ← PENALTY (KPI needs 1 row)
    - 0.40 × has_temporal_dimension  ← PENALTY (use Line instead)
```

**Scatter Chart Penalties:**
```
scatter_score =
    + 0.50 × has_two_numeric_columns
    + 0.30 × correlation_intent
    + 0.20 × no_group_by
    - 0.70 × has_single_numeric_column ← PENALTY
    - 0.50 × has_temporal_dimension    ← PENALTY (use Line instead)
    - 0.40 × has_aggregation           ← PENALTY (aggregated data ≠ scatter)
```

**Line Chart Penalties:**
```
line_score =
    + 0.95 × trend_intent
    + 0.05 × comparison_intent
    - 0.60 × no_temporal_dimension    ← PENALTY
    - 0.40 × low_row_count_lt_3       ← PENALTY (need trend to exist)
    - 0.30 × high_cardinality_string  ← PENALTY (too many categories)
```

**Bar Chart Penalties:**
```
bar_score =
    + 0.90 × comparison_intent
    + 0.40 × ranking_intent
    + 0.15 × trend_intent
    - 0.30 × category_count_gt_20    ← PENALTY (too many bars)
    - 0.20 × has_two_numeric_only    ← PENALTY (use Scatter instead)
```

### 4.3 Combined Score (V1+)

```
final_score(C) = α × rule_score(C) + β × historical_score(C)

V0:  α=1.00, β=0.00  (no history yet)
V1:  α=0.80, β=0.20  (after 100 samples)
V1+: α=0.70, β=0.30  (after 1000 samples)

Transitions happen automatically based on sample count in brain.duckdb.
```

---

## 5. Intent Scoring

### 5.1 The 12 Intents

```
Trend        → How does a metric change over time?
Comparison   → How do categories compare?
Ranking      → What are the top/bottom N items?
Distribution → How are values distributed?
Correlation  → Are two metrics related?
Composition  → What is the part-to-whole breakdown?
KPI          → What is the current value of a metric?
Anomaly      → Are there unexpected values?
Cohort       → How do groups behave over time?
Retention    → Do users/customers return?
Funnel       → Where do users drop off?
Detail       → Show me the raw data
```

### 5.2 Intent Scoring Formulas (V0 weights)

All weights live in `intent_rules.yaml`, not hardcoded.

**Trend:**
```
score(Trend) =
    + 0.40 × has_temporal_dimension
    + 0.25 × has_group_by
    + 0.20 × has_aggregation
    + 0.10 × has_temporal_ordering
    + 0.05 × temporal_cardinality_score
```

**Comparison:**
```
score(Comparison) =
    + 0.35 × has_categorical_dimension
    + 0.30 × has_aggregation
    + 0.20 × has_group_by
    + 0.10 × (1 - has_temporal_dimension)
    + 0.05 × category_count_score
```

**Ranking:**
```
score(Ranking) =
    + 0.40 × has_order_by_desc
    + 0.30 × has_limit
    + 0.20 × has_aggregation
    + 0.10 × has_group_by

Boost multiplier: 1.50 if has_order_by_desc AND has_limit
```

**KPI:**
```
score(KPI) =
    + 0.50 × is_single_metric
    + 0.30 × has_aggregation
    + 0.20 × (1 - has_group_by)
```

**Distribution:**
```
score(Distribution) =
    + 0.40 × high_cardinality_numeric
    + 0.30 × (1 - has_temporal_dimension)
    + 0.20 × (1 - has_group_by)
    + 0.10 × skewness_score
```

**Correlation:**
```
score(Correlation) =
    + 0.50 × has_two_numeric_columns
    + 0.30 × (1 - has_group_by)
    + 0.20 × (1 - has_aggregation)
```

**Composition:**
```
score(Composition) =
    + 0.40 × low_cardinality_categorical
    + 0.30 × has_aggregation
    + 0.20 × part_of_whole_pattern
    + 0.10 × category_count_between_3_and_8
```

**Detail:**
```
score(Detail) =
    + 0.50 × no_aggregation
    + 0.30 × no_group_by
    + 0.20 × high_column_count

Detail is the fallback when no other intent scores high.
```

### 5.3 Intent Vector

```
intent_scores = {Trend:0.99, Comparison:0.35, ...}
intent_vector = min_max_normalize(intent_scores)  # V0
             OR softmax(intent_scores)             # V1+
```

---

## 6. Chart Scoring with Affinity Matrix

### 6.1 Affinity Matrix

```
score(chart C) = Σᵢ affinity(C, intentᵢ) × normalized_score(intentᵢ)

Full affinity matrix:

              Trend  Comp  Rank  Dist  Corr  Comp  KPI  Anom  Detail
Line          0.95   0.10  0.00  0.05  0.00  0.00  0.00 0.20  0.05
Area          0.85   0.05  0.00  0.10  0.00  0.00  0.00 0.15  0.05
Bar           0.15   0.90  0.40  0.20  0.00  0.20  0.00 0.10  0.10
Bar_Horiz     0.05   0.60  0.95  0.10  0.00  0.10  0.00 0.05  0.05
Pie           0.00   0.30  0.00  0.80  0.00  0.90  0.00 0.00  0.00
KPI           0.00   0.00  0.00  0.00  0.00  0.00  1.00 0.00  0.00
Scatter       0.05   0.10  0.00  0.40  0.95  0.00  0.00 0.20  0.00
Multiline     0.90   0.30  0.00  0.05  0.20  0.00  0.00 0.25  0.00
Table         0.10   0.20  0.20  0.20  0.10  0.10  0.10 0.10  0.95
Histogram     0.10   0.10  0.00  0.95  0.10  0.00  0.00 0.15  0.05
Boxplot       0.05   0.40  0.00  0.80  0.30  0.00  0.00 0.40  0.00
Heatmap       0.20   0.50  0.00  0.60  0.70  0.00  0.00 0.30  0.00
Treemap       0.00   0.40  0.20  0.50  0.00  0.80  0.00 0.00  0.00
Funnel        0.00   0.00  0.00  0.00  0.00  0.00  0.00 0.00  0.00
Waterfall     0.40   0.50  0.00  0.00  0.00  0.30  0.00 0.00  0.00
Combo         0.70   0.50  0.20  0.00  0.20  0.00  0.00 0.10  0.00
Bubble        0.10   0.40  0.30  0.30  0.60  0.00  0.00 0.10  0.00
```

### 6.2 After Penalties

```
final_chart_score(C) = affinity_score(C) - penalties(C)
final_chart_score(C) = max(0.0, final_chart_score(C))

Then normalize across all candidates.
```

---

## 7. Statistical Features

### 7.1 Trend Strength (R²)

```
Given: (t₁,y₁), ..., (tₙ,yₙ)

b = Σ(tᵢ-t̄)(yᵢ-ȳ) / Σ(tᵢ-t̄)²
a = ȳ - b×t̄

R² = 1 - Σ(yᵢ-ŷᵢ)² / Σ(yᵢ-ȳ)²

R² > 0.8 → strong trend → prefer Line
R² > 0.5 → moderate trend
R² < 0.3 → no clear trend → Bar might be better
```

### 7.2 Skewness

```
skewness = (1/n) × Σ((xᵢ - μ) / σ)³

|skewness| < 1.0  → symmetric → Bar chart fine
|skewness| > 2.0  → highly skewed → Histogram preferred

Normalized for feature vector:
    skewness_normalized = 1 / (1 + exp(-|skewness|/2))
```

### 7.3 Kurtosis

```
kurtosis = (1/n) × Σ((xᵢ - μ) / σ)⁴ - 3

kurtosis ≈ 0   → normal distribution
kurtosis > 3   → heavy tails → Boxplot preferred
kurtosis < -1  → flat distribution → Histogram preferred

Normalized:
    kurtosis_normalized = 1 / (1 + exp(-kurtosis/3))
```

### 7.4 Cardinality Ratio

```
cardinality_ratio = unique_values / total_rows

ratio ≈ 1.0  → identifier (user_id) → not a dimension
ratio < 0.05 → low cardinality → good Dropdown filter
ratio < 0.50 → medium → good GROUP BY dimension
ratio > 0.80 → high → likely identifier
```

### 7.5 Seasonality (Autocorrelation)

```
r(k) = Σ(yᵢ-ȳ)(yᵢ₊ₖ-ȳ) / Σ(yᵢ-ȳ)²

Lags: k=7 (weekly), k=12 (monthly), k=4 (quarterly)
seasonality_score = max(|r(7)|, |r(12)|, |r(4)|)

score > 0.7 → strong seasonality → note in insights
score > 0.4 → moderate seasonality
score < 0.2 → no seasonality
```

### 7.6 Outlier Detection

```
z(xᵢ) = (xᵢ - μ) / σ

|z| > 3.0 → severe outlier
|z| > 2.5 → moderate outlier (insight threshold)

has_outliers = count(|z| > 3) / n > 0.01
```

### 7.7 Pearson Correlation

```
r(X,Y) = Σ(xᵢ-x̄)(yᵢ-ȳ) / √[Σ(xᵢ-x̄)² × Σ(yᵢ-ȳ)²]

r > +0.7  → strong positive → Scatter chart
r < -0.7  → strong negative → notable insight
|r| < 0.3 → no correlation

correlation_max = max |r(Xᵢ,Xⱼ)| for all numeric column pairs
```

### 7.8 Herfindahl-Hirschman Index

```
HHI = Σᵢ (sᵢ)²    where sᵢ = yᵢ / Σyⱼ

HHI > 0.50 → highly concentrated → Pie appropriate
HHI > 0.25 → moderately concentrated → Bar appropriate
HHI < 0.10 → evenly distributed → Bar Horizontal

Example:
    [A:70%, B:20%, C:7%, D:3%]
    HHI = 0.49 + 0.04 + 0.005 + 0.001 = 0.536
    → highly concentrated
    → Insight: "Category A dominates with 70% share"
```

---

## 8. Insight Mathematics

### 8.1 Anomaly Detection

```
z(xᵢ) = (xᵢ - μ) / σ

Insight when: max(|z|) > 2.5 AND outlier_count/n < 0.05
```

### 8.2 Trend Direction and Growth

```
b > 0 AND R² > 0.5 → upward trend
b < 0 AND R² > 0.5 → downward trend
R² < 0.3           → no clear trend

Period growth:  growth% = (y_last - y_first) / |y_first| × 100
CAGR:          CAGR = (y_last/y_first)^(1/n) - 1
```

### 8.3 Pareto Detection

```
Sort descending. Find smallest k where:
    Σᵢ₌₁ᵏ yᵢ / Σᵢ₌₁ⁿ yᵢ ≥ 0.80

pareto_ratio = k/n < 0.25 → Pareto confirmed
```

### 8.4 Multi-Panel Insights

```
Cross-panel correlation:
    r(P₁, P₂) = pearson_r(y_P1, y_P2)

Divergence insight:
    trend(P₁)=UP AND trend(P₂)=DOWN AND |r|>0.70
    → "Revenue growing but margin declining"

Lagged correlation:
    r_lag(k) = pearson_r(y[k:], z[:-k])
    max(|r_lag|) > 0.80 at lag k*
    → "Ad spend leads revenue by k* periods"
```

### 8.5 Funnel Drop-off

```
dropoff(i) = (cᵢ₋₁ - cᵢ) / cᵢ₋₁
worst_stage = argmax(dropoff(i))
Insight: "Biggest drop-off at {worst_stage}: {dropoff:.1%} lost"
```

### 8.6 Retention Rate

```
retention(t,k) = users_retained(t,k) / users_acquired(t)
churn(k) = 1 - avg_retention(k)
```

---

## 9. Layout Mathematics

### 9.1 Panel Importance Score

```
importance(P) =
    0.40 × degree_centrality(P) +
    0.30 × intent_strength(P) +
    0.20 × metric_importance(P) +
    0.10 × position_preference(P)
```

### 9.2 Grid Span (12-column CSS Grid)

```
importance > 0.80 → col_span=12, row_span=2  (featured)
importance > 0.60 → col_span=12, row_span=1  (primary)
importance > 0.40 → col_span=6,  row_span=1  (secondary)
importance > 0.20 → col_span=4,  row_span=1  (supporting)
importance ≤ 0.20 → col_span=3,  row_span=1  (KPI/small)

Override rules (always applied):
    KPI    → col_span=3,  row_span=1
    TABLE  → col_span=12, row_span=2
    LINE   → minimum col_span=8
    SCATTER → minimum col_span=6, row_span=2
```

---

## 10. Dashboard Genome Similarity

```
G = genome vector (32 dimensions)
    [chart_type_distribution, intent_distribution,
     metric_distribution, dimension_distribution,
     structural_features]

similarity(G₁, G₂) = cosine_similarity(G₁, G₂)

similarity > 0.80 → reuse layout and insights
similarity > 0.60 → suggest panel additions
```

---

## 11. Dimension Importance

```
importance(D) =
    0.35 × cross_panel_frequency(D) +
    0.25 × (1 - cardinality_ratio(D)) +
    0.20 × semantic_weight(D) +
    0.15 × user_interaction_rate(D) +
    0.05 × position_score(D)

importance > 0.70 → Global filter
importance > 0.40 → Local filter
importance ≤ 0.40 → No filter (just GROUP BY)
```

---

## 12. Query Rewrite Mathematics

```
KPI rewrite:
    π_{d,agg(m)}(R) → π_{agg(m)}(R)
    Remove GROUP BY, keep aggregation

Growth rewrite:
    Add LAG window function:
    growth(t) = y(t) - y(t-1)
    growth_pct(t) = (y(t) - y(t-1)) / y(t-1)

Geography rewrite:
    Replace temporal dimension with geographic dimension:
    π_{d_temporal,agg(m)}(R) → π_{d_geo,agg(m)}(R)

Share rewrite:
    Add window total:
    share(i) = yᵢ / SUM(SUM(metric)) OVER ()
```

---

## 13. Learning Engine (V1+)

NOT implemented in V0.
Requires: stable rule_score + benchmark with 100+ cases first.

### 13.1 Bayesian Update

```
P(C|fingerprint) =
    (count_accepted(C,fp) + α) / (count_total(fp) + α×|C|)

α = 1.0 (Laplace smoothing)
```

### 13.2 Confidence Decay

```
weight(t) = exp(-λ × Δdays)    λ=0.001
```

### 13.3 Thompson Sampling

```
θc ~ Beta(acceptances+1, rejections+1)
Select: argmax(θc)
```

---

## 14. YAML Rules Structure

All weights and thresholds live in YAML files.
Never hardcoded in Python.

```
packages/sqlviz-inference/rules/
├── intent_rules.yaml
├── chart_affinity_matrix.yaml
├── chart_penalties.yaml
├── feature_weights.yaml
├── metric_rules.yaml
├── dimension_rules.yaml
└── thresholds.yaml
```

### intent_rules.yaml

```yaml
trend:
  weights:
    has_temporal_dimension: 0.40
    has_group_by: 0.25
    has_aggregation: 0.20
    has_temporal_ordering: 0.10
    temporal_cardinality_score: 0.05

ranking:
  weights:
    has_order_by_desc: 0.40
    has_limit: 0.30
    has_aggregation: 0.20
    has_group_by: 0.10
  boosts:
    order_by_desc_and_limit: 1.50

kpi:
  weights:
    is_single_metric: 0.50
    has_aggregation: 0.30
    no_group_by: 0.20
```

### chart_penalties.yaml

```yaml
pie:
  penalties:
    high_cardinality: 0.50
    ranking_intent: 0.40
    temporal_dimension: 0.40
    category_count_gt_8: 0.30
    correlation_intent: 0.20

kpi:
  penalties:
    has_group_by: 0.80
    has_multiple_rows: 0.60
    has_temporal_dimension: 0.40

scatter:
  penalties:
    has_single_numeric_column: 0.70
    has_temporal_dimension: 0.50
    has_aggregation: 0.40
```

### thresholds.yaml

```yaml
confidence:
  high: 0.60
  low: 0.30

similarity:
  fingerprint_match: 1.0
  vector_match: 0.85      # V1+ only

anomaly:
  z_score: 2.5

pareto:
  share_threshold: 0.80
  ratio_max: 0.25

dimension:
  global_filter: 0.70
  local_filter: 0.40

hhi:
  high_concentration: 0.50
  moderate_concentration: 0.25

learning:
  α_rule_no_history: 1.00
  α_rule_100_samples: 0.80
  α_rule_1000_samples: 0.70
  decay_rate: 0.001
```

---

## Appendix A — Notation Reference

```
Symbol    Meaning
──────────────────────────────────────
P(A)      Probability of event A
P(A|B)    Conditional probability
Σ         Summation
μ         Mean
σ         Standard deviation
∈         Element of
ℝ         Real numbers
exp(x)    e raised to power x
~         Distributed as
·         Dot product
R²        Coefficient of determination
CAGR      Compound Annual Growth Rate
HHI       Herfindahl-Hirschman Index
argmax    Index of maximum value
```

## Appendix B — Complete Hyperparameter Reference

```
Parameter                Default  Version  Description
──────────────────────────────────────────────────────────────────
α (rule weight)          1.00     V0       Rule score weight
α (rule weight)          0.80     V1       After 100 samples
α (rule weight)          0.70     V1+      After 1000 samples
β (hist weight)          0.00     V0       Historical score weight
β (hist weight)          0.20     V1       After 100 samples
β (hist weight)          0.30     V1+      After 1000 samples
λ (decay rate)           0.001    V1+      Decay per day
α_laplace                1.0      V1+      Laplace smoothing
similarity_exact         1.0      V0       Fingerprint exact match
similarity_vector        0.85     V1+      Min cosine similarity
anomaly_z_threshold      2.5      V0       Z-score for anomaly insight
confidence_high          0.60     V0       Single recommendation
confidence_low           0.30     V0       Show alternatives
genome_similarity_high   0.80     V1+      Reuse dashboard layout
genome_similarity_med    0.60     V1+      Suggest panel additions
dimension_global_thresh  0.70     V0       Global filter threshold
dimension_local_thresh   0.40     V0       Local filter threshold
hhi_high                 0.50     V0       High concentration
hhi_moderate             0.25     V0       Moderate concentration
correlation_strong       0.70     V0       Strong correlation insight
correlation_lagged       0.80     V1+      Lagged correlation insight
pareto_threshold         0.80     V0       80% share threshold
pareto_ratio_max         0.25     V0       Max items for Pareto
funnel_dropoff_notable   0.30     V0       Notable drop-off rate
kurtosis_heavy_tail      3.0      V1+      Heavy tail detection
kurtosis_flat            -1.0     V1+      Flat distribution
```

## Appendix C — Feature Vector Version History

> Note: this appendix appears here (end of the v0.1.1 base text)
> for historical document structure, but reflects the FINAL count
> after the v0.1.2 and v0.1.3 addendums below (Result Shape
> features + trend_direction). It is correct as written — 39, not
> 35 or 38 — because it was updated during the same correction pass
> that fixed those addendums' internal numbering.

```
Version  Dimensions  Status    Description
─────────────────────────────────────────────────
V0       0-38        Active    39 explicit, well-measured features
V1       0-127       Planned   128 dimensions, extended statistics
V2       TBD         Future    Embeddings, learned representations

Rule: New features always appended.
      Never inserted in the middle.
      Reserved dimensions prevent index conflicts.
```

---

*SQLviz Mathematical & Statistical Foundations — v0.1.1*
*"Every inference has a mathematical justification."*
*"No black boxes. No magic. Just mathematics."*

---

# Addendum v0.1.2 — Corrections and Improvements

## A1. Min-Max Fallback Problem

Min-max normalization creates an artificial winner even when all scores are weak.

```
Problem example:
    Line = 0.08, Bar = 0.06, Pie = 0.04
    After min-max: Line = 1.0 (artificial winner)
    SQLviz would show Line with high confidence — WRONG

Solution — track four values:

raw_score          → absolute strength of the score
normalized_score   → relative ranking among candidates
quality            → classification of raw_score strength
confidence_gap     → normalized_score(best) - normalized_score(second)

Quality classification:
    raw_score > 0.70 → quality = "high"
    raw_score > 0.35 → quality = "medium"
    raw_score ≤ 0.35 → quality = "low" → trigger fallback

Fallback rule:
    if best_raw_score < minimum_acceptance_threshold:
        chart = Table
        intent = Detail
        confidence_gap = 0.0
        quality = "low"
        fallback_applied = True
```

## A2. Confidence vs Quality — Formal Separation

These are different concepts. SQLviz must report both.

```
quality       = absolute measure of how strong the best score is
                quality = best_raw_score

confidence_gap = relative measure of how much better best is vs second
                confidence_gap = norm_score(best) - norm_score(second_best)

Four combinations:

Case 1: quality=high, confidence_gap=high
    Line=0.91, Bar=0.39
    → Very certain. Show only Line.

Case 2: quality=high, confidence_gap=low
    Line=0.90, Bar=0.88
    → Both are good. Show both. Let user decide.

Case 3: quality=low, confidence_gap=high
    Line=0.35, Bar=0.05
    → Line wins but barely acceptable.
    → Show Line with warning: "Low confidence inference"

Case 4: quality=low, confidence_gap=low
    Line=0.20, Bar=0.18
    → All scores are weak. Apply fallback → Table.

Display rules:
    Case 1 → show winner only
    Case 2 → show winner + alternatives
    Case 3 → show winner + low confidence warning
    Case 4 → show Table + explanation
```

## A3. Feature Vector V0 Updated — 38 Dimensions

Three new features added to improve KPI and Table detection.

```
Index  Range    Feature                        Notes
──────────────────────────────────────────────────────────────────
(0-34 same as before)

Result Shape Features (35-37):
35     {0,1}   result_row_count_is_1          KPI signal (strong)
36     {0,1}   result_column_count_is_1       KPI signal (strong)
37     {0,1}   result_is_wide_table           Table signal
                                              (many columns, many rows)

Trend Direction Feature (38):
38     [0,1]   trend_direction                 0.0=declining, 0.5=flat,
                                              1.0=growing. Added in a
                                              later review round
                                              (see Section A4 below) —
                                              kept separate from
                                              trend_strength (dim 28,
                                              R², magnitude only)
                                              because magnitude and
                                              direction are independent
                                              concepts.
```

> **V0 total: 39 dimensions (indices 0-38).** Earlier drafts of
> this document said "38" — that count predates dim 38
> (`trend_direction`) being added. This is now corrected
> everywhere in this document and in DOC 5.

```python
def compute_result_shape_features(data: list[dict]) -> dict:
    """
    Compute result shape features from query output.
    These are the strongest signals for KPI detection.
    """
    if not data:
        return {35: 0.0, 36: 0.0, 37: 0.0}

    row_count = len(data)
    col_count = len(data[0]) if data else 0

    return {
        35: 1.0 if row_count == 1 else 0.0,
        36: 1.0 if col_count == 1 else 0.0,
        37: 1.0 if row_count > 20 and col_count > 5 else 0.0
    }
```

Updated KPI scoring with new features:
```
score(KPI) =
    + 0.40 × result_row_count_is_1      ← new, strongest signal
    + 0.30 × result_column_count_is_1   ← new, strong signal
    + 0.20 × has_aggregation
    + 0.10 × (1 - has_group_by)
    - 0.80 × has_group_by               ← penalty
    - 0.60 × result_row_count_gt_1      ← penalty
```

## A4. Fallback Rules — Formalized

```yaml
# rules/fallback_rules.yaml

chart:
  min_raw_score: 0.35
  default: table
  message: "Low confidence — showing raw data"

intent:
  min_raw_score: 0.30
  default: detail
  message: "Intent unclear — defaulting to detail view"

quality_thresholds:
  high: 0.70
  medium: 0.35
  low: 0.00

display_rules:
  quality_high_gap_high:
    action: show_winner_only
    alternatives: 0

  quality_high_gap_low:
    action: show_winner_with_alternatives
    alternatives: 2

  quality_low_gap_high:
    action: show_winner_with_warning
    warning: "Low confidence inference"
    alternatives: 1

  quality_low_gap_low:
    action: apply_fallback
    alternatives: 0
```

## A5. Complete YAML Rules Structure

```
packages/sqlviz-inference/rules/
├── intent_rules.yaml         ← intent scoring weights
├── chart_affinity_matrix.yaml ← affinity scores per intent
├── chart_penalties.yaml      ← penalty rules per chart
├── fallback_rules.yaml       ← fallback thresholds and actions
├── thresholds.yaml           ← global thresholds
├── metric_rules.yaml         ← semantic metric detection
├── dimension_rules.yaml      ← semantic dimension detection
└── feature_vector_v0.yaml    ← feature vector definition
```

### feature_vector_v0.yaml

```yaml
# Defines the 39-dimension feature vector for V0
# Never hardcode feature indices in Python
# Always reference by name from this file

version: "v0"
dimensions: 39

features:
  # SQL Structural Features
  has_group_by:               {index: 0,  type: binary}
  has_order_by:               {index: 1,  type: binary}
  has_order_by_desc:          {index: 2,  type: binary}
  has_limit:                  {index: 3,  type: binary}
  has_aggregation:            {index: 4,  type: binary}
  has_sum:                    {index: 5,  type: binary}
  has_count:                  {index: 6,  type: binary}
  has_avg:                    {index: 7,  type: binary}
  has_window_function:        {index: 8,  type: binary}
  has_cte:                    {index: 9,  type: binary}
  has_join:                   {index: 10, type: binary}
  has_where:                  {index: 11, type: binary}
  group_by_column_count:      {index: 12, type: continuous, normalize: "divide_by_5"}
  select_column_count:        {index: 13, type: continuous, normalize: "divide_by_10"}
  has_subquery:               {index: 14, type: binary}
  has_partition_by:           {index: 15, type: binary}
  has_case_when:              {index: 16, type: binary}
  has_distinct:               {index: 17, type: binary}

  # Column Type Features
  has_date_column:            {index: 18, type: binary}
  has_numeric_column:         {index: 19, type: binary}
  has_string_column:          {index: 20, type: binary}
  numeric_column_ratio:       {index: 21, type: continuous}
  date_column_ratio:          {index: 22, type: continuous}
  has_single_numeric_column:  {index: 23, type: binary}
  has_two_numeric_columns:    {index: 24, type: binary}

  # Data Statistics
  row_count_normalized:       {index: 25, type: continuous, normalize: "divide_by_10000"}
  cardinality_ratio:          {index: 26, type: continuous}
  temporal_cardinality:       {index: 27, type: continuous, normalize: "divide_by_366"}
  trend_strength:             {index: 28, type: continuous}
  has_outliers:               {index: 29, type: binary}

  # Semantic Features
  has_revenue_metric:         {index: 30, type: binary}
  has_temporal_dimension:     {index: 31, type: binary}
  has_geographic_dimension:   {index: 32, type: binary}
  has_kpi_pattern:            {index: 33, type: binary}
  has_ranking_pattern:        {index: 34, type: binary}

  # Result Shape Features (new in v0.1.2)
  result_row_count_is_1:      {index: 35, type: binary}
  result_column_count_is_1:   {index: 36, type: binary}
  result_is_wide_table:       {index: 37, type: binary}

  # Trend Direction Feature (new in v0.1.3 / DOC5 Section 16.2)
  trend_direction:             {index: 38, type: continuous}

reserved:
  start_index: 39  # dim 38 (trend_direction) is now active, see above
  end_index: 127
  note: "Reserved for V1 features. Never use in V0."
```

## A6. Official infer() Output Format

```python
@dataclass
class InferenceResult:
    """
    The complete output of the SQLviz inference pipeline.
    Every field has a mathematical justification.
    """
    # Intent inference
    intent_winner: str           # e.g. "trend"
    intent_raw_score: float      # absolute strength [0.0, 1.0]
    intent_normalized_score: float
    intent_confidence_gap: float
    intent_quality: str          # "high" | "medium" | "low"
    intent_alternatives: list[dict]

    # Chart inference
    chart_winner: str            # e.g. "line"
    chart_raw_score: float
    chart_normalized_score: float
    chart_confidence_gap: float
    chart_quality: str
    chart_alternatives: list[dict]

    # Fallback
    fallback_applied: bool
    fallback_reason: str | None

    # Explainability
    explanation: list[Evidence]
    feature_vector: list[float]
    fingerprint: str

# Example output:
{
    "intent_winner": "trend",
    "intent_raw_score": 0.99,
    "intent_normalized_score": 1.0,
    "intent_confidence_gap": 0.64,
    "intent_quality": "high",
    "intent_alternatives": [
        {"intent": "comparison", "raw_score": 0.35}
    ],

    "chart_winner": "line",
    "chart_raw_score": 0.91,
    "chart_normalized_score": 1.0,
    "chart_confidence_gap": 0.52,
    "chart_quality": "high",
    "chart_alternatives": [
        {"chart": "bar",  "raw_score": 0.39},
        {"chart": "area", "raw_score": 0.35}
    ],

    "fallback_applied": false,
    "fallback_reason": null,

    "explanation": [
        {"signal": "has_temporal_dimension", "weight": 0.40, "value": 1.0, "contribution": 0.40},
        {"signal": "has_group_by",           "weight": 0.25, "value": 1.0, "contribution": 0.25}
    ],
    "fingerprint": "TIME_SUM_GROUP1_ORDER_ASC"
}
```

---

*Updated to v0.1.2 based on peer review.*
*Changes: fallback rules, confidence vs quality separation,*
*feature vector V0 updated to 39 dimensions, YAML structure completed.*

---

# Addendum v0.1.3 — Final Adjustments

## B1. Versioned InferenceResult

Every inference result must carry version metadata.
When YAML weights change, old results are traceable.

```python
@dataclass
class InferenceResult:
    # Versioning — ADDED
    rules_version: str          # e.g. "intent_rules_v0.1.0"
    feature_vector_version: str # e.g. "v0" (39 dims) or "v1" (128 dims)
    engine_version: str         # e.g. "sqlviz-inference-0.1.0"

    # Intent inference
    intent_winner: str
    intent_raw_score: float
    intent_normalized_score: float
    intent_confidence_gap: float
    intent_quality: str         # "high" | "medium" | "low"
    intent_alternatives: list[dict]

    # Chart inference
    chart_winner: str
    chart_raw_score: float
    chart_normalized_score: float
    chart_confidence_gap: float
    chart_quality: str
    chart_alternatives: list[dict]

    # Fallback
    fallback_applied: bool
    fallback_reason: str | None

    # Explainability
    explanation: list[Evidence]  # per-signal contributions
    score_trace: dict            # full scoring trace per engine — ADDED
    feature_vector: list[float]
    fingerprint: str

# Complete output example:
{
    "rules_version": "intent_rules_v0.1.0",
    "feature_vector_version": "v0",
    "engine_version": "sqlviz-inference-0.1.0",

    "intent_winner": "trend",
    "intent_raw_score": 0.99,
    "intent_normalized_score": 1.0,
    "intent_confidence_gap": 0.64,
    "intent_quality": "high",
    "intent_alternatives": [
        {"intent": "comparison", "raw_score": 0.35}
    ],

    "chart_winner": "line",
    "chart_raw_score": 0.91,
    "chart_normalized_score": 1.0,
    "chart_confidence_gap": 0.52,
    "chart_quality": "high",
    "chart_alternatives": [
        {"chart": "bar",       "raw_score": 0.39},
        {"chart": "histogram", "raw_score": 0.28}
    ],

    "fallback_applied": false,
    "fallback_reason": null,

    "explanation": [
        {"signal": "has_temporal_dimension", "weight": 0.40, "value": 1.0, "contribution": 0.40},
        {"signal": "has_group_by",           "weight": 0.25, "value": 1.0, "contribution": 0.25},
        {"signal": "has_aggregation",        "weight": 0.20, "value": 1.0, "contribution": 0.20},
        {"signal": "has_temporal_ordering",  "weight": 0.10, "value": 1.0, "contribution": 0.10},
        {"signal": "temporal_cardinality",   "weight": 0.05, "value": 0.80, "contribution": 0.04}
    ],

    "score_trace": {
        "intent": {
            "trend": {
                "raw_score": 0.99,
                "signals": {
                    "has_temporal_dimension": {"weight": 0.40, "value": 1.0, "contribution": 0.40},
                    "has_group_by":           {"weight": 0.25, "value": 1.0, "contribution": 0.25}
                }
            },
            "comparison": {
                "raw_score": 0.35,
                "signals": {
                    "has_categorical_dimension": {"weight": 0.35, "value": 0.0, "contribution": 0.00},
                    "has_aggregation":           {"weight": 0.30, "value": 1.0, "contribution": 0.30}
                }
            }
        },
        "chart": {
            "line": {
                "affinity_score": 0.91,
                "penalties_applied": [],
                "penalty_total": 0.00,
                "final_score": 0.91
            },
            "pie": {
                "affinity_score": 0.30,
                "penalties_applied": [
                    {"rule": "temporal_dimension", "penalty": 0.40}
                ],
                "penalty_total": 0.40,
                "final_score": 0.00
            }
        }
    },

    "feature_vector": [1.0, 1.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, ...],
    "fingerprint": "TIME_SUM_GROUP1_ORDER_ASC"
}
```

## B2. V0 Chart Types — Fixed Set

V0 implements exactly 8 chart types.
Nothing more. Nothing less.

```
V0 Charts (implemented in v0.1):
    KPI             → 1 row, 1 numeric column
    Line            → temporal dimension + aggregation
    Bar             → categorical comparison
    Bar Horizontal  → ranking + many categories
    Pie             → composition + low cardinality
    Scatter         → two numeric columns, no aggregation
    Table           → detail view, fallback
    Histogram       → distribution of numeric values

V1+ Charts (future):
    Area            → like Line but filled
    Multiline       → multiple metrics over time
    Combo           → Bar + Line combined
    Heatmap         → two dimensions + metric
    Boxplot         → statistical distribution
    Treemap         → hierarchical composition
    Funnel          → funnel/conversion analysis
    Waterfall       → cumulative changes
    Bubble          → Scatter with size dimension
    Cohort          → retention grid
```

Affinity matrix V0 — only 8 chart types:

```
              Trend  Comp  Rank  Dist  Corr  Comp  KPI   Detail
Line          0.95   0.10  0.00  0.05  0.00  0.00  0.00  0.05
Bar           0.15   0.90  0.40  0.20  0.00  0.20  0.00  0.10
Bar_Horiz     0.05   0.60  0.95  0.10  0.00  0.10  0.00  0.05
Pie           0.00   0.30  0.00  0.80  0.00  0.90  0.00  0.00
KPI           0.00   0.00  0.00  0.00  0.00  0.00  1.00  0.00
Scatter       0.05   0.10  0.00  0.40  0.95  0.00  0.00  0.00
Table         0.10   0.20  0.20  0.20  0.10  0.10  0.10  0.95
Histogram     0.10   0.10  0.00  0.95  0.10  0.00  0.00  0.05
```

## B3. What Comes Next — From Theory to Code

This document is now complete.
The next step is not more theory.
The next step is creating these real files:

```
docs/brain/
└── SQLviz_Mathematical_Foundations_v0.1.3.md  ← this document

packages/sqlviz-inference/rules/
├── feature_vector_v0.yaml      ← 38 features defined
├── intent_rules.yaml           ← 12 intent scoring weights
├── chart_affinity_matrix.yaml  ← 8×8 affinity matrix V0
├── chart_penalties.yaml        ← penalty rules per chart
├── fallback_rules.yaml         ← fallback thresholds
└── thresholds.yaml             ← global thresholds

packages/sqlviz-inference/src/
└── infer.py                    ← infer(sql) -> InferenceResult
```

The minimum viable brain:

```python
from sqlviz_inference import infer

result = infer("SELECT month, SUM(revenue) FROM sales GROUP BY month")

# result.chart_winner    == "line"
# result.intent_winner   == "trend"
# result.chart_quality   == "high"
# result.fallback_applied == False
# result.fingerprint     == "TIME_SUM_GROUP1_ORDER_ASC"
```

That is the first real brain of SQLviz.

---

*SQLviz Mathematical & Statistical Foundations — v0.1.3 (Final V0)*
*"From theory to code. No more theory."*
*Feature Vector: 39 dimensions. Chart types: 8. Ready to implement.*
