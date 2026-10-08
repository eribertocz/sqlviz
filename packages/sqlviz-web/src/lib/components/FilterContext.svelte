<script lang="ts">
    import { Dialog } from 'bits-ui';
    import SlidersHorizontal from '@lucide/svelte/icons/sliders-horizontal';
    import ChevronDown from '@lucide/svelte/icons/chevron-down';
    import X from '@lucide/svelte/icons/x';
    import LoaderCircle from '@lucide/svelte/icons/loader-circle';
    import FilterControlComponent from './FilterControl.svelte';
    import FilterViews from './FilterViews.svelte';
    import { copyFilterValues, filterSummary, sameFilterValue, type FilterValues } from '$lib/filters/filterContext';
    import type { FilterControl, FilterDomain } from '$lib/types';

    let { dashboardId, controls, values, domains, busy = false, error = null, disabled = false, onApply }: {
        dashboardId: string | null;
        controls: FilterControl[];
        values: FilterValues;
        domains: Record<string, FilterDomain>;
        busy?: boolean;
        error?: string | null;
        disabled?: boolean;
        onApply: (values: FilterValues) => Promise<boolean>;
    } = $props();
    let open = $state(false);
    let draft = $state<FilterValues>({});
    let saving = $state(false);
    let trigger = $state<HTMLButtonElement | null>(null);
    const applied = $derived(filterSummary(controls, values));
    const changed = $derived([...new Set([...Object.keys(draft), ...Object.keys(values)])]
        .some(key => !sameFilterValue(draft[key], values[key])));
    const summary = $derived(applied.map(item => `${item.label}: ${item.value}`).join('; ') || 'All values');

    function changeOpen(value: boolean) {
        if (value) draft = copyFilterValues(values);
        open = value;
    }
    function preset(values: FilterValues) {
        // The runtime validates current bindings before executing a saved snapshot.
        draft = copyFilterValues(values);
    }
    async function submit() {
        if (busy || saving || disabled) return;
        saving = true;
        try { if (await onApply(copyFilterValues(draft))) open = false; }
        finally { saving = false; }
    }
</script>

{#if controls.length}
    <Dialog.Root {open} onOpenChange={changeOpen}>
        <Dialog.Trigger bind:ref={trigger} class="filter-context-trigger" {disabled}
            aria-label={`Dashboard filters: ${summary}${busy ? '. Updating; charts show previous filters.' : error ? '. Update failed.' : ''}`}
            title={summary}>
            {#if busy}<LoaderCircle size={14} class="filter-spin" />{:else}<SlidersHorizontal size={14} />{/if}
            <span class="context-label">{busy ? 'Updating' : error ? 'Retry filters' : 'Filters'}</span>
            {#if applied.length && !busy && !error}<span class="context-preview">{applied[0].label}: {applied[0].value}</span>{/if}
            {#if applied.length}<span class="context-count">{applied.length}</span>{/if}
            <ChevronDown size={12} />
        </Dialog.Trigger>
        <span class="sr-only" role="status">{busy ? 'Updating charts. Previous filters are still applied.' : error ? `Filter update failed. ${error}` : `Applied filters: ${summary}`}</span>
        <Dialog.Portal>
            <Dialog.Overlay class="filter-context-backdrop" />
            <Dialog.Content class="filter-context-panel"
                onCloseAutoFocus={(event) => {
                    event.preventDefault();
                    const active = document.activeElement;
                    if (trigger?.isConnected && (active === document.body || active === trigger
                        || active?.closest('.filter-context-panel'))) trigger.focus();
                }}>
                <div class="context-heading">
                    <div><Dialog.Title class="context-title">Filters</Dialog.Title>
                        <Dialog.Description class="context-description">Adjust your view. Changes apply together.</Dialog.Description></div>
                    <Dialog.Close class="context-close" aria-label="Close filters"><X size={18} /></Dialog.Close>
                </div>
                <div class="context-scroll">
                    <section class="applied-context" aria-label="Applied filters">
                        <h3>Currently applied</h3>
                        {#if applied.length}
                            <dl>{#each applied as item}<div><dt>{item.label}</dt><dd>{item.value}</dd></div>{/each}</dl>
                        {:else}<p>All values</p>{/if}
                    </section>
                    {#if busy}<p class="context-notice" role="status">Updating charts. Previous filters remain applied until all affected charts are ready.</p>{/if}
                    {#if error}<p class="context-error" role="alert">{error} Previous charts and filters are unchanged.</p>{/if}
                    <fieldset disabled={busy || saving || disabled} class="context-fields">
                        <legend class="sr-only">Filter values to apply</legend>
                        {#each controls as control (control.variable)}
                            <div class="context-field">
                                <FilterControlComponent {control} filterVals={draft} domain={domains[control.variable]}
                                    onChange={(key, value) => { draft = { ...draft, [key]: value }; }} />
                            </div>
                        {/each}
                        <div class="context-presets">
                            <FilterViews {dashboardId} currentValues={draft} onApply={preset} label="Saved filters" />
                            <p>Saved in this browser. Select, then apply.</p>
                        </div>
                    </fieldset>
                </div>
                <div class="context-footer">
                    <button class="context-reset" disabled={busy || saving} onclick={() => { draft = {}; }} title="Remove all editable filters">Clear all</button>
                    <div><Dialog.Close class="context-cancel">Cancel</Dialog.Close>
                        <button class="context-apply" disabled={busy || saving || disabled || (!changed && !error)} onclick={submit}>
                            {busy || saving ? 'Applying…' : 'Apply filters'}
                        </button></div>
                </div>
            </Dialog.Content>
        </Dialog.Portal>
    </Dialog.Root>
{/if}

<style>
    :global(.filter-context-trigger) { display: inline-flex; align-items: center; justify-content: center; gap: 0.5rem; height: 34px; padding: 0 0.625rem; flex-shrink: 0; border: 1px solid var(--sqlviz-hairline); border-radius: 9px; color: var(--sqlviz-text); background: transparent; font-size: 0.8125rem; cursor: pointer; }
    :global(.filter-context-trigger:hover:enabled) { background: var(--sqlviz-bg-base); border-color: var(--sqlviz-border); }
    :global(.filter-context-trigger:disabled) { opacity: 0.5; cursor: default; }
    .context-count { font-size: 0.6875rem; min-width: 17px; padding: 1px 4px; border-radius: 4px; background: var(--sqlviz-bg-base); font-variant-numeric: tabular-nums; }
    .context-preview { max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--sqlviz-text-muted); font-size: 0.75rem; }
    :global(.filter-context-backdrop) { position: fixed; inset: 0; z-index: 40; background: rgb(0 0 0 / 20%); }
    :global(.filter-context-panel) { position: fixed; z-index: 41; top: 12px; bottom: 12px; right: 12px; width: min(400px, calc(100vw - 24px)); display: flex; flex-direction: column; background: var(--sqlviz-bg-surface); color: var(--sqlviz-text); border: 1px solid var(--sqlviz-border); border-radius: 16px; box-shadow: var(--sqlviz-shadow-drawer); outline: none; animation: context-enter 150ms ease-out; }
    .context-heading { display: flex; align-items: flex-start; justify-content: space-between; padding: 22px 20px 18px; gap: 12px; }
    :global(.context-title) { font-size: 1rem; font-weight: 600; margin: 0; letter-spacing: -0.02em; }
    :global(.context-description) { font-size: 0.8125rem; color: var(--sqlviz-text-muted); margin: 5px 0 0; }
    :global(.context-close) { display: flex; align-items: center; justify-content: center; width: 32px; height: 32px; border: 0; border-radius: 8px; background: transparent; color: var(--sqlviz-text-muted); cursor: pointer; flex-shrink: 0; }
    .context-scroll { overflow-y: auto; min-height: 0; flex: 1; padding: 0 20px 20px; }
    .applied-context { padding: 12px; border-radius: 10px; background: var(--sqlviz-bg-base); margin-bottom: 22px; }
    .applied-context h3 { font-size: 0.6875rem; font-weight: 500; color: var(--sqlviz-text-muted); margin: 0 0 8px; }
    .applied-context p, .applied-context dl { margin: 0; font-size: 0.8125rem; }
    .applied-context dl > div { display: flex; justify-content: space-between; gap: 16px; margin-top: 6px; }
    .applied-context dt { color: var(--sqlviz-text-muted); overflow-wrap: anywhere; }
    .applied-context dd { margin: 0; text-align: right; overflow-wrap: anywhere; }
    .context-fields { border: 0; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 22px; min-width: 0; }
    .context-fields:disabled { opacity: 0.6; }
    .context-field :global(.filter-control) { align-items: flex-start; flex-direction: column; width: 100%; }
    .context-field :global(.filter-label) { color: var(--sqlviz-text); text-transform: none; letter-spacing: 0; font-size: 0.8125rem; font-weight: 500; white-space: normal; }
    .context-field :global(.filter-control > input), .context-field :global(.filter-control > button:not(.filter-clear)) { width: 100%; min-height: 36px; }
    .context-presets { border-top: 1px solid var(--sqlviz-hairline); padding-top: 16px; }
    .context-presets p { font-size: 0.6875rem; color: var(--sqlviz-text-muted); margin: 7px 0 0; }
    .context-notice, .context-error { font-size: 0.8125rem; line-height: 1.5; margin: 0 0 18px; }
    .context-notice { color: var(--sqlviz-text-muted); }
    .context-error { color: var(--sqlviz-negative); }
    .context-footer { display: flex; align-items: center; justify-content: space-between; gap: 8px; border-top: 1px solid var(--sqlviz-hairline); padding: 16px 20px; flex-shrink: 0; }
    .context-footer > div { display: flex; gap: 8px; }
    .context-footer button, :global(.context-cancel) { min-height: 36px; border: 0; padding: 0 10px; border-radius: 8px; cursor: pointer; font-size: 0.8125rem; }
    .context-reset, :global(.context-cancel) { color: var(--sqlviz-text-muted); background: transparent; }
    .context-apply { color: var(--sqlviz-bg-surface); background: var(--sqlviz-text); font-weight: 500; }
    .context-footer button:disabled { opacity: 0.45; cursor: default; }
    :global(.filter-context-trigger:focus-visible), :global(.context-close:focus-visible), :global(.context-cancel:focus-visible), .context-footer button:focus-visible { outline: 2px solid var(--sqlviz-primary); outline-offset: 2px; }
    :global(.filter-spin) { animation: context-spin 1s linear infinite; }
    @keyframes context-spin { to { transform: rotate(360deg); } }
    @keyframes context-enter { from { opacity: 0; transform: translateX(8px); } to { opacity: 1; transform: translateX(0); } }
    @media (max-width: 600px) { .context-preview { display: none; } :global(.filter-context-panel) { top: 8px; bottom: 8px; right: 8px; width: calc(100vw - 16px); border-radius: 14px; } .context-heading { padding: 18px 16px; } .context-scroll { padding: 0 16px 16px; } .context-footer { padding: 14px 16px; } }
    @media (prefers-reduced-motion: reduce) { :global(.filter-context-panel), :global(.filter-spin) { animation: none; } }
</style>
