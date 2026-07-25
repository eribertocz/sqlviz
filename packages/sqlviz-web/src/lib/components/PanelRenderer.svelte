<script lang="ts">
    import { editMode } from '$lib/stores/editMode';
    import { dashboardStore } from '$lib/stores/dashboardStore.svelte';
    import type { DashboardPanel } from '$lib/types';
    import EChartsRenderer from './EChartsRenderer.svelte';
    import KPIRenderer from './KPIRenderer.svelte';
    import PanelFooter from './PanelFooter.svelte';
    import PanelHeader from './PanelHeader.svelte';
    import PanelOverflow from './PanelOverflow.svelte';
    import TableRenderer from './TableRenderer.svelte';

    let { panel, selected = false, palette, onEditSQL, onExplain, onDelete, onSelect }: {
        panel: DashboardPanel;
        selected?: boolean;
        palette?: string[];
        onEditSQL?: (id: string) => void;
        onExplain?: (id: string) => void;
        onDelete?: (id: string) => void;
        // v0.2.9: click a panel in edit mode → open its Properties panel.
        onSelect?: (id: string) => void;
    } = $props();

    function selectPanel() {
        if ($editMode) onSelect?.(panel.panel_id);
    }

    // ── Inline axis-title editing (edit mode, cartesian charts) ────────────────
    const spec = $derived(panel.inference_result.visual_spec);
    const hasAxes = $derived(
        !!spec && ['line', 'bar', 'bar_horizontal', 'scatter', 'histogram'].includes(spec.chart_type)
    );
    const xTitle = $derived((spec?.x_label || spec?.x_field) ?? '');
    const yTitle = $derived((spec?.y_label || spec?.y_fields[0]) ?? '');

    let editingAxis = $state<'x_label' | 'y_label' | null>(null);
    let axisDraft = $state('');
    function startEditAxis(axis: 'x_label' | 'y_label', current: string) {
        editingAxis = axis;
        axisDraft = current;
    }
    function commitAxis() {
        if (editingAxis) dashboardStore.setViewOverride(panel.panel_id, editingAxis, axisDraft);
        editingAxis = null;
    }
    function axisKeydown(e: KeyboardEvent) {
        if (e.key === 'Enter') { e.preventDefault(); commitAxis(); }
        else if (e.key === 'Escape') { e.preventDefault(); editingAxis = null; }
    }
    function focusInput(node: HTMLInputElement) { node.focus(); node.select(); }
</script>

<!--
    DOC6 §5.3: dispatches on chart_winner. DOC6 §6: overflow menu / footer gated on
    $editMode. v0.2.9: clicking a panel in edit mode opens the Panel Properties
    panel (replaces the floating Chart Selector modal + inline layout popover).
-->
<div
    class="panel-content"
    class:selected={selected && $editMode}
    class:clickable={$editMode}
    onclick={selectPanel}
    onkeydown={(e) => { if ($editMode && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); selectPanel(); } }}
    role="button"
    tabindex={$editMode ? 0 : -1}
    aria-label={$editMode ? 'Open panel properties' : 'Panel'}
>
    <PanelHeader result={panel.inference_result} panelId={panel.panel_id} {onExplain} />

    {#if $editMode}
        <!-- Menu clicks must not also open the properties panel. -->
        <div class="overflow-anchor" onclick={(e) => e.stopPropagation()} role="presentation">
            <PanelOverflow
                panelId={panel.panel_id}
                {onEditSQL}
                {onExplain}
                {onDelete}
            />
        </div>
    {/if}

    <div class="chart-body">
        {#if panel.inference_result.chart_winner === 'kpi'}
            <KPIRenderer result={panel.inference_result} data={panel.data} />
        {:else if panel.inference_result.chart_winner === 'table'}
            <TableRenderer data={panel.data} />
        {:else}
            <EChartsRenderer
                visualSpec={panel.inference_result.visual_spec}
                data={panel.data}
                {palette}
                hideAxisNames={$editMode && hasAxes}
            />

            {#if $editMode && hasAxes}
                <!-- Inline axis-title editing — click to rename; persists + shows in shares. -->
                <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
                <div class="axis-edit axis-x" onclick={(e) => e.stopPropagation()} role="presentation">
                    {#if editingAxis === 'x_label'}
                        <input class="axis-input" bind:value={axisDraft} use:focusInput onkeydown={axisKeydown} onblur={commitAxis} />
                    {:else}
                        <button class="axis-chip" onclick={() => startEditAxis('x_label', xTitle)} title="Edit X axis title">{xTitle || 'X axis'}</button>
                    {/if}
                </div>
                <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
                <div class="axis-edit axis-y" onclick={(e) => e.stopPropagation()} role="presentation">
                    {#if editingAxis === 'y_label'}
                        <input class="axis-input" bind:value={axisDraft} use:focusInput onkeydown={axisKeydown} onblur={commitAxis} />
                    {:else}
                        <button class="axis-chip" onclick={() => startEditAxis('y_label', yTitle)} title="Edit Y axis title">{yTitle || 'Y axis'}</button>
                    {/if}
                </div>
            {/if}
        {/if}
    </div>

    {#if $editMode}
        <PanelFooter result={panel.inference_result} data={panel.data} />
    {/if}
</div>

<style>
    .panel-content {
        height: 100%;
        display: flex;
        flex-direction: column;
        position: relative;
    }

    .panel-content.clickable { cursor: pointer; }

    /* Selected panel — highlighted while its Properties panel is open. */
    .panel-content.selected {
        outline: 2px solid var(--sqlviz-primary);
        outline-offset: -2px;
        border-radius: var(--sqlviz-radius-lg);
    }

    .overflow-anchor {
        position: absolute;
        top: 6px;
        right: 6px;
        z-index: 10;
    }

    .chart-body {
        flex: 1;
        min-height: 0;
        display: flex;
        flex-direction: column;
        position: relative;
    }

    /* Inline axis-title editing overlays (edit mode) */
    .axis-edit { position: absolute; z-index: 5; }
    .axis-x { bottom: 2px; left: 0; right: 0; display: flex; justify-content: center; }
    /* Y sits at the left, centred; both its chip and its edit input are rotated
       to match the rendered (vertical) axis title. */
    .axis-y { top: 0; bottom: 0; left: 2px; display: flex; align-items: center; }
    .axis-y .axis-chip,
    .axis-y .axis-input { transform: rotate(-90deg); }
    .axis-chip {
        font-size: 11px;
        font-weight: 600;
        color: var(--sqlviz-text-muted);
        background: transparent;
        border: 1px dashed transparent;
        border-radius: 4px;
        padding: 1px 6px;
        cursor: text;
        max-width: 60%;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        transition: border-color 0.12s, color 0.12s, background 0.12s;
    }
    .axis-chip:hover { border-color: var(--sqlviz-border); color: var(--sqlviz-text); background: var(--sqlviz-bg-base); }
    .axis-input {
        font-size: 11px;
        width: 150px;
        max-width: 70%;
        padding: 1px 6px;
        border: 1px solid var(--sqlviz-primary);
        border-radius: 4px;
        background: var(--sqlviz-bg);
        color: var(--sqlviz-text);
        outline: none;
    }
</style>
