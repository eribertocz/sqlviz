<script lang="ts">
    import { explainTarget } from '$lib/stores/explainStore';
    import type { InferenceResult } from '$lib/types';

    // ── Human-readable signal names (from FEATURE_INDEX + derived features) ──
    const SIGNAL_LABELS: Record<string, string> = {
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
    const INTENT_META: Record<string, { label: string; icon: string; description: string }> = {
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
    const CHART_META: Record<string, { label: string; description: string }> = {
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
    const QUALITY_META: Record<string, { label: string; cls: string; detail: string }> = {
        high:   { label: 'High confidence',   cls: 'positive', detail: 'The SQL pattern clearly matches the detected intent. This visualization is highly reliable.' },
        medium: { label: 'Medium confidence', cls: 'neutral',  detail: 'The SQL pattern partially matches. The result is likely correct but some ambiguity exists.' },
        low:    { label: 'Low confidence',    cls: 'negative', detail: 'The SQL pattern is ambiguous. Consider rephrasing your query for clearer inference.' },
    };

    // ── Derived display helpers ────────────────────────────────────────────────
    type ExplainItem = { signal: string; contribution: number };

    function topSignals(ir: InferenceResult): ExplainItem[] {
        return (ir.explanation as Array<{ signal: string; contribution: number }>)
            .filter(e => e.contribution > 0)
            .sort((a, b) => b.contribution - a.contribution)
            .slice(0, 5);
    }

    function signalLabel(signal: string): string {
        return SIGNAL_LABELS[signal] ?? signal.replace(/_/g, ' ');
    }

    function intentMeta(intent: string) {
        return INTENT_META[intent] ?? { label: intent, icon: '?', description: '' };
    }

    function chartMeta(chart: string) {
        return CHART_META[chart] ?? { label: chart, description: '' };
    }

    function qualityMeta(quality: string) {
        return QUALITY_META[quality] ?? QUALITY_META['low'];
    }

    function pct(score: number, max: number): string {
        if (max === 0) return '4%';
        return Math.max(4, Math.round((score / max) * 100)) + '%';
    }

    function close() {
        explainTarget.set(null);
    }

    function handleKeydown(e: KeyboardEvent) {
        if (e.key === 'Escape') close();
    }
</script>

<svelte:window onkeydown={handleKeydown} />

{#if $explainTarget}
    {@const ir = $explainTarget.inference_result}
    {@const signals = topSignals(ir)}
    {@const im = intentMeta(ir.intent_winner)}
    {@const cm = chartMeta(ir.chart_winner)}
    {@const qm = qualityMeta(ir.chart_quality)}
    {@const allIntents = [
        { intent: ir.intent_winner, raw_score: ir.intent_raw_score },
        ...(ir.intent_alternatives as Array<{ intent: string; raw_score: number }>),
    ]}
    {@const maxIntentScore = Math.max(...allIntents.map(x => x.raw_score), 0.01)}
    {@const chartAlts = ir.chart_alternatives as Array<{ chart: string; raw_score: number }>}
    {@const allCharts = [
        { chart: ir.chart_winner, raw_score: ir.chart_raw_score },
        ...chartAlts,
    ]}
    {@const maxChartScore = Math.max(...allCharts.map(x => x.raw_score), 0.01)}

    <!-- Backdrop (click to close) -->
    <div
        class="backdrop"
        role="presentation"
        onclick={close}
        onkeydown={() => {}}
    ></div>

    <!-- Drawer -->
    <aside class="explain-drawer" aria-label="Explainability panel">
        <!-- Header -->
        <div class="drawer-header">
            <h2 class="drawer-title">Why this chart?</h2>
            <button class="close-btn" onclick={close} aria-label="Close">✕</button>
        </div>

        <div class="drawer-body">

            <!-- Fallback banner -->
            {#if ir.fallback_applied}
                <div class="banner fallback">
                    <span class="banner-icon">⚠</span>
                    <div>
                        <strong>Inference without data</strong>
                        <p>{ir.fallback_reason || 'The query could not be executed, so inference ran on SQL structure only.'}</p>
                    </div>
                </div>
            {/if}

            <!-- ── Intent ───────────────────────────────────────────── -->
            <section class="section">
                <h3 class="section-title">Detected intent</h3>
                <div class="intent-badge">
                    <span class="intent-icon">{im.icon}</span>
                    <div>
                        <div class="intent-name">{im.label}</div>
                        {#if im.description}
                            <div class="intent-desc">{im.description}</div>
                        {/if}
                    </div>
                </div>

                <!-- Signals that drove the intent -->
                {#if signals.length > 0}
                    <div class="subsection-title">Key signals</div>
                    <ul class="signal-list">
                        {#each signals as s}
                            <li class="signal-item">
                                <span class="signal-dot">✓</span>
                                <span class="signal-name">{signalLabel(s.signal)}</span>
                                <span class="signal-score">{s.contribution.toFixed(2)}</span>
                            </li>
                        {/each}
                    </ul>
                {:else}
                    <p class="muted-note">Signal data unavailable — run the panel to see details.</p>
                {/if}

                <!-- Intent score comparison -->
                {#if allIntents.length > 1}
                    <div class="subsection-title">Intent scores</div>
                    <div class="score-bars">
                        {#each allIntents as item, i}
                            <div class="score-row">
                                <span class="score-label" class:winner={i === 0}>
                                    {intentMeta(item.intent).label}
                                </span>
                                <div class="bar-track">
                                    <div
                                        class="bar-fill"
                                        class:bar-winner={i === 0}
                                        style="width: {pct(item.raw_score, maxIntentScore)}"
                                    ></div>
                                </div>
                                <span class="score-value" class:winner={i === 0}>
                                    {item.raw_score.toFixed(2)}
                                </span>
                            </div>
                        {/each}
                    </div>
                {/if}
            </section>

            <!-- ── Chart ────────────────────────────────────────────── -->
            <section class="section">
                <h3 class="section-title">Selected chart</h3>
                <div class="chart-badge">
                    <strong>{cm.label}</strong>
                    {#if cm.description}
                        <p class="chart-desc">{cm.description}</p>
                    {/if}
                </div>

                <!-- Chart alternatives (if any) -->
                {#if chartAlts.length > 0}
                    <div class="subsection-title">Chart scores</div>
                    <div class="score-bars">
                        {#each allCharts as item, i}
                            <div class="score-row">
                                <span class="score-label" class:winner={i === 0}>
                                    {chartMeta(item.chart).label}
                                </span>
                                <div class="bar-track">
                                    <div
                                        class="bar-fill"
                                        class:bar-winner={i === 0}
                                        style="width: {pct(item.raw_score, maxChartScore)}"
                                    ></div>
                                </div>
                                <span class="score-value" class:winner={i === 0}>
                                    {item.raw_score.toFixed(2)}
                                </span>
                            </div>
                        {/each}
                    </div>
                {/if}
            </section>

            <!-- ── Quality ───────────────────────────────────────────── -->
            <section class="section">
                <h3 class="section-title">Inference confidence</h3>
                <div class="quality-row">
                    <span class="quality-badge {qm.cls}">{qm.label}</span>
                </div>
                <p class="quality-detail">{qm.detail}</p>

                {#if ir.errors.length > 0}
                    <div class="subsection-title">Errors</div>
                    <ul class="error-list">
                        {#each ir.errors as err}
                            <li class="error-item">{err}</li>
                        {/each}
                    </ul>
                {/if}
            </section>

            <!-- ── Debug info ────────────────────────────────────────── -->
            <div class="debug-row">
                <span class="debug-item">fingerprint: <code>{ir.fingerprint.slice(0, 12)}…</code></span>
                <span class="debug-item">{ir.engine_version}</span>
                <span class="debug-item">{ir.elapsed_ms.toFixed(1)} ms</span>
            </div>

        </div>
    </aside>
{/if}

<style>
    /* ── Backdrop ─────────────────────────────────────────────── */
    .backdrop {
        position: fixed;
        inset: 0;
        z-index: 200;
        background: rgba(0, 0, 0, 0.25);
    }

    /* ── Drawer ───────────────────────────────────────────────── */
    .explain-drawer {
        position: fixed;
        top: 48px;               /* below app bar */
        right: 0;
        bottom: 0;
        width: 380px;
        z-index: 201;
        background: var(--sqlviz-bg-surface);
        border-left: 1px solid var(--sqlviz-border);
        display: flex;
        flex-direction: column;
        box-shadow: -8px 0 32px rgba(0, 0, 0, 0.4);
        animation: slideIn 0.18s ease-out;
    }

    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to   { transform: translateX(0);    opacity: 1; }
    }

    /* ── Drawer header ────────────────────────────────────────── */
    .drawer-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.875rem 1rem;
        border-bottom: 1px solid var(--sqlviz-border);
        flex-shrink: 0;
    }

    .drawer-title {
        margin: 0;
        font-size: 0.9375rem;
        font-weight: 700;
        color: var(--sqlviz-text);
    }

    .close-btn {
        background: none;
        border: none;
        cursor: pointer;
        font-size: 1rem;
        color: var(--sqlviz-text-muted);
        padding: 0.25rem;
        border-radius: var(--sqlviz-radius);
        transition: color 0.15s;
        line-height: 1;
    }

    .close-btn:hover { color: var(--sqlviz-text); }

    /* ── Drawer body ──────────────────────────────────────────── */
    .drawer-body {
        flex: 1;
        overflow-y: auto;
        padding: 1rem;
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }

    /* ── Fallback banner ──────────────────────────────────────── */
    .banner {
        display: flex;
        gap: 0.75rem;
        padding: 0.75rem;
        border-radius: var(--sqlviz-radius-lg);
        margin-bottom: 0.5rem;
    }

    .banner.fallback {
        background: color-mix(in srgb, var(--sqlviz-negative) 10%, transparent);
        border: 1px solid color-mix(in srgb, var(--sqlviz-negative) 30%, transparent);
        color: var(--sqlviz-negative);
    }

    .banner-icon { font-size: 1.125rem; flex-shrink: 0; margin-top: 0.1rem; }

    .banner strong { font-size: 0.875rem; font-weight: 600; }

    .banner p {
        margin: 0.25rem 0 0;
        font-size: 0.8125rem;
        opacity: 0.85;
    }

    /* ── Section ──────────────────────────────────────────────── */
    .section {
        padding: 0.75rem 0;
        border-bottom: 1px solid var(--sqlviz-border);
    }

    .section:last-of-type { border-bottom: none; }

    .section-title {
        margin: 0 0 0.625rem;
        font-size: 0.6875rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        color: var(--sqlviz-text-muted);
    }

    .subsection-title {
        margin: 0.875rem 0 0.5rem;
        font-size: 0.6875rem;
        font-weight: 600;
        color: var(--sqlviz-text-muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* ── Intent badge ─────────────────────────────────────────── */
    .intent-badge {
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        padding: 0.5rem 0.75rem;
        background: color-mix(in srgb, var(--sqlviz-primary) 10%, transparent);
        border: 1px solid color-mix(in srgb, var(--sqlviz-primary) 25%, transparent);
        border-radius: var(--sqlviz-radius-lg);
    }

    .intent-icon {
        font-size: 1.25rem;
        flex-shrink: 0;
        color: var(--sqlviz-primary);
        margin-top: 0.1rem;
        font-style: normal;
    }

    .intent-name {
        font-size: 0.9375rem;
        font-weight: 600;
        color: var(--sqlviz-text);
    }

    .intent-desc {
        font-size: 0.8125rem;
        color: var(--sqlviz-text-muted);
        margin-top: 0.25rem;
        line-height: 1.45;
    }

    /* ── Signal list ──────────────────────────────────────────── */
    .signal-list {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: 0.3125rem;
    }

    .signal-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.8125rem;
    }

    .signal-dot {
        color: var(--sqlviz-positive);
        font-size: 0.6875rem;
        flex-shrink: 0;
    }

    .signal-name {
        flex: 1;
        color: var(--sqlviz-text);
        line-height: 1.4;
    }

    .signal-score {
        font-family: var(--sqlviz-font-mono);
        font-size: 0.6875rem;
        color: var(--sqlviz-text-muted);
        flex-shrink: 0;
    }

    /* ── Score bars ───────────────────────────────────────────── */
    .score-bars {
        display: flex;
        flex-direction: column;
        gap: 0.4375rem;
    }

    .score-row {
        display: grid;
        grid-template-columns: 120px 1fr 36px;
        align-items: center;
        gap: 0.5rem;
    }

    .score-label {
        font-size: 0.75rem;
        color: var(--sqlviz-text-muted);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .score-label.winner { color: var(--sqlviz-text); font-weight: 600; }

    .bar-track {
        height: 6px;
        background: var(--sqlviz-bg-base);
        border-radius: 3px;
        overflow: hidden;
    }

    .bar-fill {
        height: 100%;
        background: var(--sqlviz-neutral);
        border-radius: 3px;
        transition: width 0.3s ease-out;
    }

    .bar-fill.bar-winner { background: var(--sqlviz-primary); }

    .score-value {
        font-size: 0.6875rem;
        font-family: var(--sqlviz-font-mono);
        color: var(--sqlviz-text-muted);
        text-align: right;
    }

    .score-value.winner { color: var(--sqlviz-primary); font-weight: 600; }

    /* ── Chart badge ──────────────────────────────────────────── */
    .chart-badge {
        padding: 0.5rem 0.75rem;
        background: var(--sqlviz-bg-base);
        border-radius: var(--sqlviz-radius-lg);
        border: 1px solid var(--sqlviz-border);
    }

    .chart-badge strong {
        font-size: 0.875rem;
        color: var(--sqlviz-text);
    }

    .chart-desc {
        margin: 0.25rem 0 0;
        font-size: 0.8125rem;
        color: var(--sqlviz-text-muted);
        line-height: 1.45;
    }

    /* ── Quality ──────────────────────────────────────────────── */
    .quality-row { margin-bottom: 0.5rem; }

    .quality-badge {
        display: inline-block;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.25rem 0.625rem;
        border-radius: var(--sqlviz-radius);
    }

    .quality-badge.positive {
        background: color-mix(in srgb, var(--sqlviz-positive) 15%, transparent);
        color: var(--sqlviz-positive);
    }

    .quality-badge.neutral {
        background: color-mix(in srgb, var(--sqlviz-neutral) 15%, transparent);
        color: var(--sqlviz-neutral);
    }

    .quality-badge.negative {
        background: color-mix(in srgb, var(--sqlviz-negative) 15%, transparent);
        color: var(--sqlviz-negative);
    }

    .quality-detail {
        margin: 0;
        font-size: 0.8125rem;
        color: var(--sqlviz-text-muted);
        line-height: 1.5;
    }

    /* ── Error list ───────────────────────────────────────────── */
    .error-list {
        list-style: none;
        margin: 0;
        padding: 0;
    }

    .error-item {
        font-size: 0.75rem;
        font-family: var(--sqlviz-font-mono);
        color: var(--sqlviz-negative);
        padding: 0.25rem 0;
    }

    /* ── Debug row ────────────────────────────────────────────── */
    .debug-row {
        display: flex;
        gap: 0.75rem;
        flex-wrap: wrap;
        padding: 0.75rem 0 0;
        border-top: 1px solid var(--sqlviz-border);
        margin-top: 0.25rem;
    }

    .debug-item {
        font-size: 0.6875rem;
        color: var(--sqlviz-text-muted);
        font-family: var(--sqlviz-font-mono);
    }

    .debug-item code {
        font-family: inherit;
        opacity: 0.7;
    }

    /* ── Misc ─────────────────────────────────────────────────── */
    .muted-note {
        font-size: 0.8125rem;
        color: var(--sqlviz-text-muted);
        font-style: italic;
        margin: 0;
    }
</style>
