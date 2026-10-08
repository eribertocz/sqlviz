<script module lang="ts">
    export type DashboardDestination = { id: string; name: string; folderName: string };
</script>

<script lang="ts">
    import * as Popover from '$lib/components/ui/popover/index.js';
    import * as Command from '$lib/components/ui/command/index.js';
    import ChevronDown from '@lucide/svelte/icons/chevron-down';
    import ChevronLeft from '@lucide/svelte/icons/chevron-left';
    import ChevronRight from '@lucide/svelte/icons/chevron-right';
    import Check from '@lucide/svelte/icons/check';

    let { dashboards, activeId, loading = false, compact = false, open = $bindable(false), onSelect }: {
        dashboards: DashboardDestination[];
        activeId: string | null;
        loading?: boolean;
        compact?: boolean;
        open?: boolean;
        onSelect: (id: string) => void;
    } = $props();
    let searchInput = $state<HTMLInputElement | null>(null);
    let trigger = $state<HTMLButtonElement | null>(null);
    let returnToTrigger = false;
    const index = $derived(dashboards.findIndex(d => d.id === activeId));
    const active = $derived(dashboards[index]);
    const previous = $derived(index > 0 ? dashboards[index - 1] : undefined);
    const next = $derived(index >= 0 ? dashboards[index + 1] : undefined);

    function select(id: string) {
        if (loading) return;
        returnToTrigger = true;
        open = false;
        onSelect(id);
    }
</script>

<div class="viewer-switcher" role="group" aria-label="Dashboard switcher">
    {#if dashboards.length > 1}
        <Popover.Root bind:open>
            <Popover.Trigger bind:ref={trigger} class="dashboard-switch-trigger"
                aria-label={`Switch dashboard: ${active?.name ?? 'Dashboard'}`}
                title="Switch dashboard (Ctrl/Cmd+K)">
                <span class="dashboard-switch-name">{active?.name ?? 'Dashboard'}</span>
                <ChevronDown class="size-3.5 shrink-0 opacity-60" />
            </Popover.Trigger>
            <Popover.Content align="start" class="p-0 w-[360px] max-w-[calc(100vw-24px)]"
                role="dialog" aria-label="Choose a dashboard"
                onOpenAutoFocus={(event) => { returnToTrigger = false; event.preventDefault(); searchInput?.focus(); }}
                onEscapeKeydown={() => { returnToTrigger = true; }}
                onCloseAutoFocus={(event) => {
                    if (returnToTrigger) { event.preventDefault(); trigger?.focus(); returnToTrigger = false; }
                }}>
                <Command.Root label="Search shared dashboards" value={activeId ?? ''}>
                    <Command.Input bind:ref={searchInput} aria-label="Search shared dashboards"
                        placeholder="Search dashboards or groups..." />
                    <Command.List class="max-h-[min(320px,60dvh)]">
                        <Command.Empty>No matching dashboards.</Command.Empty>
                        <Command.Group heading="Shared dashboards">
                            {#each dashboards as dashboard (dashboard.id)}
                                <Command.Item value={dashboard.id}
                                    keywords={[dashboard.name, dashboard.folderName]}
                                    disabled={loading} onSelect={() => select(dashboard.id)}>
                                    <div class="min-w-0 flex-1">
                                        <span class="block truncate">{dashboard.name}</span>
                                        {#if dashboard.folderName}
                                            <span class="block truncate text-xs opacity-60">{dashboard.folderName}</span>
                                        {/if}
                                    </div>
                                    {#if dashboard.id === activeId}<Check class="size-4 shrink-0" />{/if}
                                </Command.Item>
                            {/each}
                        </Command.Group>
                    </Command.List>
                </Command.Root>
            </Popover.Content>
        </Popover.Root>
        {#if !compact}<div class="dashboard-stepper">
            <button aria-label="Previous dashboard" title={previous?.name ?? 'First dashboard'}
                disabled={loading || !previous} onclick={() => previous && select(previous.id)}>
                <ChevronLeft size={16} />
            </button>
            <span class="dashboard-position" aria-label={`Dashboard ${index + 1} of ${dashboards.length}`}>
                {index + 1}<span aria-hidden="true"> / </span>{dashboards.length}
            </span>
            <button aria-label="Next dashboard" title={next?.name ?? 'Last dashboard'}
                disabled={loading || !next} onclick={() => next && select(next.id)}>
                <ChevronRight size={16} />
            </button>
        </div>{/if}
    {:else}
        <span class="dashboard-switch-name">{active?.name ?? 'No dashboards'}</span>
    {/if}
</div>

<style>
    .viewer-switcher { display: flex; align-items: center; gap: 0.5rem; min-width: 0; flex: 1; }
    .dashboard-switch-name { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 0.875rem; font-weight: 600; }
    :global(.dashboard-switch-trigger) { display: flex; align-items: center; gap: 0.5rem; min-width: 0; padding: 0.375rem 0.5rem; border: 0; border-radius: 8px; background: transparent; color: var(--sqlviz-text); cursor: pointer; }
    :global(.dashboard-switch-trigger:hover) { background: var(--sqlviz-bg-base); }
    .dashboard-stepper { display: flex; align-items: center; flex-shrink: 0; gap: 0.125rem; }
    .dashboard-stepper button { width: 30px; height: 32px; display: flex; align-items: center; justify-content: center; border: 0; border-radius: 8px; color: var(--sqlviz-text-muted); background: transparent; cursor: pointer; }
    .dashboard-stepper button:hover:enabled { background: var(--sqlviz-bg-base); color: var(--sqlviz-text); }
    .dashboard-stepper button:disabled { opacity: 0.4; cursor: default; }
    .dashboard-stepper button:focus-visible, :global(.dashboard-switch-trigger:focus-visible) { outline: 2px solid var(--sqlviz-primary); outline-offset: 2px; }
    .dashboard-position { font-size: 0.6875rem; color: var(--sqlviz-text-muted); white-space: nowrap; font-variant-numeric: tabular-nums; }
    @media (max-width: 600px) { .viewer-switcher { flex: 1; } .dashboard-position { display: none; } }
</style>
