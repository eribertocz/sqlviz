<script lang="ts">
    import * as Popover from '$lib/components/ui/popover/index.js';
    import Ellipsis from '@lucide/svelte/icons/ellipsis';
    import PalettePicker from './PalettePicker.svelte';
    import ThemeToggle from './ThemeToggle.svelte';
    let { paletteId, onPalette, onEdit, onFocus }: {
        paletteId: string; onPalette: (value: string) => void;
        onEdit?: () => void; onFocus?: () => void;
    } = $props();
    let open = $state(false);
</script>

<Popover.Root bind:open>
    <Popover.Trigger class="viewer-options-trigger" aria-label="View options" title="View options"
        data-focus-recovery={onFocus ? '' : undefined}>
        <Ellipsis size={18} />
    </Popover.Trigger>
    <Popover.Content align="end" class="w-60 p-3 gap-3" role="dialog" aria-label="View options">
        {#if onFocus}<button class="library-option" aria-label="Enter focus mode" onclick={() => { open = false; onFocus?.(); }}>Focus mode</button>{/if}
        {#if onEdit}<button class="library-option" aria-label="Edit" onclick={() => { open = false; onEdit?.(); }}>Edit dashboard</button>{/if}
        <div class="appearance-option"><span>Chart colors</span><PalettePicker value={paletteId} onSelect={onPalette} /></div>
        <div class="appearance-option"><span>Appearance</span><ThemeToggle /></div>
    </Popover.Content>
</Popover.Root>

<style>
    :global(.viewer-options-trigger) { display: inline-flex; align-items: center; justify-content: center; width: 34px; height: 34px; flex-shrink: 0; color: var(--sqlviz-text-muted); background: transparent; border: 0; border-radius: 8px; cursor: pointer; }
    :global(.viewer-options-trigger:hover) { background: var(--sqlviz-bg-base); color: var(--sqlviz-text); }
    :global(.viewer-options-trigger:focus-visible), .library-option:focus-visible { outline: 2px solid var(--sqlviz-primary); outline-offset: 2px; }
    .library-option { display: flex; align-items: center; gap: 10px; width: 100%; border: 0; background: transparent; color: var(--sqlviz-text); text-align: left; font-size: 0.8125rem; padding: 8px 4px; border-radius: 6px; cursor: pointer; }
    .library-option:hover { background: var(--sqlviz-bg-base); }
    .appearance-option { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 4px; font-size: 0.8125rem; color: var(--sqlviz-text-muted); }
</style>
