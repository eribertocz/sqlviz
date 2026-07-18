<script lang="ts">
    import type { FilterControl, FilterDomain } from '$lib/types';
    import FilterControlComponent from './FilterControl.svelte';

    let { controls, filterVals, domains = {}, onChange }: {
        controls: FilterControl[];
        filterVals: Record<string, unknown>;
        domains?: Record<string, FilterDomain>;
        onChange: (varName: string, value: unknown) => void;
    } = $props();
</script>

<div class="filter-bar" role="group" aria-label="Dashboard filters">
    <span class="filter-bar-icon" aria-hidden="true">⊟</span>
    <div class="filter-bar-controls">
        {#each controls as control (control.variable)}
            <FilterControlComponent {control} {filterVals} domain={domains[control.variable]} {onChange} />
            <!-- Separator between controls (not after the last one) -->
        {/each}
    </div>
</div>

<style>
    .filter-bar {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0 1rem;
        height: 44px;
        background: var(--sqlviz-bg-surface);
        border-bottom: 1px solid var(--sqlviz-border);
        flex-shrink: 0;
        overflow-x: auto;
        overflow-y: hidden;
        /* Hide scrollbar but keep scroll functionality */
        scrollbar-width: none;
    }

    .filter-bar::-webkit-scrollbar { display: none; }

    .filter-bar-icon {
        color: var(--sqlviz-text-muted);
        font-size: 0.875rem;
        flex-shrink: 0;
        opacity: 0.6;
        user-select: none;
    }

    .filter-bar-controls {
        display: flex;
        align-items: center;
        gap: 1.25rem;
        flex: 1;
        min-width: 0;
    }
</style>
