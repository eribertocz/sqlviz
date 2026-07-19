<script lang="ts">
    import { dashboardStore } from '$lib/stores/dashboardStore.svelte';
    import type { DashboardPanel } from '$lib/types';
    import ChartSelectorPanel from './ChartSelectorPanel.svelte';
    import { Input } from '$lib/components/ui/input/index.js';
    import { Button } from '$lib/components/ui/button/index.js';
    import XIcon from '@lucide/svelte/icons/x';
    import RotateCcwIcon from '@lucide/svelte/icons/rotate-ccw';

    let { panel }: { panel: DashboardPanel } = $props();

    const result = $derived(panel.inference_result);
    const spec = $derived(result.visual_spec);

    // Columns available for the X / Y axis pickers (from the panel's rows).
    const columns = $derived(
        panel.data.length > 0 ? Object.keys(panel.data[0]) : []
    );

    // ── Title ────────────────────────────────────────────────────────────────
    let titleValue = $state('');
    $effect(() => { titleValue = result.title ?? ''; });
    function commitTitle() {
        if (titleValue !== result.title) {
            dashboardStore.handleTitleOverride(panel.panel_id, titleValue);
        }
    }

    // ── Panel SQL ──────────────────────────────────────────────────────────────
    const panelSql = $derived(
        dashboardStore.panelSQLs[dashboardStore.panelIds.indexOf(panel.panel_id)] ?? ''
    );
    let sqlValue = $state('');
    $effect(() => { sqlValue = panelSql; });
    const sqlDirty = $derived(sqlValue.trim() !== panelSql.trim());
    function applySql() {
        if (sqlDirty) dashboardStore.handlePanelSqlChange(panel.panel_id, sqlValue);
    }

    // ── Colors ──────────────────────────────────────────────────────────────
    const PALETTES: { name: string; colors: string[] }[] = [
        { name: 'Theme',   colors: ['#6366f1', '#22c55e', '#f59e0b', '#06b6d4', '#ef4444', '#a78bfa'] },
        { name: 'Emerald', colors: ['#10b981', '#34d399', '#059669', '#6ee7b7', '#047857', '#a7f3d0'] },
        { name: 'Sunset',  colors: ['#f59e0b', '#ef4444', '#f97316', '#fbbf24', '#dc2626', '#fb923c'] },
        { name: 'Ocean',   colors: ['#0ea5e9', '#06b6d4', '#3b82f6', '#22d3ee', '#2563eb', '#67e8f9'] },
        { name: 'Mono',    colors: ['#64748b', '#94a3b8', '#475569', '#cbd5e1', '#334155', '#e2e8f0'] },
    ];
    const activePalette = $derived(dashboardStore.colorOverrides[panel.panel_id] ?? null);
    function pickPalette(p: { name: string; colors: string[] }) {
        // "Theme" clears the override; others set it.
        dashboardStore.handleColorOverride(panel.panel_id, p.name === 'Theme' ? null : p.colors);
    }
    function isActivePalette(p: { name: string; colors: string[] }): boolean {
        if (p.name === 'Theme') return activePalette === null;
        return activePalette !== null && activePalette[0] === p.colors[0];
    }

    // ── Dimensions ────────────────────────────────────────────────────────────
    let colsValue = $state(1);
    let heightValue = $state(0);
    $effect(() => { colsValue = panel.final_col_span; });
    $effect(() => { heightValue = result.panel_height_px; });
    function commitCols(v: number) {
        const c = Math.max(1, Math.min(12, Math.round(v)));
        colsValue = c;
        dashboardStore.handleWidthOverride(panel.panel_id, c);
    }
    function commitHeight(v: number) {
        const h = Math.max(120, Math.min(900, Math.round(v)));
        heightValue = h;
        dashboardStore.handleHeightOverride(panel.panel_id, h);
    }
    function resetDimensions() {
        dashboardStore.handleWidthOverride(panel.panel_id, null);
        dashboardStore.handleHeightOverride(panel.panel_id, null);
    }

    // ── Axes ──────────────────────────────────────────────────────────────────
    function setX(field: string) {
        dashboardStore.handleAxisOverride(panel.panel_id, { x_field: field || null });
    }
    function toggleY(field: string, on: boolean) {
        const current = spec?.y_fields ?? [];
        const next = on ? [...current, field] : current.filter(f => f !== field);
        dashboardStore.handleAxisOverride(panel.panel_id, { y_fields: next });
    }

    // ── Explanation ───────────────────────────────────────────────────────────
    const explanationLines = $derived(
        (result.explanation ?? [])
            .map(e => (typeof e === 'string' ? e : (e && typeof e === 'object' && 'text' in e ? String((e as { text: unknown }).text) : '')))
            .filter(Boolean)
    );
</script>

<aside class="props-panel" aria-label="Panel properties">
    <div class="props-header">
        <span class="props-title">Panel properties</span>
        <button class="close-btn" onclick={dashboardStore.closePanelProperties} aria-label="Close">
            <XIcon size={16} />
        </button>
    </div>

    <div class="props-body">
        <!-- Chart type -->
        <section class="prop-section">
            <h3 class="section-title">Chart type</h3>
            <ChartSelectorPanel
                embedded
                {result}
                onSelect={(ct) => dashboardStore.handleChartOverride(panel.panel_id, ct)}
                onClose={() => {}}
            />
        </section>

        <!-- Title -->
        <section class="prop-section">
            <h3 class="section-title">Title</h3>
            <Input bind:value={titleValue} placeholder="Panel title"
                onblur={commitTitle} onkeydown={(e) => e.key === 'Enter' && commitTitle()} />
        </section>

        <!-- Axes -->
        {#if spec}
            <section class="prop-section">
                <h3 class="section-title">Axes</h3>
                <label class="field-label" for="axis-x">X axis</label>
                <select id="axis-x" class="native-select" value={spec.x_field ?? ''} onchange={(e) => setX((e.currentTarget as HTMLSelectElement).value)}>
                    <option value="">(none)</option>
                    {#each columns as col}
                        <option value={col}>{col}</option>
                    {/each}
                </select>

                <span class="field-label">Y axis</span>
                <div class="y-fields">
                    {#each columns as col}
                        <label class="check-row">
                            <input type="checkbox" checked={spec.y_fields.includes(col)}
                                onchange={(e) => toggleY(col, (e.currentTarget as HTMLInputElement).checked)} />
                            <span>{col}</span>
                        </label>
                    {/each}
                </div>
            </section>
        {/if}

        <!-- Colors -->
        <section class="prop-section">
            <h3 class="section-title">Colors</h3>
            <div class="palettes">
                {#each PALETTES as p (p.name)}
                    <button class="palette" class:active={isActivePalette(p)} onclick={() => pickPalette(p)} title={p.name}>
                        <span class="swatches">
                            {#each p.colors.slice(0, 5) as c}
                                <span class="swatch" style="background:{c}"></span>
                            {/each}
                        </span>
                        <span class="palette-name">{p.name}</span>
                    </button>
                {/each}
            </div>
        </section>

        <!-- Dimensions -->
        <section class="prop-section">
            <h3 class="section-title">Dimensions</h3>
            <div class="dim-row">
                <label class="field-label" for="dim-cols">Width (columns)</label>
                <input id="dim-cols" type="range" min="1" max="12" step="1" value={colsValue}
                    oninput={(e) => commitCols(Number((e.currentTarget as HTMLInputElement).value))} />
                <span class="dim-value">{colsValue}</span>
            </div>
            <div class="dim-row">
                <label class="field-label" for="dim-h">Height (px)</label>
                <input id="dim-h" type="number" min="120" max="900" step="20" value={heightValue}
                    onchange={(e) => commitHeight(Number((e.currentTarget as HTMLInputElement).value))}
                    class="native-num" />
            </div>
            <Button variant="ghost" size="sm" class="gap-2" onclick={resetDimensions}>
                <RotateCcwIcon class="size-3.5" /> Reset to auto
            </Button>
        </section>

        <!-- SQL -->
        <section class="prop-section">
            <h3 class="section-title">SQL</h3>
            <textarea class="sql-area" bind:value={sqlValue} spellcheck="false"></textarea>
            <Button size="sm" disabled={!sqlDirty} onclick={applySql} class="w-full">
                Apply & run panel
            </Button>
        </section>

        <!-- Explanation -->
        <section class="prop-section">
            <h3 class="section-title">Inference</h3>
            <dl class="infer-meta">
                <dt>Intent</dt><dd>{result.intent_winner} · {result.intent_quality}</dd>
                <dt>Chart</dt><dd>{result.chart_winner} · {result.chart_quality}</dd>
                <dt>Confidence</dt><dd>{Math.round((result.chart_normalized_score ?? 0) * 100)}%</dd>
            </dl>
            {#if explanationLines.length > 0}
                <ul class="explain-list">
                    {#each explanationLines as line}
                        <li>{line}</li>
                    {/each}
                </ul>
            {:else}
                <p class="muted">No detailed explanation available for this panel.</p>
            {/if}
            {#if result.fallback_applied}
                <p class="muted">Fallback: {result.fallback_reason}</p>
            {/if}
        </section>
    </div>
</aside>

<style>
    .props-panel {
        width: 300px;
        flex-shrink: 0;
        background: var(--sqlviz-bg-surface);
        border-left: 1px solid var(--sqlviz-hairline);
        display: flex;
        flex-direction: column;
        overflow: hidden;
    }

    .props-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.625rem 0.875rem;
        border-bottom: 1px solid var(--sqlviz-hairline);
        flex-shrink: 0;
    }
    .props-title {
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        color: var(--sqlviz-text-muted);
    }
    .close-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 24px;
        height: 24px;
        border: none;
        background: none;
        color: var(--sqlviz-text-muted);
        border-radius: var(--sqlviz-radius);
        cursor: pointer;
    }
    .close-btn:hover { background: var(--sqlviz-bg-base); color: var(--sqlviz-text); }

    .props-body {
        flex: 1;
        overflow-y: auto;
        padding: 0.5rem 0.875rem 1.5rem;
    }

    .prop-section { padding: 0.75rem 0; border-bottom: 1px solid var(--sqlviz-hairline); }
    .prop-section:last-child { border-bottom: none; }

    .section-title {
        margin: 0 0 0.5rem;
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--sqlviz-text);
    }

    .field-label {
        display: block;
        font-size: 0.6875rem;
        font-weight: 600;
        color: var(--sqlviz-text-muted);
        margin: 0.5rem 0 0.25rem;
    }

    .native-select, .native-num {
        width: 100%;
        height: 30px;
        padding: 0 0.5rem;
        font-size: 0.8125rem;
        color: var(--sqlviz-text);
        background: var(--sqlviz-bg);
        border: 1px solid var(--sqlviz-border);
        border-radius: var(--sqlviz-radius);
        outline: none;
    }

    .y-fields { display: flex; flex-direction: column; gap: 0.125rem; }
    .check-row {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.8125rem;
        color: var(--sqlviz-text);
        padding: 0.1875rem 0;
    }

    .palettes { display: flex; flex-direction: column; gap: 0.375rem; }
    .palette {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.375rem 0.5rem;
        background: none;
        border: 1px solid var(--sqlviz-border);
        border-radius: var(--sqlviz-radius);
        cursor: pointer;
        transition: border-color 0.12s;
    }
    .palette:hover { border-color: var(--sqlviz-text-muted); }
    .palette.active { border-color: var(--sqlviz-primary); }
    .swatches { display: flex; gap: 2px; }
    .swatch { width: 14px; height: 14px; border-radius: 3px; }
    .palette-name { font-size: 0.75rem; color: var(--sqlviz-text); }

    .dim-row { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem; }
    .dim-row .field-label { margin: 0; flex-shrink: 0; width: 96px; }
    .dim-row input[type="range"] { flex: 1; }
    .dim-value { font-size: 0.8125rem; color: var(--sqlviz-text); min-width: 1.5ch; text-align: right; }
    .native-num { width: 96px; }

    .sql-area {
        width: 100%;
        min-height: 90px;
        margin-bottom: 0.5rem;
        padding: 0.5rem;
        font-family: var(--sqlviz-font-mono);
        font-size: 0.75rem;
        line-height: 1.5;
        color: var(--sqlviz-text);
        background: var(--sqlviz-bg);
        border: 1px solid var(--sqlviz-border);
        border-radius: var(--sqlviz-radius);
        outline: none;
        resize: vertical;
    }
    .sql-area:focus { border-color: var(--sqlviz-primary); }

    .infer-meta { display: grid; grid-template-columns: auto 1fr; gap: 0.125rem 0.625rem; margin: 0 0 0.5rem; }
    .infer-meta dt { font-size: 0.6875rem; color: var(--sqlviz-text-muted); }
    .infer-meta dd { margin: 0; font-size: 0.75rem; color: var(--sqlviz-text); }

    .explain-list { margin: 0; padding-left: 1rem; display: flex; flex-direction: column; gap: 0.25rem; }
    .explain-list li { font-size: 0.75rem; color: var(--sqlviz-text-muted); line-height: 1.4; }

    .muted { font-size: 0.75rem; color: var(--sqlviz-text-muted); margin: 0.25rem 0 0; line-height: 1.4; }
</style>
