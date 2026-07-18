<script lang="ts">
    import type { InferenceResult } from '$lib/types';
    import ScoreBars from './ScoreBars.svelte';
    import { chartMeta } from './explainMeta';

    let { ir }: { ir: InferenceResult } = $props();

    const cm = $derived(chartMeta(ir.chart_winner));
    const chartAlts = $derived(ir.chart_alternatives as Array<{ chart: string; raw_score: number }>);
    const allCharts = $derived([
        { chart: ir.chart_winner, raw_score: ir.chart_raw_score },
        ...chartAlts,
    ]);
</script>

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
        <ScoreBars items={allCharts.map(x => ({ label: chartMeta(x.chart).label, raw_score: x.raw_score }))} />
    {/if}
</section>

<style>
    .section {
        padding: 0.75rem 0;
        border-bottom: 1px solid var(--sqlviz-border);
    }

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
</style>
