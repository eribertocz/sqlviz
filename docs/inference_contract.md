# Inference Engine Contract

**Version:** V0.1 — frozen as of §16.27  
**Scope:** sqlviz-inference package  
**Purpose:** Decisions already made and encoded. Not a design proposal.

Each law documents a concrete engineering choice made during §16.1-§16.27. Every law has an example of a query that exercises it and a counter-example showing what the engine must NOT do.

---

## Law 1 — SQL structure beats column names

**Source:** DOC5 §1.2, §16.1

The pipeline processes signals in strict order: Parser → FeatureEngine → SemanticEngine → IntentEngine → ChartEngine. Structural signals derived from the AST (GROUP BY, aggregation, ORDER BY DESC + LIMIT, window functions) are computed first and carry the highest weight. Column-name semantics refine the score but cannot reverse a structural conclusion alone.

**Correct**
```sql
-- GROUP BY + SUM → temporal dimension → intent: trend
SELECT mes, SUM(monto) AS total
FROM ventas
GROUP BY mes
ORDER BY mes
-- Result: intent=trend, chart=line  ✓
```

**Incorrect** (what the engine must NOT do)
```sql
-- A column named "tendencia" (trend) must NOT alone push intent=trend
-- if the query has no GROUP BY, no ORDER BY, and returns a single row.
SELECT tendencia FROM resumen_ejecutivo
-- Wrong: intent=trend  ✗
-- Right: intent=kpi or detail  ✓
```

---

## Law 2 — Column names are semantic hints, not ground truth

**Source:** §16.21

Column names enter the engine as soft evidence. A name like `recuperacion_pct` contains the token `recuperacion`, which belongs to the **negative** list for part-of-whole signals (`_POW_NEGATIVE_TRIGGER`). This suppresses composition intent by −0.8, regardless of how "percentage-like" the name sounds.

Symmetrically, `participacion` or `share_of_total` are positive hints (+0.6) but still weaker than structural AST evidence (+1.0).

**Correct**
```sql
-- recuperacion_pct → semantic negative → composition score reduced
SELECT segmento, recuperacion_pct FROM cartera
GROUP BY segmento
-- Result: intent=comparison, chart=bar  ✓
-- (NOT intent=composition/chart=pie because name signals a rate, not a share)
```

**Incorrect**
```sql
-- naming a column "porcentaje" must NOT force pie chart
-- if there is no SUM(x)/SUM(SUM(x)) OVER () pattern
SELECT categoria, porcentaje FROM tabla
GROUP BY categoria
-- Wrong: chart=pie forced by column name alone  ✗
-- Right: chart=bar with composition as a low-confidence alternative  ✓
```

---

## Law 3 — Pie requires strong part-of-whole evidence

**Source:** §16.21

The composition intent and pie chart require **structural AST evidence** of the DOC4 §19.4 share formula: `x / AGG(x) OVER ()` with no `PARTITION BY`. Signal weights:

| Signal | Weight |
|--------|--------|
| AST `x / AGG(x) OVER ()` pattern | +1.0 |
| Strong positive column name (`participacion`, `share`, `pct_total`) | +0.6 |
| Neutral (no evidence) | 0.0 |
| Negative column name (`tasa_*`, `recuperacion_*`, `ratio_*`, `conversion_*`) | −0.8 |

Score is clamped to [−1.0, 1.0]. LAG/LEAD in the denominator deliberately does not trigger the pattern — growth-rate formulas (`SUM(x) / LAG(SUM(x)) OVER (ORDER BY t)`) are not part-of-whole.

**Correct**
```sql
-- Structural pattern present → composition intent with high confidence
SELECT categoria,
       SUM(monto) / SUM(SUM(monto)) OVER () AS participacion
FROM ventas
GROUP BY categoria
-- Result: intent=composition, chart=pie  ✓
```

**Incorrect**
```sql
-- Growth rate formula must NOT trigger pie
SELECT mes, SUM(rev) / LAG(SUM(rev)) OVER (ORDER BY mes) AS crecimiento
FROM ventas GROUP BY mes
-- Wrong: chart=pie because of division  ✗
-- Right: chart=line (trend/growth pattern)  ✓
```

---

## Law 4 — A weak/medium signal must never override a very-strong signal without lowering confidence

**Source:** §16.21 (generalized from the composition/rate conflict)

If the winning intent has `quality=high` and `intent_confidence_gap ≥ 0.60`, secondary signals pointing elsewhere must be surfaced in `intent_alternatives` and `chart_alternatives` — not promoted to winner. Overriding a high-confidence result requires the challenger to also reach high quality.

**Correct**
```sql
-- trend signals are dominant (quality=high, gap=0.72)
-- weak composition hint from column name stays as alternative
SELECT mes, SUM(monto) FROM ventas GROUP BY mes ORDER BY mes
-- intent_winner=trend, quality=high, intent_alternatives=[{composition, 0.18}]  ✓
```

**Incorrect**
```sql
-- Same query: a 0.18 composition score must NOT flip the winner to composition
-- Wrong: intent_winner=composition  ✗
-- Right: intent_winner=trend, composition in alternatives  ✓
```

---

## Law 5 — Chart penalties must be intent-aware, not global

**Source:** §16.24

The `bar` chart carries a `has_two_numeric_columns` penalty whose original purpose is to prefer `scatter` for correlation queries. This penalty is **suppressed** when `intent_winner != "correlation"`. A comparison query with `revenue`, `cost`, and `margin` columns legitimately uses a grouped bar chart; penalizing it globally was incorrect.

**Correct**
```sql
-- intent=comparison, two numeric columns → bar penalty suppressed
SELECT region, SUM(revenue) AS rev, SUM(cost) AS cost FROM sales
GROUP BY region
-- chart_winner=bar, penalty suppressed  ✓
```

**Incorrect**
```sql
-- Same query: applying has_two_numeric_columns penalty to bar regardless of intent
-- Wrong: bar demoted, scatter wins  ✗
-- Right: bar wins because penalty is intent-gated  ✓
```

---

## Law 6 — Alternative GROUP BY syntax must be treated identically to explicit columns

**Source:** §16.19 (GROUP BY ALL), §16.27 (positional GROUP BY 1, 2)

`count_group_by_columns()` handles all three syntactic forms and produces the same semantic count:

| Syntax | Form | Count method |
|--------|------|--------------|
| `GROUP BY a, b` | Named | `len(group.expressions)` |
| `GROUP BY 1, 2` | Positional | `len(group.expressions)` |
| `GROUP BY ALL` | Synthetic | Count non-aggregated SELECT columns |

The fingerprint generator, intent weights, and layout engine all consume this count. None of them see raw syntax.

**Correct**
```sql
-- GROUP BY ALL with 2 non-aggregated columns → same as GROUP BY a, b
SELECT region, categoria, SUM(monto) FROM ventas GROUP BY ALL
-- group_by_column_count = 2, same as GROUP BY region, categoria  ✓
```

**Incorrect**
```sql
-- Positional GROUP BY must not be counted as 0 or treated as "no group by"
SELECT mes, SUM(monto) FROM ventas GROUP BY 1
-- Wrong: group_by_column_count=0  ✗
-- Right: group_by_column_count=1  ✓
```

---

## Law 7 — Graceful degradation always produces a result

**Source:** DOC5 §3.4, §16.1 (stress tests)

Every module in `RuntimePipeline` wraps its logic in `try/except`. On failure it calls `context.with_error(module_name, message)` and returns the partially-populated context. The pipeline runner calls all 8 modules unconditionally — no module skips downstream execution. The final `InferenceResult` always exists; it may have `errors` populated and may have fallback defaults, but it never raises to the caller.

**Correct**
```python
# Invalid SQL reaches every module, all complete, result is produced
result = _run("THIS IS NOT SQL")
assert result.chart_winner == "table"  # fallback applied
assert len(result.errors) > 0          # errors recorded  ✓
```

**Incorrect**
```python
# A module must NOT raise an unhandled exception
result = _run("SELECT * FROM $$invalid$$")
# Wrong: raises ValueError or AttributeError  ✗
# Right: returns InferenceResult with errors list  ✓
```

---

## Law 8 — Every inference must report confidence, never fake certainty

**Source:** §16.8 (implied by DOC4 mathematical foundations)

`InferenceResult` always exposes:
- `intent_quality` / `chart_quality` — `"high"` | `"medium"` | `"low"`
- `intent_confidence_gap` / `chart_confidence_gap` — best normalized score minus second-best

A result is considered highly confident only when `quality == "high"` **and** `confidence_gap ≥ 0.60`. The API and frontend must never display a single recommended chart without exposing `chart_quality` to the consumer.

**Correct**
```python
result = infer("SELECT region, SUM(revenue) FROM sales GROUP BY region")
assert result.chart_quality in ("high", "medium", "low")
assert 0.0 <= result.chart_confidence_gap <= 1.0  ✓
```

**Incorrect**
```python
# Must not return a winner without exposing confidence metadata
result = infer(sql)
# Wrong: InferenceResult missing chart_quality or chart_confidence_gap  ✗
```

---

## Law 9 — Tie-breaking uses pre-clamp scores, not clamped scores

**Source:** §16.11

Raw chart scores can exceed 1.0 when multiple intents agree. Clamping to [0.0, 1.0] for storage destroys the ranking information when several charts all clamp to 1.0. The engine sorts by `sort_score` (pre-clamp) and stores `raw_score` (clamped). `chart_alternatives` ordering therefore reflects true relative strength.

**Correct**
```
line:  sort_score=1.38, raw_score=1.00  → rank 1  ✓
bar:   sort_score=1.12, raw_score=1.00  → rank 2  ✓
```

**Incorrect**
```
# Sorting by clamped raw_score → arbitrary tie order
line: 1.00, bar: 1.00 → random winner  ✗
```

---

## Law 10 — Cardinality signals require explicit data-presence guards

**Source:** §16.23

`high_cardinality` requires `row_count_normalized > 0.005` (≥ 50 rows) so that preview datasets where every row is distinct do not incorrectly fire the cardinality penalty on composition. `low_cardinality` requires `cardinality_ratio > 0.0` (a VARCHAR column exists) so that pure numeric queries don't accidentally satisfy `ratio < 0.15`.

Both derived features return `0.0` if no result data is present (`row_count_normalized == 0`).

**Correct**
```python
# 3-row preview dataset, all distinct → high_cardinality must NOT fire
# cardinality_ratio=1.0 but row_count_normalized=0.0003 → guard prevents it  ✓
```

**Incorrect**
```python
# 3-row preview → high_cardinality=1.0 → pie heavily penalized → wrong winner  ✗
```

---

## Law 11 — Temporal context suppresses composition inference

**Source:** §16.26

`low_cardinality` is a positive signal for composition intent (few distinct categories suggests a pie). It is suppressed (`= 0.0`) whenever `has_temporal_dimension = 1.0`. A trend query that includes a low-cardinality secondary dimension (e.g. `segmento` with 2 values: "premium", "standard") must not be pulled toward composition/pie.

**Correct**
```sql
-- temporal + low-cardinality segment → low_cardinality suppressed
SELECT mes, segmento, SUM(monto) FROM ventas GROUP BY mes, segmento ORDER BY mes
-- intent=trend, chart=line  (not composition/pie)  ✓
```

**Incorrect**
```sql
-- Same query: segmento has 2 values → low_cardinality fires → pie wins  ✗
```

---

## Law 12 — Trend direction is computed backend, not inferred frontend

**Source:** §16.6

`trend_direction_label` (`"growing"` | `"declining"` | `"flat"` | `"unknown"`) is computed in `InferenceResult.from_context()` from `fv[28]` (R² / trend strength) and `fv[38]` (normalized slope direction). The frontend receives a label string. It must not re-derive direction from raw feature vector values.

**Correct**
```python
result = infer(sql)
direction = result.trend_direction_label  # "growing"  ✓
```

**Incorrect**
```python
# Frontend reading fv[28] / fv[38] directly and computing its own label  ✗
```

---

## Law 13 — Threshold inequality direction matters: use `>=` when the boundary is a valid case

**Source:** §16.22

`group_by_column_count` is normalized as `count / 5`. Two GROUP BY columns produce `2/5 = 0.40` exactly. The derived feature `group_by_count_gte_2` originally used `> 0.4` (strict), silently excluding exactly-2-column queries. The fix: `>= 0.4`.

When a threshold corresponds to the normalized value of a valid real-world case, use `>=`, not `>`.

**Correct**
```python
# group_by_column_count = 2 → fv[12] = 0.40
# group_by_count_gte_2 = 1.0 if fv[12] >= 0.40 else 0.0
# Result: 1.0  ✓
```

**Incorrect**
```python
# group_by_count_gte_2 = 1.0 if fv[12] > 0.40 else 0.0
# Result: 0.0  ✗  (exactly-2-column GROUP BY silently excluded)
```

---

## Law 14 — Filter control type is determined by column data type, not query operator

**Source:** §16.12

`FilterEngine._classify_control()` assigns control type based on `column_type` first. DATE → `date_picker`, NUMERIC → `numeric`, BOOLEAN → `toggle`, regardless of `operator_context`. Range controls (`date_range_picker` / `range_slider`) are produced exclusively by `pair_range_filters()` as post-processing when two controls reference the same column. Control classification and range detection are separate concerns.

**Correct**
```python
# DATE column with equality operator → still date_picker, not dropdown
# Two date_pickers on same column → pair_range_filters → date_range_picker  ✓
```

**Incorrect**
```python
# DATE column with "=" operator → classified as "dropdown"  ✗
# Date range detected inside _classify_control  ✗
```

---

## Deferred to V0.2 / V1

The following items are explicitly **not** implemented in V0.1. They are listed here so future sessions have a clear boundary.

**Column Role Engine**
- A formal 17-role taxonomy (dimension, metric, identifier, date, geographic, etc.) replacing the current semantic class dict

**New chart types**
- `multi_line` — multiple line series
- `grouped_bar` — multiple bar series by category
- `boxplot` — distribution by group
- `heatmap` — matrix of two categorical dimensions
- `funnel_chart` — sequential step conversion

**New intent candidates**
- `comparison_matrix` — multi-metric × multi-dimension
- `kpi_tracking` — KPI vs target/budget
- `forecast_evaluation` — actual vs predicted

**New `InferenceResult` fields**
- `ranking_direction` — `"asc"` | `"desc"` | `"none"` for ranking/distribution charts
- `semantic_tag` — structured tag: `"cumulative"`, `"moving_average"`, `"growth_rate"`, etc.

**Heavy data profiling (DOC4 V1)**
- Full column-level statistics (percentiles, mode, null rate, entropy)
- Outlier detection beyond the current IQR heuristic
- Correlation matrix computation for scatter / multi-line suggestions
