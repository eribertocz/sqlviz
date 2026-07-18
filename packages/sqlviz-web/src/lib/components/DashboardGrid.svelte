<script lang="ts">
    import type { DashboardLayout } from '$lib/types';
    import PanelRenderer from './PanelRenderer.svelte';

    /**
     * DashboardLayout produced by DashboardEngine.compose() (DOC5 §15.4).
     * Rendered in the exact order received — NO client-side layout logic.
     * (DOC6 §1.1: "The frontend NEVER infers. The frontend ONLY renders.")
     */
    let { layout, onEditSQL, onExplain, onDelete, onChartOverride, onWidthOverride, onHeightOverride }: {
        layout: DashboardLayout;
        onEditSQL?: (id: string) => void;
        onExplain?: (id: string) => void;
        onDelete?: (id: string) => void;
        onChartOverride?: (panelId: string, chartType: string) => void;
        onWidthOverride?: (panelId: string, cols: number | null) => void;
        onHeightOverride?: (panelId: string, px: number | null) => void;
    } = $props();
</script>

<!--
    CSS Grid: 12 columns, gap and padding from --sqlviz-gap (DOC6 §4.1).

    Each panel sets --panel-col-span = panel.final_col_span.
    --panel-height = inference_result.panel_height_px (px, computed by LayoutEngine).
    No grid-auto-rows — heights are explicit per panel, not driven by row multipliers.
    panel.col_offset > 0 on the first panel of a KPI row — rendered as a spacer div
    so the row appears visually centered in the 12-column grid.

    id="panel-{panel_id}" on each panel div enables DashboardSidebar scroll-to (DOC6 §12).
-->
<div class="dashboard-grid">
    {#each layout.rows as row (row.panels[0]?.panel_id ?? Math.random())}
        {#each row.panels as panel, i (panel.panel_id)}
            {#if i === 0 && panel.col_offset > 0}
                <div class="kpi-spacer" style="grid-column: span {panel.col_offset}"></div>
            {/if}
            <div
                id="panel-{panel.panel_id}"
                class="dashboard-panel"
                style="--panel-col-span: {panel.final_col_span};
                       --panel-height: {panel.inference_result.panel_height_px}px"
            >
                <PanelRenderer
                    {panel}
                    {onEditSQL}
                    {onExplain}
                    {onDelete}
                    {onChartOverride}
                    {onWidthOverride}
                    {onHeightOverride}
                />
            </div>
        {/each}
    {/each}
</div>

<style>
    /* ── DOC6 §4.1 CSS ─────────────────────────────────────────── */
    .dashboard-grid {
        display: grid;
        grid-template-columns: repeat(12, 1fr);
        /* No grid-auto-rows: heights come from --panel-height (panel_height_px from
           LayoutEngine). Each panel row auto-sizes to its tallest member. */
        gap: var(--sqlviz-gap);
        padding: var(--sqlviz-gap);
    }

    .dashboard-panel {
        grid-column: span var(--panel-col-span);
        height: var(--panel-height);
        background: var(--sqlviz-bg-surface);
        border: 1px solid var(--sqlviz-hairline);
        border-radius: var(--sqlviz-radius-lg);
        box-shadow: var(--sqlviz-shadow-card);
        overflow: hidden;
    }

    .kpi-spacer {
        /* Invisible gap that centers KPI cards in the 12-col grid (DOC5 §16.34). */
        height: 0;
    }
</style>
