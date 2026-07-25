<script lang="ts">
    import * as Popover from '$lib/components/ui/popover/index.js';
    import { PALETTES } from '$lib/charts/palettes';
    import PaletteIcon from '@lucide/svelte/icons/palette';
    import CheckIcon from '@lucide/svelte/icons/check';

    // Prop-driven so admin (dashboard store) and viewer (local state) reuse it.
    let { value, onSelect }: { value: string; onSelect: (id: string) => void } = $props();

    let open = $state(false);
    const activeId = $derived(value);

    function pick(id: string) {
        onSelect(id);
        open = false;
    }
</script>

<Popover.Root bind:open>
    <Popover.Trigger class="palette-btn" aria-label="Chart palette" title="Chart palette">
        <PaletteIcon class="size-4" />
    </Popover.Trigger>
    <Popover.Content class="w-60 p-2" align="end">
        <p class="pal-head">Dashboard palette</p>
        {#each PALETTES as p (p.id)}
            <button class="pal-row" class:active={p.id === activeId} onclick={() => pick(p.id)}>
                <span class="pal-swatches">
                    {#each p.colors.slice(0, 6) as c}
                        <span class="pal-dot" style="background:{c}"></span>
                    {/each}
                </span>
                <span class="pal-name">{p.name}</span>
                {#if p.id === activeId}<CheckIcon class="size-4 pal-check" />{/if}
            </button>
        {/each}
    </Popover.Content>
</Popover.Root>

<style>
    :global(.palette-btn) {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        border: none;
        background: none;
        border-radius: var(--sqlviz-radius);
        cursor: pointer;
        color: var(--sqlviz-text-muted);
        transition: background 0.15s, color 0.15s;
    }
    :global(.palette-btn:hover) { background: var(--sqlviz-bg-base); color: var(--sqlviz-text); }

    .pal-head {
        margin: 0 0 0.375rem;
        padding: 0 0.25rem;
        font-size: 0.6875rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--sqlviz-text-muted);
    }
    .pal-row {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        width: 100%;
        padding: 0.375rem 0.5rem;
        background: none;
        border: none;
        border-radius: var(--sqlviz-radius);
        cursor: pointer;
        color: var(--sqlviz-text);
    }
    .pal-row:hover { background: var(--sqlviz-bg-base); }
    .pal-row.active { background: color-mix(in srgb, var(--sqlviz-primary) 12%, transparent); }
    .pal-swatches { display: inline-flex; gap: 2px; flex-shrink: 0; }
    .pal-dot { width: 12px; height: 12px; border-radius: 3px; }
    .pal-name { flex: 1; text-align: left; font-size: 0.8125rem; }
    :global(.pal-check) { color: var(--sqlviz-primary); }
</style>
