<script lang="ts">
    import DashboardGrid from '$lib/components/DashboardGrid.svelte';
    import StateMessage from '$lib/components/shared/StateMessage.svelte';
    import { Skeleton } from '$lib/components/ui/skeleton/index.js';
    import { dashboardStore } from '$lib/stores/dashboardStore.svelte';
    import { editMode } from '$lib/stores/editMode';
    import { executionStore } from '$lib/stores/executionStore.svelte';

    import { Play } from 'lucide-svelte';

    // While executing with no layout yet, show one skeleton card per statement
    // (clamped) so the dashboard area previews its incoming shape.
    const skeletonCount = $derived(Math.min(Math.max(dashboardStore.statementCount, 1), 6));

    // After a refresh we don't re-run automatically (UX spec §Refresh); instead
    // show "Last run X ago" + Run Again when there is a prior successful run.
    const showLastRun = $derived(
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
    {:else if showLastRun}
        <div class="last-run">
            <p class="last-run-text">Last run {agoLabel(dashboardStore.lastRunAt!)}</p>
            <button class="run-again" onclick={dashboardStore.run}>
                <Play size={13} fill="currentColor" /> Run Again
            </button>
        </div>
    {:else if !dashboardStore.hasLayout}
        <StateMessage
            kind="empty"
            message={$editMode
                ? 'Press Ctrl+Enter to run and see results here'
                : 'Switch to Edit mode to write SQL and create panels'}
            hint={$editMode ? 'Separate multiple queries with ; — each becomes a panel' : undefined}
        />
    {:else if dashboardStore.layout}
        <DashboardGrid
            layout={dashboardStore.layout}
            onEditSQL={dashboardStore.handleEditSQL}
            onExplain={dashboardStore.handleExplain}
            onDelete={dashboardStore.handleDelete}
            onChartOverride={dashboardStore.handleChartOverride}
            onWidthOverride={dashboardStore.handleWidthOverride}
            onHeightOverride={dashboardStore.handleHeightOverride}
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

    .last-run {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.875rem;
    }
    .last-run-text {
        margin: 0;
        font-size: 0.875rem;
        color: var(--sqlviz-text-muted);
    }
    .run-again {
        display: inline-flex;
        align-items: center;
        gap: 0.4375rem;
        padding: 0.4375rem 0.875rem;
        background: var(--sqlviz-primary);
        color: #fff;
        border: none;
        border-radius: var(--sqlviz-radius);
        font-size: 0.8125rem;
        font-weight: 500;
        cursor: pointer;
        transition: filter 0.12s;
    }
    .run-again:hover { filter: brightness(1.1); }

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
