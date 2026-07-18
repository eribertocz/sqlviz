import type { InferenceResult } from '$lib/types';

// ── Human-readable signal names (from FEATURE_INDEX + derived features) ──
export const SIGNAL_LABELS: Record<string, string> = {
    has_group_by:                    'Groups results with GROUP BY',
    has_order_by:                    'Results are ordered sequentially',
    has_order_by_desc:               'Results ordered descending (ranking)',
    has_limit:                       'Uses TOP/LIMIT (top-N records)',
    has_aggregation:                 'Uses aggregation (SUM, COUNT, AVG…)',
    has_sum:                         'Uses SUM aggregate',
    has_count:                       'Uses COUNT aggregate',
    has_avg:                         'Uses AVG aggregate',
    has_window_function:             'Window function (RANK, ROW_NUMBER…)',
    has_cte:                         'Uses Common Table Expression (WITH…)',
    has_join:                        'Joins multiple tables',
    has_where:                       'Filters data with WHERE',
    has_date_column:                 'Contains a date/time column',
    has_numeric_column:              'Contains numeric columns',
    has_string_column:               'Contains text/string columns',
    has_single_numeric_column:       'Returns a single numeric value',
    has_two_numeric_columns:         'Returns two numeric columns (x/y pair)',
    has_temporal_dimension:          'Temporal grouping (date/time)',
    has_geographic_dimension:        'Geographic grouping (location)',
    has_revenue_metric:              'Revenue or monetary metric detected',
    has_product_entity:              'Product or item entity detected',
    has_customer_entity:             'Customer or user entity detected',
    has_distinct:                    'Uses DISTINCT',
    has_case_when:                   'Contains CASE WHEN logic',
    has_outliers:                    'Data contains statistical outliers',
    has_outliers_detected:           'Outlier values detected in results',
    has_partition_by:                'Uses PARTITION BY',
    has_subquery:                    'Contains a subquery',
    result_row_count_is_1:           'Returns exactly 1 row (single metric)',
    result_column_count_is_1:        'Returns exactly 1 column',
    result_is_wide_table:            'Wide table — many columns, general data',
    numeric_column_ratio:            'High proportion of numeric columns',
    date_column_ratio:               'High proportion of date columns',
    row_count_normalized:            'Number of result rows (non-zero)',
    cardinality_ratio:               'Category uniqueness ratio',
    temporal_cardinality:            'Distinct time periods in result',
    trend_strength:                  'Statistical trend detected in values',
    no_group_by:                     'No GROUP BY clause',
    no_aggregation:                  'No aggregate functions',
    no_temporal_dimension:           'No temporal dimension present',
    no_order_by_desc:                'Not ordered descending',
    no_numeric_column:               'No numeric output columns',
    no_case_when:                    'No conditional logic',
    no_customer_entity:              'No customer entity found',
    no_count:                        'No COUNT aggregate',
    order_desc_and_limit:            'Top-N ranking pattern (DESC + LIMIT)',
    high_cardinality:                'Many unique categories',
    low_cardinality:                 'Few distinct categories',
    multiple_rows:                   'Returns multiple rows',
    single_numeric_column:           'Single numeric column in result',
    high_col_count:                  'Many columns selected',
    group_by_count_gte_2:            'Groups by 2 or more dimensions',
    part_of_whole_score:             'Part-of-whole pattern (share/percentage)',
    is_monotonic_decreasing:         'Values consistently decrease (funnel)',
    distinct_entity_count_over_time: 'Distinct users counted over time (retention)',
    has_percentile:                  'Uses percentile/quantile function',
};

// ── Intent metadata ────────────────────────────────────────────────────────
export const INTENT_META: Record<string, { label: string; icon: string; description: string }> = {
    trend:       { label: 'Temporal Trend',       icon: '↗',  description: 'Values change over time. The SQL groups by a date or sequential column with an ORDER BY.' },
    comparison:  { label: 'Comparison',           icon: '⇄',  description: 'Values compared across distinct categories such as products, regions or segments.' },
    kpi:         { label: 'Key Metric (KPI)',      icon: '#',  description: 'A single aggregate number — the SQL returns one summary value with no GROUP BY.' },
    distribution:{ label: 'Distribution',         icon: '∿',  description: 'How values are spread across a range or bucket (histogram-style data).' },
    geospatial:  { label: 'Geographic',           icon: '⊕',  description: 'Data has a geographic dimension such as country, region or coordinates.' },
    relationship:{ label: 'Correlation',          icon: '◎',  description: 'Two numeric dimensions that may be correlated — scatter-plot pattern.' },
    composition: { label: 'Composition',          icon: '◔',  description: 'Parts that add up to a whole — market share, budget split, category breakdown.' },
    retention:   { label: 'Retention / Cohort',   icon: '⟲',  description: 'Tracks how many users or customers return over time (COUNT DISTINCT over temporal).' },
    funnel:      { label: 'Funnel',               icon: '▽',  description: 'Sequential steps where values consistently decrease — conversion or drop-off.' },
    ranking:     { label: 'Ranking / Top-N',      icon: '▲',  description: 'Top values sorted descending with a LIMIT — leaderboard or best performers.' },
    detail:      { label: 'Tabular Detail',       icon: '≡',  description: 'General table of records with no clear analytical pattern.' },
    anomaly:     { label: 'Anomaly Detection',    icon: '!',  description: 'Highlights outlier or unusual values in the data.' },
};

// ── Chart metadata ─────────────────────────────────────────────────────────
export const CHART_META: Record<string, { label: string; description: string }> = {
    line:           { label: 'Line Chart',          description: 'Shows how a value evolves over time or a sequential dimension.' },
    bar:            { label: 'Bar Chart',           description: 'Compares discrete values across categories side by side.' },
    bar_horizontal: { label: 'Horizontal Bar',      description: 'Same as bar but rotated — better when category labels are long.' },
    pie:            { label: 'Pie Chart',           description: 'Shows each category as a fraction of the total.' },
    scatter:        { label: 'Scatter Plot',        description: 'Reveals correlations between two numeric variables.' },
    histogram:      { label: 'Histogram',           description: 'Distribution of a single numeric variable across value buckets.' },
    table:          { label: 'Table',               description: 'Presents all records when no single visualization fits better.' },
    kpi:            { label: 'KPI Card',            description: 'A single headline number — the most important metric, front and center.' },
};

// ── Quality metadata ───────────────────────────────────────────────────────
export const QUALITY_META: Record<string, { label: string; cls: string; detail: string }> = {
    high:   { label: 'High confidence',   cls: 'positive', detail: 'The SQL pattern clearly matches the detected intent. This visualization is highly reliable.' },
    medium: { label: 'Medium confidence', cls: 'neutral',  detail: 'The SQL pattern partially matches. The result is likely correct but some ambiguity exists.' },
    low:    { label: 'Low confidence',    cls: 'negative', detail: 'The SQL pattern is ambiguous. Consider rephrasing your query for clearer inference.' },
};

// ── Derived display helpers ────────────────────────────────────────────────
export type ExplainItem = { signal: string; contribution: number };

export function topSignals(ir: InferenceResult): ExplainItem[] {
    return (ir.explanation as Array<{ signal: string; contribution: number }>)
        .filter(e => e.contribution > 0)
        .sort((a, b) => b.contribution - a.contribution)
        .slice(0, 5);
}

export function signalLabel(signal: string): string {
    return SIGNAL_LABELS[signal] ?? signal.replace(/_/g, ' ');
}

export function intentMeta(intent: string) {
    return INTENT_META[intent] ?? { label: intent, icon: '?', description: '' };
}

export function chartMeta(chart: string) {
    return CHART_META[chart] ?? { label: chart, description: '' };
}

export function qualityMeta(quality: string) {
    return QUALITY_META[quality] ?? QUALITY_META['low'];
}

export function pct(score: number, max: number): string {
    if (max === 0) return '4%';
    return Math.max(4, Math.round((score / max) * 100)) + '%';
}
