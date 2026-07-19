<script lang="ts">
    import { editMode } from '$lib/stores/editMode';
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
            />
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
    }
</style>
