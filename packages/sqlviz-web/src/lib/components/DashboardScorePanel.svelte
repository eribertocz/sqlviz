<script lang="ts">
    import type { DashboardLayout } from '$lib/types';

    // Thresholds per DOC6 §12.3.2.
    function scoreLabel(pct: number): { text: string; cls: string } {
        if (pct >= 85) return { text: 'Excellent', cls: 'excellent' };
        if (pct >= 70) return { text: 'Good',      cls: 'good' };
        if (pct >= 55) return { text: 'Fair',      cls: 'fair' };
        return               { text: 'Needs work', cls: 'needs-work' };
    }

    let { layout, onApplySuggestion, onClose }: {
        layout: DashboardLayout;
        onApplySuggestion?: (panelId: string, action: Record<string, unknown>) => void;
        onClose: () => void;
    } = $props();

    const utilityPct = $derived(Math.round((layout.utility_score ?? 0) * 100));
    const label = $derived(scoreLabel(utilityPct));

    const suggestions = $derived(
        (layout.suggestions ?? [])
            .slice()
            .sort((a, b) => b.score_impact - a.score_impact)
    );

    const breakdown = $derived(layout.utility_breakdown ?? {});
    const hasData = $derived(layout.utility_score != null);

    // Track dismissed suggestions (session-only, no API).
    let dismissed = $state(new Set<string>());
    const visibleSuggestions = $derived(
        suggestions.filter(s => !dismissed.has(s.panel_id + s.suggestion))
    );

    function dismiss(s: typeof suggestions[0]) {
        dismissed = new Set([...dismissed, s.panel_id + s.suggestion]);
    }
</script>

<aside class="score-panel" aria-label="Dashboard Score">
    <div class="panel-header">
        <span class="panel-title">Dashboard Score</span>
        <button class="close-btn" onclick={onClose} aria-label="Close score panel">×</button>
    </div>

    {#if !hasData}
        <div class="no-data">
            <p>Score available after dashboard execution.</p>
            <p class="hint">V0.2 backend required for utility scoring.</p>
        </div>
    {:else}
        <!-- Utility score bar (DOC6 §12.3.1) -->
        <div class="utility-block">
            <div class="score-row">
                <span class="score-heading">Utility Score</span>
                <span class="score-value {label.cls}">{utilityPct} / 100 · {label.text}</span>
            </div>
            <div class="score-track">
                <div class="score-fill" style="width: {utilityPct}%"></div>
            </div>
        </div>

        <!-- Per-dimension breakdown -->
        {#if Object.keys(breakdown).length > 0}
            <div class="breakdown-block">
                {#each Object.entries(breakdown) as [key, value] (key)}
                    {@const pct = Math.round(Number(value) * 100)}
                    {@const lowGood = key === 'cognitive_load' || key === 'space_waste'}
                    <div class="breakdown-row">
                        <span class="dim-name">{key}</span>
                        <div class="mini-track">
                            <div class="mini-fill" style="width: {pct}%"></div>
                        </div>
                        <span class="dim-value" class:low-good={lowGood}>
                            {Number(value).toFixed(2)}
                            {#if lowGood}<span class="low-good-hint">(low=good)</span>{/if}
                        </span>
                    </div>
                {/each}
            </div>
        {/if}

        <!-- Suggestions (DOC6 §12.3.1) -->
        {#if visibleSuggestions.length > 0}
            <div class="suggestions-block">
                <span class="suggestions-label">Sugerencias</span>
                {#each visibleSuggestions as s (s.panel_id + s.suggestion)}
                    <div class="suggestion">
                        <div class="suggestion-text">
                            <span class="warn-icon">⚠</span>
                            <div>
                                <strong>{s.panel_label ?? s.panel_id}</strong>
                                <span class="suggestion-body"> — {s.suggestion}</span>
                                <span class="impact">(+{Math.round(s.score_impact * 100)}% utility)</span>
                            </div>
                        </div>
                        <div class="suggestion-actions">
                            {#if s.action && onApplySuggestion}
                                <button class="action-btn apply"
                                        onclick={() => onApplySuggestion?.(s.panel_id, s.action)}>
                                    Apply
                                </button>
                            {/if}
                            <button class="action-btn dismiss" onclick={() => dismiss(s)}>
                                Dismiss
                            </button>
                        </div>
                    </div>
                {/each}
            </div>
        {/if}
    {/if}
</aside>

<style>
    .score-panel {
        width: 300px;
        background: var(--sqlviz-bg-surface);
        border-left: 1px solid var(--sqlviz-hairline);
        display: flex;
        flex-direction: column;
        overflow-y: auto;
        flex-shrink: 0;
    }

    .panel-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.75rem 1rem;
        border-bottom: 1px solid var(--sqlviz-border);
        flex-shrink: 0;
    }

    .panel-title {
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--sqlviz-text);
    }

    .close-btn {
        background: none;
        border: none;
        cursor: pointer;
        color: var(--sqlviz-text-muted);
        font-size: 1.125rem;
        line-height: 1;
        transition: color 0.15s;
    }
    .close-btn:hover { color: var(--sqlviz-text); }

    .no-data {
        padding: 1rem;
        color: var(--sqlviz-text-muted);
        font-size: 0.8125rem;
    }
    .no-data p { margin: 0 0 0.375rem; }
    .hint { font-size: 0.75rem; opacity: 0.7; }

    /* Utility score */
    .utility-block {
        padding: 0.875rem 1rem;
        border-bottom: 1px solid var(--sqlviz-border);
    }

    .score-row {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        margin-bottom: 0.5rem;
    }

    .score-heading {
        font-size: 0.8125rem;
        font-weight: 600;
        color: var(--sqlviz-text);
    }

    .score-value {
        font-size: 0.75rem;
        font-variant-numeric: tabular-nums;
        font-weight: 600;
    }
    .score-value.excellent { color: var(--sqlviz-positive); }
    .score-value.good      { color: var(--sqlviz-primary); }
    .score-value.fair      { color: var(--sqlviz-neutral); }
    .score-value.needs-work { color: var(--sqlviz-negative); }

    .score-track {
        height: 6px;
        background: var(--sqlviz-border);
        border-radius: 3px;
        overflow: hidden;
    }
    .score-fill {
        height: 100%;
        background: var(--sqlviz-primary);
        border-radius: 3px;
        transition: width 0.4s ease;
    }

    /* Breakdown */
    .breakdown-block {
        padding: 0.75rem 1rem;
        border-bottom: 1px solid var(--sqlviz-border);
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .breakdown-row {
        display: grid;
        grid-template-columns: 1fr 80px auto;
        align-items: center;
        gap: 0.5rem;
    }

    .dim-name {
        font-size: 0.75rem;
        color: var(--sqlviz-text-muted);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .mini-track {
        height: 4px;
        background: var(--sqlviz-border);
        border-radius: 2px;
        overflow: hidden;
    }
    .mini-fill {
        height: 100%;
        background: var(--sqlviz-primary);
        border-radius: 2px;
        transition: width 0.3s ease;
    }

    .dim-value {
        font-size: 0.6875rem;
        font-variant-numeric: tabular-nums;
        color: var(--sqlviz-text-muted);
        text-align: right;
        white-space: nowrap;
    }
    .dim-value.low-good { color: var(--sqlviz-positive); }
    .low-good-hint { opacity: 0.6; margin-left: 2px; }

    /* Suggestions */
    .suggestions-block {
        padding: 0.75rem 1rem;
        display: flex;
        flex-direction: column;
        gap: 0.625rem;
    }

    .suggestions-label {
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--sqlviz-text-muted);
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.125rem;
    }

    .suggestion {
        background: var(--sqlviz-bg-base);
        border: 1px solid var(--sqlviz-border);
        border-radius: var(--sqlviz-radius);
        padding: 0.5rem 0.625rem;
    }

    .suggestion-text {
        display: flex;
        gap: 0.375rem;
        font-size: 0.75rem;
        color: var(--sqlviz-text);
        margin-bottom: 0.375rem;
    }

    .warn-icon {
        color: var(--sqlviz-neutral);
        flex-shrink: 0;
    }

    .suggestion-body { color: var(--sqlviz-text-muted); }
    .impact { color: var(--sqlviz-positive); margin-left: 2px; }

    .suggestion-actions {
        display: flex;
        gap: 0.375rem;
        justify-content: flex-end;
    }

    .action-btn {
        padding: 0.1875rem 0.625rem;
        border-radius: var(--sqlviz-radius);
        border: 1px solid var(--sqlviz-border);
        background: none;
        cursor: pointer;
        font-size: 0.6875rem;
        font-weight: 600;
        transition: background 0.12s, color 0.12s;
    }
    .action-btn.apply {
        background: var(--sqlviz-primary);
        border-color: var(--sqlviz-primary);
        color: #fff;
    }
    .action-btn.apply:hover { opacity: 0.85; }
    .action-btn.dismiss {
        color: var(--sqlviz-text-muted);
    }
    .action-btn.dismiss:hover {
        background: var(--sqlviz-bg-surface);
        color: var(--sqlviz-text);
    }
</style>
