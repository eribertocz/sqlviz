<script lang="ts">
    import { resolveDashboardIcon } from '$lib/dashboardIcons';
    import type { DashboardInfo } from '$lib/types';

    export interface DashboardSidebarItem extends DashboardInfo {}

    let { items, activeId = null, onSelect }: {
        items: DashboardSidebarItem[];
        activeId?: string | null;
        onSelect?: (id: string) => void;
    } = $props();

    let listEl: HTMLUListElement;

    // Roving tabindex: only the active (or first, if none active) item is
    // tabbable; Arrow/Home/End move focus between items.
    function isTabbable(item: DashboardSidebarItem, i: number): boolean {
        return activeId ? item.id === activeId : i === 0;
    }

    function handleKeydown(e: KeyboardEvent, idx: number) {
        let next = idx;
        if (e.key === 'ArrowDown')      next = Math.min(idx + 1, items.length - 1);
        else if (e.key === 'ArrowUp')   next = Math.max(idx - 1, 0);
        else if (e.key === 'Home')      next = 0;
        else if (e.key === 'End')       next = items.length - 1;
        else return;

        e.preventDefault();
        listEl.querySelectorAll<HTMLButtonElement>('.panel-item')[next]?.focus();
    }
</script>

<nav class="dashboard-sidebar" aria-label="Dashboard navigation">
    <div class="sidebar-label" id="dashboard-sidebar-label">Dashboards</div>
    <ul class="panel-list" bind:this={listEl} role="listbox" aria-labelledby="dashboard-sidebar-label">
        {#each items as item, i (item.id)}
            {@const IconCmp = resolveDashboardIcon(item.dashboard_hint, item.dashboard_domain)}
            <li role="presentation">
                <button
                    class="panel-item"
                    role="option"
                    aria-selected={item.id === activeId}
                    tabindex={isTabbable(item, i) ? 0 : -1}
                    class:active={item.id === activeId}
                    onclick={() => onSelect?.(item.id)}
                    onkeydown={(e) => handleKeydown(e, i)}
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
        border-right: 1px solid var(--sqlviz-hairline);
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
