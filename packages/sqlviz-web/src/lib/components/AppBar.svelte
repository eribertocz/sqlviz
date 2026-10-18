<script lang="ts">
    import { ChevronDown, Code2, Eye, Loader2, Maximize2, RotateCcw, Search, Share2 } from 'lucide-svelte';
    import NavigationToggle from '$lib/components/NavigationToggle.svelte';
    import FilterContext from '$lib/components/FilterContext.svelte';
    import ViewerDashboardSwitcher from '$lib/components/ViewerDashboardSwitcher.svelte';
    import ViewerOptions from '$lib/components/ViewerOptions.svelte';
    import PalettePicker from '$lib/components/PalettePicker.svelte';
    import ShareModal from '$lib/components/ShareModal.svelte';
    import * as Tooltip from '$lib/components/ui/tooltip/index.js';
    import { dashboardStore } from '$lib/stores/dashboardStore.svelte';
    import { editMode } from '$lib/stores/editMode';
    import { executionStore } from '$lib/stores/executionStore.svelte';
    import { filterValues } from '$lib/stores/filterValues.svelte';
    import { uiStore } from '$lib/stores/uiStore.svelte';

    let { onOpenCommands, readerSearchOpen = $bindable(false) }: { onOpenCommands: () => void; readerSearchOpen?: boolean } = $props();
    const folderName = $derived(
        dashboardStore.folders.find(f => f.id === dashboardStore.activeDashboard?.folder_id)?.name ?? 'Workspace'
    );

    // Inline dashboard-name editing (UX spec §"Cambiar nombre").
    let editingName = $state(false);
    let nameValue = $state('');

    // Share modal (Section 4).
    let shareOpen = $state(false);

    function startEditName() {
        const d = dashboardStore.activeDashboard;
        if (!d) return;
        nameValue = d.name;
        editingName = true;
    }
    function commitName() {
        const d = dashboardStore.activeDashboard;
        if (d && nameValue.trim() && nameValue.trim() !== d.name) {
            dashboardStore.renameDashboard(d.id, nameValue);
        }
        editingName = false;
    }
    function nameKeydown(e: KeyboardEvent) {
        if (e.key === 'Enter') { e.preventDefault(); commitName(); }
        else if (e.key === 'Escape') { e.preventDefault(); editingName = false; }
    }
    function selectOnMount(node: HTMLInputElement) { node.focus(); node.select(); }

    // Subtle save/run status shown only in the header (UX spec §"Estados visuales").
    type Status = { text: string; kind: 'draft' | 'saving' | 'saved' | 'running' | 'error' } | null;
    const status = $derived.by<Status>(() => {
        if (executionStore.executing) return { text: 'Running', kind: 'running' };
        if (executionStore.errorMsg)  return { text: 'Error', kind: 'error' };
        if (executionStore.saveStatus === 'saving') return { text: 'Saving…', kind: 'saving' };
        if (executionStore.saveStatus === 'saved')  return { text: 'Saved', kind: 'saved' };
        if (executionStore.saveStatus === 'draft')  return { text: 'Draft', kind: 'draft' };
        return null;
    });
</script>

{#if !$editMode && dashboardStore.activeDashboard}
    <header class="app-bar reader-bar">
        <NavigationToggle expanded={!uiStore.sidebarCollapsed} onclick={uiStore.toggleSidebar} />
        <ViewerDashboardSwitcher compact bind:open={readerSearchOpen} activeId={dashboardStore.dashboardId} loading={executionStore.executing || dashboardStore.viewLoading}
            dashboards={dashboardStore.allDashboards.map(d => ({ id: d.id, name: d.name,
                folderName: dashboardStore.folders.find(f => f.id === d.folder_id)?.name ?? '' }))}
            onSelect={(id) => { void dashboardStore.loadDashboard(id); }} />
        <div class="reader-actions">
            {#if dashboardStore.hasFilters}
                {#key dashboardStore.dashboardId}<FilterContext dashboardId={dashboardStore.dashboardId}
                    controls={dashboardStore.allFilterControls} values={filterValues.current}
                    domains={dashboardStore.filterDomains} busy={dashboardStore.filterBusy}
                    error={dashboardStore.filterError} disabled={executionStore.executing || dashboardStore.viewLoading}
                    onApply={dashboardStore.applyFilters} />{/key}
            {/if}
            <ViewerOptions paletteId={dashboardStore.dashboardPaletteId} onPalette={dashboardStore.setDashboardPalette}
                onFocus={uiStore.toggleFocusMode} onEdit={() => editMode.set(true)} />
        </div>
    </header>
{:else}
<header class="app-bar">
    <div class="bar-left">
        <NavigationToggle expanded={!uiStore.sidebarCollapsed} onclick={uiStore.toggleSidebar} />
        <button class="workspace-context" onclick={onOpenCommands} aria-label="Switch dashboard" title="Switch dashboard">
            <span>{folderName}</span><ChevronDown size={12} />
        </button>
        {#if dashboardStore.activeDashboard}
            <span class="breadcrumb-separator" aria-hidden="true">/</span>
            {#if editingName}
                <input
                    class="dash-name-input"
                    bind:value={nameValue}
                    use:selectOnMount
                    onkeydown={nameKeydown}
                    onblur={commitName}
                    aria-label="Dashboard name"
                />
            {:else}
                <button
                    class="dash-name"
                    title="Click to rename"
                    onclick={startEditName}
                >{dashboardStore.activeDashboard.name}</button>
            {/if}

            {#if status}
                <span class="save-status" class:running={status.kind === 'running'} class:error={status.kind === 'error'}>
                    {#if status.kind === 'running'}
                        <Loader2 size={12} class="spin" />
                    {:else if status.kind === 'draft'}
                        <span class="dot" aria-hidden="true">●</span>
                    {/if}
                    {status.text}
                </span>
            {/if}

            {#if dashboardStore.canRestoreLastRun}
                <button
                    class="restore-btn"
                    onclick={dashboardStore.restoreLastRun}
                    title="Replace the draft with the SQL of the last successful run"
                >
                    <RotateCcw size={12} /> Restore last run
                </button>
            {/if}
        {/if}
    </div>

    {#if dashboardStore.activeDashboard && dashboardStore.hasFilters}
        {#key dashboardStore.dashboardId}<FilterContext dashboardId={dashboardStore.dashboardId}
            controls={dashboardStore.allFilterControls} values={filterValues.current}
            domains={dashboardStore.filterDomains} busy={dashboardStore.filterBusy}
            error={dashboardStore.filterError} disabled={executionStore.executing || dashboardStore.viewLoading}
            onApply={dashboardStore.applyFilters} />{/key}
    {/if}

    <div class="bar-right">
        <button class="command-search" onclick={onOpenCommands} aria-label="Search dashboards and commands" title="Search dashboards and commands (Ctrl or Cmd + K)">
            <Search size={15} />
            <span>Search dashboards & commands</span>
            <kbd>⌘ / Ctrl K</kbd>
        </button>
        <button class="focus-button" onclick={uiStore.toggleFocusMode} aria-label="Enter focus mode" title="Focus mode">
            <Maximize2 size={16} />
        </button>
        {#if dashboardStore.activeDashboard}
            <!-- Dashboard chart palette -->
            <PalettePicker
                value={dashboardStore.dashboardPaletteId}
                onSelect={dashboardStore.setDashboardPalette}
            />

            <Tooltip.Provider delayDuration={200}>
                <!-- Share — icon-only, 28x28, tooltip -->
                <Tooltip.Root>
                    <Tooltip.Trigger
                        class="icon-btn"
                        aria-label="Share"
                        onclick={() => (shareOpen = true)}
                    >
                        <Share2 size={16} />
                    </Tooltip.Trigger>
                    <Tooltip.Content>Share</Tooltip.Content>
                </Tooltip.Root>

                <!-- Preview / Edit — segmented control (GitHub-style) -->
                <div class="seg" role="group" aria-label="Dashboard mode">
                    <Tooltip.Root>
                        <Tooltip.Trigger
                            class="seg-btn {!$editMode ? 'active' : ''}"
                            aria-label="Preview"
                            aria-pressed={!$editMode}
                            onclick={() => editMode.set(false)}
                        >
                            <Eye size={16} />
                        </Tooltip.Trigger>
                        <Tooltip.Content>Preview</Tooltip.Content>
                    </Tooltip.Root>
                    <Tooltip.Root>
                        <Tooltip.Trigger
                            class="seg-btn seg-btn-r {$editMode ? 'active' : ''}"
                            aria-label="Edit"
                            aria-pressed={$editMode}
                            onclick={() => editMode.set(true)}
                        >
                            <Code2 size={16} />
                        </Tooltip.Trigger>
                        <Tooltip.Content>Edit</Tooltip.Content>
                    </Tooltip.Root>
                </div>
            </Tooltip.Provider>
        {/if}
    </div>
</header>
{/if}

<ShareModal
    bind:open={shareOpen}
    dashboardId={dashboardStore.activeDashboard?.id ?? null}
    dashboardName={dashboardStore.activeDashboard?.name ?? ''}
/>

<style>
    .reader-actions { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
    .reader-bar { padding-block: 8px; }

    .app-bar {
        min-height: 52px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.5rem;
        padding: 0 0.875rem;
        background: var(--sqlviz-bg-surface);
        border-bottom: 1px solid var(--sqlviz-hairline);
        flex-shrink: 0;
    }

    .bar-left {
        display: flex;
        align-items: center;
        gap: 0.625rem;
        min-width: 0;
        flex: 1;
        overflow: hidden;
    }


    .workspace-context {
        display: inline-flex;
        align-items: center;
        gap: 0.375rem;
        min-width: 0;
        max-width: 140px;
        height: 30px;
        padding: 0 0.375rem;
        border: none;
        border-radius: 6px;
        background: none;
        color: var(--sqlviz-text-muted);
        font-size: 0.8125rem;
        cursor: pointer;
    }
    .workspace-context span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .workspace-context:hover { background: var(--sqlviz-bg-base); color: var(--sqlviz-text); }
    .breadcrumb-separator { color: var(--sqlviz-text-muted); opacity: 0.4; }
    .command-search {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        height: 30px;
        padding: 0 0.625rem;
        border: 1px solid var(--sqlviz-hairline);
        border-radius: 7px;
        background: var(--sqlviz-bg-base);
        color: var(--sqlviz-text-muted);
        font-size: 0.75rem;
        cursor: pointer;
    }
    .command-search:hover { border-color: var(--sqlviz-border); color: var(--sqlviz-text); }
    .command-search kbd { margin-left: 1rem; font-family: inherit; font-size: 0.625rem; opacity: 0.6; }
    .focus-button {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 30px;
        height: 30px;
        border: none;
        border-radius: 6px;
        background: none;
        color: var(--sqlviz-text-muted);
        cursor: pointer;
    }
    .focus-button:hover { background: var(--sqlviz-bg-base); color: var(--sqlviz-text); }
    .workspace-context:focus-visible, .command-search:focus-visible, .focus-button:focus-visible {
        outline: 2px solid var(--sqlviz-primary);
        outline-offset: 2px;
    }
    @media (max-width: 1100px) {
        .command-search span, .command-search kbd { display: none; }
        .command-search { width: 30px; justify-content: center; padding: 0; }
    }

    /* Active dashboard name */
    .dash-name {
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--sqlviz-text);
        max-width: 200px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        border: none;
        background: none;
        border-radius: var(--sqlviz-radius);
        padding: 0.125rem 0.25rem;
        cursor: text;
        flex-shrink: 0;
        transition: color 0.12s;
    }
    .dash-name:hover { color: var(--sqlviz-primary); }

    .dash-name-input {
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--sqlviz-text);
        background: var(--sqlviz-bg);
        border: 1px solid var(--sqlviz-primary);
        border-radius: var(--sqlviz-radius);
        padding: 0.125rem 0.375rem;
        max-width: 220px;
        outline: none;
    }

    .save-status {
        display: inline-flex;
        align-items: center;
        gap: 0.3125rem;
        font-size: 0.6875rem;
        color: var(--sqlviz-text-muted);
        white-space: nowrap;
        flex-shrink: 0;
    }
    .save-status .dot { color: var(--sqlviz-primary); font-size: 0.625rem; line-height: 1; }
    .save-status.running { color: var(--sqlviz-primary); }
    .save-status.error { color: var(--sqlviz-negative); }
    .save-status :global(.spin) { animation: appbar-spin 0.8s linear infinite; }

    @keyframes appbar-spin { to { transform: rotate(360deg); } }

    .restore-btn {
        display: inline-flex;
        align-items: center;
        gap: 0.3125rem;
        height: 24px;
        padding: 0 0.5rem;
        font-size: 0.6875rem;
        font-weight: 500;
        color: var(--sqlviz-text-muted);
        background: none;
        border: 1px solid var(--sqlviz-border);
        border-radius: var(--sqlviz-radius);
        cursor: pointer;
        white-space: nowrap;
        flex-shrink: 0;
        transition: color 0.12s, border-color 0.12s, background 0.12s;
    }
    .restore-btn:hover {
        color: var(--sqlviz-primary);
        border-color: var(--sqlviz-primary);
        background: color-mix(in srgb, var(--sqlviz-primary) 8%, transparent);
    }

    /* Subtle vertical separator between the name and the filter chips */


    .bar-right {
        display: flex;
        align-items: center;
        gap: 0.375rem;
        flex-shrink: 0;
    }

    /* Share — borderless 28x28 icon button with tooltip */
    :global(.icon-btn) {
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
    :global(.icon-btn:hover) {
        background: var(--sqlviz-bg-base);
        color: var(--sqlviz-text);
    }

    /* Preview / Edit — segmented control: unified outer border, internal
       divider, active segment gets the accent tint. */
    .seg {
        display: inline-flex;
        align-items: stretch;
        border: 1px solid var(--sqlviz-border);
        border-radius: var(--sqlviz-radius);
        overflow: hidden;
    }
    :global(.seg-btn) {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 34px;
        height: 28px;
        border: none;
        background: none;
        cursor: pointer;
        color: var(--sqlviz-text-muted);
        transition: background 0.15s, color 0.15s;
    }
    :global(.seg-btn.seg-btn-r) { border-left: 1px solid var(--sqlviz-border); }
    :global(.seg-btn:hover:not(.active)) {
        background: var(--sqlviz-bg-base);
        color: var(--sqlviz-text);
    }
    :global(.seg-btn.active) {
        background: color-mix(in srgb, var(--sqlviz-primary) 15%, transparent);
        color: var(--sqlviz-primary);
    }
    @media (max-width: 600px) {
        .workspace-context, .breadcrumb-separator { display: none; }
        .app-bar { padding: 0.375rem 0.5rem; flex-wrap: wrap; }
        .bar-left { gap: 0.25rem; }
        .dash-name { max-width: 140px; flex-shrink: 1; }
        .dash-name-input { min-width: 0; width: 100%; }
        .save-status, .restore-btn { display: none; }
    }
</style>
