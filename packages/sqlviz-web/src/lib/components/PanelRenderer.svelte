<script lang="ts">
    import { untrack } from 'svelte';
    import { editMode } from '$lib/stores/editMode';
    import type { DashboardPanel } from '$lib/types';
    import ChartSelectorPanel from './ChartSelectorPanel.svelte';
    import EChartsRenderer from './EChartsRenderer.svelte';
    import KPIRenderer from './KPIRenderer.svelte';
    import LayoutOverrideControls from './LayoutOverrideControls.svelte';
    import PanelFooter from './PanelFooter.svelte';
    import PanelHeader from './PanelHeader.svelte';
    import PanelOverflow from './PanelOverflow.svelte';
    import TableRenderer from './TableRenderer.svelte';

    let { panel, onEditSQL, onExplain, onDelete, onChartOverride, onWidthOverride, onHeightOverride }: {
        panel: DashboardPanel;
        onEditSQL?: (id: string) => void;
        onExplain?: (id: string) => void;
        onDelete?: (id: string) => void;
        onChartOverride?: (panelId: string, chartType: string) => void;
        onWidthOverride?: (panelId: string, cols: number | null) => void;
        onHeightOverride?: (panelId: string, px: number | null) => void;
    } = $props();

    let showChartSelector = $state(false);
    let showLayoutControls = $state(false);
    let animating = $state(false);
    let animationSafetyTimer = 0;

    // Teleports a node to document.body so it escapes panel overflow clipping.
    function portal(node: HTMLElement) {
        document.body.appendChild(node);
        return { destroy() { node.remove(); } };
    }

    function closePopovers() {
        showChartSelector = false;
        showLayoutControls = false;
    }

    // When chart_winner changes in props (API override applied), end the fade-out → start fade-in.
    $effect(() => {
        void panel.inference_result.chart_winner; // reactive dependency only
        if (untrack(() => animating)) {
            clearTimeout(animationSafetyTimer);
            animating = false;
        }
    });

    function handleChartSelect(chartType: string) {
        if (chartType === panel.inference_result.chart_winner) return;
        animating = true;
        clearTimeout(animationSafetyTimer);
        // Safety reset: if API fails and chart_winner never changes, fade back in after 3s.
        animationSafetyTimer = window.setTimeout(() => { animating = false; }, 3000);
        onChartOverride?.(panel.panel_id, chartType);
    }
</script>

<!--
    DOC6 §5.3: dispatches on chart_winner.
    DOC6 §6: overflow menu and footer gated on $editMode.
    DOC6 §12.5: ChartSelectorPanel + LayoutOverrideControls as popovers in edit mode.
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
                onOpenChart={onChartOverride ? () => {
                    showLayoutControls = false;
                    showChartSelector = !showChartSelector;
                } : undefined}
                onOpenLayout={onWidthOverride ? () => {
                    showChartSelector = false;
                    showLayoutControls = !showLayoutControls;
                } : undefined}
            />
        </div>

        <!-- Chart Selector modal (DOC6 §12.1) — portalled to body to escape panel clipping -->
        {#if showChartSelector}
            <div class="modal-backdrop" use:portal onclick={closePopovers} role="presentation">
                <ChartSelectorPanel
                    result={panel.inference_result}
                    onSelect={(ct) => handleChartSelect(ct)}
                    onClose={closePopovers}
                />
            </div>
        {/if}

        <!-- Layout Override popover (DOC6 §12.2) -->
        {#if showLayoutControls}
            <div class="popover-anchor">
                <LayoutOverrideControls
                    result={panel.inference_result}
                    currentColSpan={panel.final_col_span}
                    onWidthChange={(cols) => onWidthOverride?.(panel.panel_id, cols)}
                    onHeightChange={(px) => onHeightOverride?.(panel.panel_id, px)}
                    onReset={() => {
                        onWidthOverride?.(panel.panel_id, null);
                        onHeightOverride?.(panel.panel_id, null);
                    }}
                    onClose={closePopovers}
                />
            </div>
        {/if}
    {/if}

    <div class="chart-body" class:chart-fading={animating}>
        {#if panel.inference_result.chart_winner === 'kpi'}
            <KPIRenderer result={panel.inference_result} data={panel.data} />
        {:else if panel.inference_result.chart_winner === 'table'}
            <TableRenderer data={panel.data} />
        {:else}
            <EChartsRenderer
                visualSpec={panel.inference_result.visual_spec}
                data={panel.data}
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

    .overflow-anchor {
        position: absolute;
        top: 6px;
        right: 6px;
        z-index: 10;
    }

    /* Popover for LayoutOverrideControls (DOC6 §12.2). */
    .popover-anchor {
        position: absolute;
        top: 36px;
        right: 6px;
        z-index: 200;
    }

    /* Full-screen backdrop for ChartSelectorPanel modal (DOC6 §12.1). */
    .modal-backdrop {
        position: fixed;
        inset: 0;
        z-index: 1000;
        background: rgba(0, 0, 0, 0.25);
        display: flex;
        align-items: flex-start;
        justify-content: center;
        padding-top: 80px;
    }

    /* Chart fade: 150ms out, 200ms in (DOC6 §12.1.3). */
    .chart-body {
        flex: 1;
        min-height: 0;
        display: flex;
        flex-direction: column;
        opacity: 1;
        transition: opacity 0.2s ease;
    }
    .chart-body.chart-fading {
        opacity: 0;
        transition: opacity 0.15s ease;
    }
</style>
