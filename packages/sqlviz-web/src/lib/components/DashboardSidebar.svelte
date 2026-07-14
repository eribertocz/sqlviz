<script lang="ts">
    import { resolveDashboardIcon } from '$lib/dashboardIcons';
    import type { DashboardInfo } from '$lib/types';

    export interface DashboardSidebarItem extends DashboardInfo {}

    let { items, activeId = null, onSelect }: {
        items: DashboardSidebarItem[];
        activeId?: string | null;
        onSelect?: (id: string) => void;
    } = $props();
</script>

<nav class="dashboard-sidebar" aria-label="Dashboard navigation">
    <div class="sidebar-label">Dashboards</div>
    <ul class="panel-list">
        {#each items as item (item.id)}
            {@const IconCmp = resolveDashboardIcon(item.dashboard_hint, item.dashboard_domain)}
            <li>
                <button
                    class="panel-item"
                    class:active={item.id === activeId}
                    onclick={() => onSelect?.(item.id)}
                    title={item.name}
                >
                    <span class="panel-icon"><IconCmp size={14} /></span>
                    <span class="panel-title">{item.name}</span>
                </button>
            </li>
        {/each}
    </ul>
</nav>

<style>
    .dashboard-sidebar {
        width: 200px;
        flex-shrink: 0;
        background: var(--sqlviz-bg-surface);
        border-right: 1px solid var(--sqlviz-border);
        display: flex;
        flex-direction: column;
        overflow-y: auto;
    }

    .sidebar-label {
        padding: 0.625rem 0.875rem 0.375rem;
        font-size: 0.6875rem;
        font-weight: 600;
        letter-spacing: 0.07em;
        text-transform: uppercase;
        color: var(--sqlviz-text-muted);
        flex-shrink: 0;
    }

    .panel-list {
        list-style: none;
        margin: 0;
        padding: 0 0.375rem 0.5rem;
        flex: 1;
    }

    .panel-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        width: 100%;
        padding: 0.4375rem 0.5rem;
        background: none;
        border: none;
        border-radius: var(--sqlviz-radius);
        cursor: pointer;
        text-align: left;
        transition: background 0.12s, color 0.12s;
        color: var(--sqlviz-text-muted);
    }

    .panel-item:hover {
        background: var(--sqlviz-bg-base);
        color: var(--sqlviz-text);
    }

    .panel-item.active {
        background: color-mix(in srgb, var(--sqlviz-primary) 15%, transparent);
        color: var(--sqlviz-primary);
    }

    .panel-icon {
        flex-shrink: 0;
        display: flex;
        align-items: center;
    }

    .panel-title {
        font-size: 0.8125rem;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        line-height: 1.3;
    }
</style>
