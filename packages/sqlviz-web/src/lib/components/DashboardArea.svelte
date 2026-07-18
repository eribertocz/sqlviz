<script lang="ts">
    import DashboardGrid from '$lib/components/DashboardGrid.svelte';
    import StateMessage from '$lib/components/shared/StateMessage.svelte';
    import { dashboardStore } from '$lib/stores/dashboardStore.svelte';
    import { editMode } from '$lib/stores/editMode';
    import { executionStore } from '$lib/stores/executionStore.svelte';
</script>

<div class="dashboard-area" class:empty={!dashboardStore.hasLayout && !executionStore.executing}>
    {#if executionStore.executing && !dashboardStore.hasLayout}
        <StateMessage kind="loading" message={executionStore.statusMsg ?? 'Executing…'} />
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
</style>
