<script lang="ts">
    import * as Popover from '$lib/components/ui/popover/index.js';
    import { Input } from '$lib/components/ui/input/index.js';
    import { Button } from '$lib/components/ui/button/index.js';
    import { filterViews, type FilterView } from '$lib/stores/filterViews.svelte';
    import BookmarkIcon from '@lucide/svelte/icons/bookmark';
    import XIcon from '@lucide/svelte/icons/x';

    // Prop-driven so it works for both the admin app and the anonymous viewer:
    // the caller supplies which dashboard id to key views by, the current filter
    // values to snapshot, and how to apply a view's values.
    let { dashboardId, currentValues, onApply }: {
        dashboardId: string | null;
        currentValues: Record<string, unknown>;
        onApply: (values: Record<string, unknown>) => void;
    } = $props();

    let open = $state(false);
    let name = $state('');

    const views = $derived(dashboardId ? filterViews.list(dashboardId) : []);

    function apply(v: FilterView) {
        onApply(v.values);
        open = false;
    }

    function saveCurrent() {
        const n = name.trim();
        if (!dashboardId || !n) return;
        filterViews.save(dashboardId, n, currentValues);
        name = '';
    }

    function remove(e: MouseEvent, v: FilterView) {
        e.stopPropagation();
        if (dashboardId) filterViews.remove(dashboardId, v.id);
    }
</script>

<Popover.Root bind:open>
    <Popover.Trigger class="views-pill" aria-label="Saved views">
        <BookmarkIcon class="size-3" />
        Views{#if views.length}<span class="views-count">{views.length}</span>{/if}
    </Popover.Trigger>
    <Popover.Content class="w-64 p-2" align="end">
        {#if views.length}
            <div class="views-list">
                {#each views as v (v.id)}
                    <div class="view-row">
                        <button class="view-apply" onclick={() => apply(v)} title="Apply view">
                            {v.name}
                        </button>
                        <button class="view-del" onclick={(e) => remove(e, v)} aria-label="Delete view">
                            <XIcon class="size-3" />
                        </button>
                    </div>
                {/each}
            </div>
            <div class="views-sep"></div>
        {:else}
            <p class="views-empty">Save the current filters as a reusable view.</p>
        {/if}
        <div class="views-save">
            <Input
                class="h-8 text-xs"
                placeholder="Save current as…"
                bind:value={name}
                onkeydown={(e) => e.key === 'Enter' && saveCurrent()}
            />
            <Button size="sm" onclick={saveCurrent} disabled={!name.trim()}>Save</Button>
        </div>
    </Popover.Content>
</Popover.Root>

<style>
    :global(.views-pill) {
        display: inline-flex;
        align-items: center;
        gap: 0.375rem;
        padding: 3px 10px;
        font-size: 11px;
        font-weight: 600;
        color: var(--sqlviz-text-muted);
        background: transparent;
        border: 1px dashed var(--sqlviz-border);
        border-radius: 100px;
        cursor: pointer;
        white-space: nowrap;
        transition: border-color 0.12s, color 0.12s;
    }
    :global(.views-pill:hover) { border-color: var(--sqlviz-primary); color: var(--sqlviz-text); }

    .views-count {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 15px;
        height: 15px;
        padding: 0 4px;
        font-size: 10px;
        border-radius: 100px;
        background: color-mix(in srgb, var(--sqlviz-primary) 18%, transparent);
        color: var(--sqlviz-primary);
    }

    .views-list { display: flex; flex-direction: column; gap: 1px; }
    .view-row { display: flex; align-items: center; border-radius: var(--sqlviz-radius); }
    .view-row:hover { background: var(--sqlviz-bg-base); }
    .view-apply {
        flex: 1;
        min-width: 0;
        text-align: left;
        padding: 0.375rem 0.5rem;
        font-size: 0.8125rem;
        color: var(--sqlviz-text);
        background: none;
        border: none;
        cursor: pointer;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .view-del {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 24px;
        height: 24px;
        margin-right: 0.25rem;
        color: var(--sqlviz-text-muted);
        background: none;
        border: none;
        border-radius: var(--sqlviz-radius);
        cursor: pointer;
    }
    .view-del:hover { color: var(--sqlviz-negative); background: var(--sqlviz-border); }

    .views-sep { height: 1px; margin: 0.375rem 0; background: var(--sqlviz-hairline); }
    .views-empty {
        margin: 0 0 0.375rem;
        padding: 0.25rem 0.5rem;
        font-size: 0.75rem;
        line-height: 1.4;
        color: var(--sqlviz-text-muted);
    }
    .views-save { display: flex; align-items: center; gap: 0.375rem; }
</style>
