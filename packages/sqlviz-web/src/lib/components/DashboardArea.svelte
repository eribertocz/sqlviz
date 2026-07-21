<script lang="ts">
    import DashboardGrid from '$lib/components/DashboardGrid.svelte';
    import StateMessage from '$lib/components/shared/StateMessage.svelte';
    import { Skeleton } from '$lib/components/ui/skeleton/index.js';
    import { dashboardStore } from '$lib/stores/dashboardStore.svelte';
    import { editMode } from '$lib/stores/editMode';
    import { executionStore } from '$lib/stores/executionStore.svelte';

    // While executing with no layout yet, show one skeleton card per statement
    // (clamped) so the dashboard area previews its incoming shape.
    const skeletonCount = $derived(Math.min(Math.max(dashboardStore.statementCount, 1), 6));

    // With no cached view to show, "Last run X ago" is surfaced as a purely
    // informational line (no action) beneath the empty-state prompt. Results are
    // restored from the in-memory cache on navigation; a manual re-run rebuilds
    // them when the cache is cold (e.g. after a page reload).
    const showLastRunInfo = $derived(
        !dashboardStore.hasLayout && !executionStore.executing
        && dashboardStore.lastRunAt !== null && dashboardStore.statementCount > 0
    );

    function agoLabel(iso: string): string {
        const secs = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 1000));
        if (secs < 60) return 'just now';
        const mins = Math.round(secs / 60);
        if (mins < 60) return `${mins} min ago`;
        const hrs = Math.round(mins / 60);
        if (hrs < 24) return `${hrs} h ago`;
        return `${Math.round(hrs / 24)} d ago`;
    }
</script>

<div class="dashboard-area" class:empty={!dashboardStore.hasLayout && !executionStore.executing}>
    {#if executionStore.executing && !dashboardStore.hasLayout}
        <div class="skeleton-grid" aria-busy="true" aria-label={executionStore.statusMsg ?? 'Executing…'}>
            {#each Array(skeletonCount) as _, i (i)}
                <div class="skeleton-card">
                    <div class="skeleton-card-head">
                        <Skeleton class="h-4 w-40 rounded" />
                        <Skeleton class="size-5 rounded" />
                    </div>
                    <Skeleton class="h-[180px] w-full rounded-md" />
                </div>
            {/each}
        </div>
    {:else if !dashboardStore.hasLayout}
        <div class="empty-wrap">
            <StateMessage
                kind="empty"
                message={$editMode
                    ? 'Press Ctrl+Enter to run and see results here'
                    : 'Switch to Edit mode to write SQL and create panels'}
                hint={$editMode ? 'Separate multiple queries with ; — each becomes a panel' : undefined}
            />
            {#if showLastRunInfo}
                <p class="last-run-info">Last run {agoLabel(dashboardStore.lastRunAt!)}</p>
            {/if}
        </div>
    {:else if dashboardStore.layout}
        <DashboardGrid
            layout={dashboardStore.layout}
            onEditSQL={dashboardStore.handleEditSQL}
            onExplain={dashboardStore.handleExplain}
            onDelete={dashboardStore.handleDelete}
            onSelectPanel={dashboardStore.openPanelProperties}
            selectedPanelId={dashboardStore.propertiesPanelId}
            colorOverrides={dashboardStore.colorOverrides}
        />
    {/if}
</div>

<style>
    .dashboard-area {
        flex: 1;
        overflow-y: auto;
        min-height: 0;
    }

    .dashboard-area.empty {
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .empty-wrap {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.875rem;
    }
    .last-run-info {
        margin: 0;
        font-size: 0.8125rem;
        color: var(--sqlviz-text-muted);
        opacity: 0.75;
    }

    .skeleton-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
        gap: var(--sqlviz-gap);
        padding: var(--sqlviz-gap);
    }

    .skeleton-card {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
        padding: 1rem;
        background: var(--sqlviz-bg-surface);
        border: 1px solid var(--sqlviz-hairline);
        border-radius: var(--sqlviz-radius-lg);
        box-shadow: var(--sqlviz-shadow-card);
    }

    .skeleton-card-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
</style>
