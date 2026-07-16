<script lang="ts">
    import type { InferenceResult } from '$lib/types';

    const CHART_LABELS: Record<string, string> = {
        bar:            'Bar',
        bar_horizontal: 'Horizontal bar',
        pie:            'Pie',
        line:           'Line',
        scatter:        'Scatter',
        histogram:      'Histogram',
        table:          'Table',
        kpi:            'KPI',
        funnel:         'Funnel',
    };

    function labelFor(ct: string): string {
        return CHART_LABELS[ct] ?? ct.replace(/_/g, ' ');
    }

    function scoreColor(pct: number): string {
        if (pct >= 80) return 'score-high';
        if (pct >= 60) return 'score-mid';
        if (pct >= 40) return 'score-low';
        return 'score-vlow';
    }

    let { result, onSelect, onClose }: {
        result: InferenceResult;
        onSelect: (chartType: string) => void;
        onClose: () => void;
    } = $props();

    // Engine's pure winner (stable across re-executes for same SQL/data).
    const engineWinner = result.chart_engine_winner ?? result.chart_winner;

    // Build stable list from ALL 8 chart types. Computed once at init, never recomputed.
    type ListItem = { chart: string; pct: number; isWinner: boolean };
    const allItems: ListItem[] = (() => {
        const alts = result.chart_alternatives ?? [];
        if (alts.length === 0) {
            return [{ chart: engineWinner, pct: 100, isWinner: true }];
        }
        return alts
            .map(a => ({
                chart: a.chart,
                pct: Math.round((a.pct ?? 0) * 100),
                isWinner: a.chart === engineWinner,
            }))
            .sort((a, b) => b.pct - a.pct);
    })();

    const recommended = allItems.filter(a => a.pct >= 50);
    const available    = allItems.filter(a => a.pct < 50);

    let showBreakdown = $state(false);
    // _override tracks in-session selection. Initialise from chart_winner so
    // a panel-level override (chart_user_override) is visible on first open.
    let _override = $state<string | null>(
        result.chart_winner !== engineWinner ? result.chart_winner : null
    );
    const selected    = $derived(_override ?? engineWinner);
    const isOverridden = $derived(selected !== engineWinner);

    function handleSelect(chartType: string) {
        _override = chartType === engineWinner ? null : chartType;
        onSelect(chartType);
    }

    const breakdown = $derived(result.chart_scores?.[selected]?.breakdown);
</script>

<!-- Close on Escape -->
<svelte:window onkeydown={(e) => { if (e.key === 'Escape') onClose(); }} />

<div class="chart-selector" onclick={(e) => e.stopPropagation()} onkeydown={(e) => e.stopPropagation()} role="dialog" aria-label="Chart type selector" tabindex="-1">
    <div class="selector-header">
        <span class="selector-title">Chart type</span>
        <button class="close-btn" onclick={onClose} aria-label="Close">×</button>
    </div>

    <div class="candidates">
        {#if recommended.length > 0}
            <div class="group-label">Recommended</div>
            {#each recommended as item (item.chart)}
                <label class="candidate" class:winner={item.isWinner}>
                    <input type="radio" name="chart-sel" value={item.chart}
                           checked={selected === item.chart}
                           onchange={() => handleSelect(item.chart)} />
                    <span class="chart-name">{labelFor(item.chart)}</span>
                    <span class="score {scoreColor(item.pct)}">{item.pct}%</span>
                    {#if item.isWinner}
                        <span class="badge">{isOverridden ? 'Manual' : 'Auto'}</span>
                    {:else if result.feedback_preferred_chart === item.chart}
                        <span class="badge badge-preferred">★</span>
                    {/if}
                </label>
            {/each}
        {/if}

        {#if available.length > 0}
            <div class="group-label group-label-available">Available</div>
            {#each available as item (item.chart)}
                <label class="candidate candidate-available">
                    <input type="radio" name="chart-sel" value={item.chart}
                           checked={selected === item.chart}
                           onchange={() => handleSelect(item.chart)} />
                    <span class="chart-name">{labelFor(item.chart)}</span>
                    <span class="score {scoreColor(item.pct)}">{item.pct}%</span>
                    {#if result.feedback_preferred_chart === item.chart}
                        <span class="badge badge-preferred">★</span>
                    {/if}
                </label>
            {/each}
        {/if}
    </div>

    <!-- Score breakdown (DOC6 §12.1.1) -->
    <button class="breakdown-toggle" onclick={() => showBreakdown = !showBreakdown}>
        {showBreakdown ? '▲' : '▶'} Why these scores?
    </button>

    {#if showBreakdown}
        {#if breakdown}
            <dl class="breakdown">
                <dt>semantic_fit</dt>        <dd>{breakdown.semantic_fit.toFixed(2)}</dd>
                <dt>readability</dt>         <dd>{breakdown.readability.toFixed(2)}</dd>
                <dt>perceptual_accuracy</dt> <dd>{breakdown.perceptual_accuracy.toFixed(2)}</dd>
                <dt>cognitive_load</dt>      <dd>{breakdown.cognitive_load.toFixed(2)}</dd>
                <dt>task_fit</dt>            <dd>{breakdown.task_fit.toFixed(2)}</dd>
            </dl>
        {:else}
            <p class="breakdown-na">Detailed breakdown available in V0.2 backend.</p>
        {/if}
    {/if}

    {#if isOverridden}
        <button class="reset-btn" onclick={() => {
            _override = null;
            onSelect(engineWinner);
        }}>
            Reset to auto
        </button>
    {/if}
</div>

<style>
    .chart-selector {
        background: var(--sqlviz-bg-surface);
        border: 1px solid var(--sqlviz-border);
        border-radius: var(--sqlviz-radius-lg);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        width: 260px;
        font-size: 0.8125rem;
        overflow: hidden;
    }

    .selector-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.625rem 0.875rem;
        border-bottom: 1px solid var(--sqlviz-border);
    }

    .selector-title {
        font-weight: 600;
        color: var(--sqlviz-text);
        font-size: 0.8125rem;
    }

    .close-btn {
        background: none;
        border: none;
        cursor: pointer;
        color: var(--sqlviz-text-muted);
        font-size: 1.125rem;
        line-height: 1;
        padding: 0 0.125rem;
        transition: color 0.15s;
    }
    .close-btn:hover { color: var(--sqlviz-text); }

    .candidates {
        padding: 0.25rem 0;
        max-height: 360px;
        overflow-y: auto;
    }

    .group-label {
        padding: 0.3125rem 0.875rem 0.125rem;
        font-size: 0.6875rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: var(--sqlviz-text-muted);
    }

    .group-label-available {
        border-top: 1px solid var(--sqlviz-border);
        margin-top: 0.25rem;
    }

    .candidate {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.4375rem 0.875rem;
        cursor: pointer;
        transition: background 0.1s;
    }
    .candidate:hover { background: var(--sqlviz-bg-base); }
    .candidate.winner { font-weight: 600; }
    .candidate.candidate-available { opacity: 0.75; }

    .candidate input[type="radio"] {
        accent-color: var(--sqlviz-primary);
        flex-shrink: 0;
    }

    .chart-name {
        flex: 1;
        color: var(--sqlviz-text);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .score {
        font-variant-numeric: tabular-nums;
        font-weight: 600;
        flex-shrink: 0;
    }
    .score-high  { color: var(--sqlviz-positive); }
    .score-mid   { color: var(--sqlviz-text); }
    .score-low   { color: var(--sqlviz-neutral); }
    .score-vlow  { color: var(--sqlviz-negative); }

    .badge {
        font-size: 0.6875rem;
        background: var(--sqlviz-primary);
        color: #fff;
        border-radius: 3px;
        padding: 0.0625rem 0.3125rem;
        flex-shrink: 0;
    }

    .badge-preferred {
        background: transparent;
        color: #f59e0b;
        border: 1px solid #f59e0b;
    }

    .breakdown-toggle {
        display: block;
        width: 100%;
        padding: 0.4375rem 0.875rem;
        background: none;
        border: none;
        border-top: 1px solid var(--sqlviz-border);
        text-align: left;
        cursor: pointer;
        font-size: 0.75rem;
        color: var(--sqlviz-text-muted);
        transition: color 0.15s;
    }
    .breakdown-toggle:hover { color: var(--sqlviz-text); }

    .breakdown {
        display: grid;
        grid-template-columns: 1fr auto;
        gap: 0.1875rem 0.75rem;
        padding: 0.5rem 0.875rem;
        margin: 0;
        font-size: 0.75rem;
        border-top: 1px solid var(--sqlviz-border);
    }
    .breakdown dt { color: var(--sqlviz-text-muted); }
    .breakdown dd {
        margin: 0;
        text-align: right;
        font-variant-numeric: tabular-nums;
        color: var(--sqlviz-text);
    }

    .breakdown-na {
        margin: 0;
        padding: 0.5rem 0.875rem;
        font-size: 0.75rem;
        color: var(--sqlviz-text-muted);
        border-top: 1px solid var(--sqlviz-border);
    }

    .reset-btn {
        display: block;
        width: 100%;
        padding: 0.5rem 0.875rem;
        background: none;
        border: none;
        border-top: 1px solid var(--sqlviz-border);
        text-align: center;
        cursor: pointer;
        font-size: 0.75rem;
        color: var(--sqlviz-text-muted);
        transition: color 0.15s, background 0.15s;
    }
    .reset-btn:hover {
        background: var(--sqlviz-bg-base);
        color: var(--sqlviz-text);
    }
</style>
