<script lang="ts">
    import { editMode } from '$lib/stores/editMode';
    import type { DashboardPanel } from '$lib/types';
    import EChartsRenderer from './EChartsRenderer.svelte';
    import KPIRenderer from './KPIRenderer.svelte';
    import PanelFooter from './PanelFooter.svelte';
    import PanelHeader from './PanelHeader.svelte';
    import PanelOverflow from './PanelOverflow.svelte';
    import TableRenderer from './TableRenderer.svelte';

    let { panel, onEditSQL, onExplain, onDelete }: {
        panel: DashboardPanel;
        onEditSQL?: (id: string) => void;
        onExplain?: (id: string) => void;
        onDelete?: (id: string) => void;
    } = $props();
</script>

<!--
    DOC6 §5.3 — dispatches on chart_winner.
    KPI and Table get dedicated components; all other chart types
    go through EChartsRenderer. NO inference here — chart_winner
    already decided by sqlviz-inference (DOC6 §1.1).

    DOC6 §6: overflow menu and footer are gated on $editMode.
-->
<div class="panel-content">
    <PanelHeader result={panel.inference_result} panelId={panel.panel_id} {onExplain} />

    {#if $editMode}
        <div class="overflow-anchor">
            <PanelOverflow
                panelId={panel.panel_id}
                {onEditSQL}
                {onExplain}
                {onDelete}
            />
        </div>
    {/if}

    {#if panel.inference_result.chart_winner === 'kpi'}
        <KPIRenderer result={panel.inference_result} data={panel.data} />
    {:else if panel.inference_result.chart_winner === 'table'}
        <TableRenderer data={panel.data} />
    {:else}
        <EChartsRenderer
            chartType={panel.inference_result.chart_winner}
            result={panel.inference_result}
            data={panel.data}
        />
    {/if}

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

    /* Overflow button — top-right corner, sits above the panel content */
    .overflow-anchor {
        position: absolute;
        top: 6px;
        right: 6px;
        z-index: 10;
    }
</style>
