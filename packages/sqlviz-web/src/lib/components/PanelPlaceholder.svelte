<script lang="ts">
    import type { InferenceResult } from '$lib/types';

    let { result }: { result: InferenceResult } = $props();

    // Icon map for chart types — pure rendering lookup, not inference (DOC6 §1.1)
    const CHART_ICONS: Record<string, string> = {
        kpi:            '🔢',
        line:           '📈',
        bar:            '📊',
        bar_horizontal: '📊',
        scatter:        '⬤',
        pie:            '🥧',
        donut:          '🍩',
        table:          '⊞',
    };

    const icon = $derived(CHART_ICONS[result.chart_winner] ?? '📊');
</script>

<div class="placeholder">
    <div class="panel-header">
        <h3 class="panel-title">{result.title || 'Untitled query'}</h3>
        {#if result.fallback_applied}
            <span class="fallback-badge" title={result.fallback_reason}>fallback</span>
        {/if}
    </div>

    <div class="panel-body">
        <div class="chart-type">
            <span class="chart-icon">{icon}</span>
            <span class="chart-name">{result.chart_winner}</span>
        </div>
        <dl class="meta">
            <dt>intent</dt>
            <dd>{result.intent_winner}</dd>
            <dt>quality</dt>
            <dd class="quality-{result.chart_quality}">{result.chart_quality}</dd>
            <dt>grid</dt>
            <dd>{result.col_span} col · {result.panel_height_px}px</dd>
        </dl>
    </div>
</div>

<style>
    .placeholder {
        height: 100%;
        display: flex;
        flex-direction: column;
    }

    .panel-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.5rem;
        padding: 0.75rem 1rem;
        border-bottom: 1px solid var(--sqlviz-border);
    }

    .panel-title {
        margin: 0;
        font-size: 0.9375rem;
        font-weight: 600;
        color: var(--sqlviz-text);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .fallback-badge {
        flex-shrink: 0;
        font-size: 0.6875rem;
        font-weight: 600;
        padding: 0.125rem 0.375rem;
        border-radius: 4px;
        background: color-mix(in srgb, var(--sqlviz-negative) 15%, transparent);
        color: var(--sqlviz-negative);
        border: 1px solid color-mix(in srgb, var(--sqlviz-negative) 40%, transparent);
    }

    .panel-body {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 1rem;
        padding: 1.25rem;
    }

    .chart-type {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.375rem;
    }

    .chart-icon {
        font-size: 2rem;
        line-height: 1;
    }

    .chart-name {
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--sqlviz-primary);
        font-family: var(--sqlviz-font-mono);
    }

    .meta {
        display: grid;
        grid-template-columns: auto 1fr;
        gap: 0.25rem 0.75rem;
        font-size: 0.8125rem;
        margin: 0;
    }

    dt {
        color: var(--sqlviz-text-muted);
        text-align: right;
    }

    dd {
        margin: 0;
        color: var(--sqlviz-text);
        font-family: var(--sqlviz-font-mono);
    }

    .quality-high   { color: var(--sqlviz-positive); }
    .quality-medium { color: var(--sqlviz-neutral); }
    .quality-low    { color: var(--sqlviz-negative); }
</style>
