<script lang="ts">
    let { panelId, onEditSQL, onExplain, onDelete }: {
        panelId: string;
        onEditSQL?: (id: string) => void;
        onExplain?: (id: string) => void;
        onDelete?: (id: string) => void;
    } = $props();

    let open = $state(false);

    function toggle(e: MouseEvent) {
        e.stopPropagation();
        open = !open;
    }

    function closeMenu() {
        open = false;
    }

    function handleEditSQL(e: MouseEvent) {
        e.stopPropagation();
        open = false;
        onEditSQL?.(panelId);
    }

    function handleExplain(e: MouseEvent) {
        e.stopPropagation();
        open = false;
        onExplain?.(panelId);
    }

    function handleDelete(e: MouseEvent) {
        e.stopPropagation();
        open = false;
        onDelete?.(panelId);
    }
</script>

<!-- Close the menu when anything outside the component is clicked -->
<svelte:window onclick={closeMenu} />

<div class="overflow-host">
    <button
        class="overflow-trigger"
        class:active={open}
        onclick={toggle}
        title="Panel options"
        aria-label="Panel options"
    >···</button>

    {#if open}
        <!-- stopPropagation on the menu so window click doesn't immediately close it -->
        <div class="overflow-menu" role="menu" tabindex="-1" onclick={(e) => e.stopPropagation()} onkeydown={(e) => e.stopPropagation()}>
            <button class="menu-item" onclick={handleEditSQL}>
                Edit SQL
            </button>
            <button class="menu-item" onclick={handleExplain}>
                Explain…
            </button>
            <div class="menu-divider"></div>
            <button class="menu-item danger" onclick={handleDelete}>
                Delete
            </button>
        </div>
    {/if}
</div>

<style>
    .overflow-host {
        position: relative;
    }

    .overflow-trigger {
        background: none;
        border: none;
        cursor: pointer;
        padding: 0.1875rem 0.375rem;
        border-radius: var(--sqlviz-radius);
        color: var(--sqlviz-text-muted);
        font-size: 1rem;
        line-height: 1;
        letter-spacing: 0.1em;
        transition: background 0.15s, color 0.15s;
        display: flex;
        align-items: center;
    }

    .overflow-trigger:hover,
    .overflow-trigger.active {
        background: var(--sqlviz-bg-base);
        color: var(--sqlviz-text);
    }

    .overflow-menu {
        position: absolute;
        top: calc(100% + 4px);
        right: 0;
        min-width: 140px;
        background: var(--sqlviz-bg-surface);
        border: 1px solid var(--sqlviz-border);
        border-radius: var(--sqlviz-radius-lg);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        z-index: 100;
        overflow: hidden;
        padding: 0.25rem 0;
    }

    .menu-item {
        display: block;
        width: 100%;
        padding: 0.4375rem 0.875rem;
        text-align: left;
        background: none;
        border: none;
        cursor: pointer;
        font-size: 0.8125rem;
        color: var(--sqlviz-text);
        transition: background 0.1s;
        white-space: nowrap;
    }

    .menu-item:hover {
        background: var(--sqlviz-bg-base);
    }

    .menu-item.danger {
        color: var(--sqlviz-negative);
    }

    .menu-divider {
        height: 1px;
        background: var(--sqlviz-border);
        margin: 0.25rem 0;
    }
</style>
