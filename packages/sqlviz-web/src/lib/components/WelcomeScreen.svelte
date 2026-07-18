<script lang="ts">
    import { dashboardStore } from '$lib/stores/dashboardStore.svelte';
    import { Button } from '$lib/components/ui/button/index.js';
    import LayoutDashboardIcon from '@lucide/svelte/icons/layout-dashboard';
    import PlusIcon from '@lucide/svelte/icons/plus';
</script>

<div class="welcome">
    <div class="welcome-icon"><LayoutDashboardIcon size={34} /></div>
    <h1 class="welcome-title">Create your first dashboard</h1>
    <p class="welcome-sub">
        Write SQL and SQLviz composes the panels for you. Start with an empty
        dashboard and run your first query.
    </p>
    <Button class="gap-2" onclick={() => dashboardStore.createDashboard('New Dashboard', null)}>
        <PlusIcon class="size-4" /> New Dashboard
    </Button>
</div>

<style>
    .welcome {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 1rem;
        padding: 2rem;
        text-align: center;
    }

    .welcome-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 72px;
        height: 72px;
        border-radius: var(--sqlviz-radius-lg);
        background: color-mix(in srgb, var(--sqlviz-primary) 12%, transparent);
        color: var(--sqlviz-primary);
        margin-bottom: 0.25rem;
    }

    .welcome-title {
        font-size: 1.25rem;
        font-weight: 650;
        color: var(--sqlviz-text);
        margin: 0;
    }

    .welcome-sub {
        max-width: 380px;
        font-size: 0.875rem;
        line-height: 1.5;
        color: var(--sqlviz-text-muted);
        margin: 0 0 0.5rem;
    }
</style>
