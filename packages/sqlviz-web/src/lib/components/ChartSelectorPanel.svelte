<script lang="ts">
    import { ChevronRight, ChevronUp, Star, X } from 'lucide-svelte';
    import type { InferenceResult } from '$lib/types';
    import type { ChartOverrideResult } from '$lib/stores/dashboardStore.svelte';

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

    let { result, onSelect, onClose, embedded = false }: {
        result: InferenceResult;
        onSelect: (chartType: string | null, refreshOnly?: boolean) => Promise<ChartOverrideResult>;
        onClose: () => void;
        // When embedded in the Panel Properties panel, drop the modal chrome
        // (header, fixed sizing) so it flows as a plain section.
        embedded?: boolean;
    } = $props();

    const engineWinner = $derived(result.chart_engine_winner ?? result.chart_winner);

    // Recompute when the selected panel or its inference changes.
    type ListItem = { chart: string; pct: number | null; isWinner: boolean };
    const allItems: ListItem[] = $derived.by(() => {
        const alts = result.chart_alternatives ?? [];
        const items: ListItem[] = alts.length === 0
            ? [{ chart: engineWinner, pct: null, isWinner: true }]
            : alts
            .map(a => ({
                chart: a.chart,
                pct: Math.round((a.pct ?? 0) * 100),
                isWinner: a.chart === engineWinner,
            }))
            .sort((a, b) => b.pct - a.pct);
        if (!items.some(item => item.chart === result.chart_winner)) {
            items.push({ chart: result.chart_winner, pct: null, isWinner: false });
        }
        return items;
    });

    const recommended = $derived(allItems.filter(a => a.isWinner || (a.pct !== null && a.pct >= 50)));
    const available    = $derived(allItems.filter(a => !a.isWinner && (a.pct === null || a.pct < 50)));

    let showBreakdown = $state(false);
    const selected = $derived(result.chart_winner);
    const isOverridden = $derived(result.chart_user_override !== undefined
        ? result.chart_user_override !== null : selected !== engineWinner);
    let saving = $state(false);
    let attempted = $state<string | null>(null);
    let error = $state<string | null>(null);
    let refreshOnly = $state(false);

    async function handleSelect(chartType: string | null, refresh = false) {
        if (saving) return;
        saving = true;
        attempted = chartType;
        refreshOnly = refresh;
        error = null;
        try {
            const outcome = await onSelect(chartType, refresh);
            refreshOnly = outcome.saved;
            error = outcome.error;
        } catch {
            refreshOnly = refresh;
            error = 'Could not confirm the chart change. Retry when ready.';
        } finally {
            saving = false;
        }
    }

    function selectCandidate(event: Event, chartType: string) {
        // Native radio clicks/arrow keys must not announce an unconfirmed save.
        event.preventDefault();
        const radio = event.currentTarget as HTMLInputElement;
        radio.closest('.candidates')?.querySelectorAll<HTMLInputElement>('input[type="radio"]')
            .forEach(input => { input.checked = input.value === selected; });
        void handleSelect(chartType);
    }

    const breakdown = $derived(result.chart_scores?.[selected]?.breakdown);
</script>

<!-- Close on Escape -->
<svelte:window onkeydown={(e) => { if (e.key === 'Escape') onClose(); }} />

<div class="chart-selector" class:embedded onclick={(e) => e.stopPropagation()} onkeydown={(e) => e.stopPropagation()} role="dialog" aria-label="Chart type selector" tabindex="-1">
    {#if !embedded}
        <div class="selector-header">
            <span class="selector-title">Chart type</span>
            <button class="close-btn" onclick={onClose} aria-label="Close"><X size={15} /></button>
        </div>
    {/if}

    <div class="candidates">
        {#if recommended.length > 0}
            <div class="group-label">Recommended</div>
            {#each recommended as item (item.chart)}
                <label class="candidate" class:winner={item.isWinner}>
                    <input type="radio" name="chart-sel" value={item.chart}
                           checked={selected === item.chart}
                           disabled={saving}
                           onclick={(event) => selectCandidate(event, item.chart)}
                           onchange={(event) => selectCandidate(event, item.chart)} />
                    <span class="chart-name">{labelFor(item.chart)}</span>
                    {#if item.pct !== null}<span class="score {scoreColor(item.pct)}">{item.pct}%</span>{/if}
                    {#if selected === item.chart && isOverridden}
                        <span class="badge">Manual</span>
                    {:else if item.isWinner}
                        <span class="badge">Auto</span>
                    {:else if result.feedback_preferred_chart === item.chart}
                        <span class="badge badge-preferred"><Star size={11} fill="currentColor" /></span>
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
                           disabled={saving}
                           onclick={(event) => selectCandidate(event, item.chart)}
                           onchange={(event) => selectCandidate(event, item.chart)} />
                    <span class="chart-name">{labelFor(item.chart)}</span>
                    {#if item.pct !== null}<span class="score {scoreColor(item.pct)}">{item.pct}%</span>{/if}
                    {#if selected === item.chart && isOverridden}
                        <span class="badge">Manual</span>
                    {:else if result.feedback_preferred_chart === item.chart}
                        <span class="badge badge-preferred">★</span>
                    {/if}
                </label>
            {/each}
        {/if}
    </div>

    {#if saving}
        <p class="save-status" role="status">{refreshOnly ? 'Refreshing chart…' : 'Saving chart type…'}</p>
    {/if}
    {#if error}
        <div class="save-status save-error" role="alert">
            <p>{error}</p>
            <button class="retry-btn" onclick={() => handleSelect(attempted, refreshOnly)}>
                {refreshOnly ? 'Retry refresh' : 'Retry'}
            </button>
        </div>
    {/if}

    <!-- Score breakdown (DOC6 §12.1.1) -->
    <button class="breakdown-toggle" onclick={() => showBreakdown = !showBreakdown}>
        {#if showBreakdown}
            <ChevronUp size={12} />
        {:else}
            <ChevronRight size={12} />
        {/if}
        Why these scores?
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
        <button class="reset-btn" disabled={saving} onclick={() => handleSelect(null)}>
            Reset to auto
        </button>
    {/if}
</div>

<style>
    .save-status {
        margin: 0;
        padding: 0.5rem 0.875rem;
        font-size: 0.75rem;
        color: var(--sqlviz-text-muted);
    }
    .save-error { color: var(--sqlviz-text); }
    .save-error p { margin: 0 0 0.375rem; }
    .retry-btn {
        padding: 0.25rem 0.5rem;
        border: 1px solid var(--sqlviz-border);
        border-radius: var(--sqlviz-radius);
        background: var(--sqlviz-bg-surface);
        color: var(--sqlviz-text);
        cursor: pointer;
    }
    .retry-btn:hover { background: var(--sqlviz-bg-base); }
    .candidate:has(input:disabled), .reset-btn:disabled { opacity: 0.65; cursor: wait; }
    .chart-selector {
        background: var(--sqlviz-bg-surface);
        border: 1px solid var(--sqlviz-hairline);
        border-radius: var(--sqlviz-radius-lg);
        box-shadow: var(--sqlviz-shadow-popover);
        width: 260px;
        font-size: 0.8125rem;
        overflow: hidden;
    }

    /* Embedded in the Panel Properties panel — no modal chrome, flows full width. */
    .chart-selector.embedded {
        background: none;
        border: none;
        border-radius: 0;
        box-shadow: none;
        width: 100%;
        overflow: visible;
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
        display: inline-flex;
        align-items: center;
        background: none;
        border: none;
        cursor: pointer;
        color: var(--sqlviz-text-muted);
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
        display: inline-flex;
        align-items: center;
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
        display: flex;
        align-items: center;
        gap: 0.3125rem;
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
