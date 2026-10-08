<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import DashboardGrid from '$lib/components/DashboardGrid.svelte';
    import FilterContext from '$lib/components/FilterContext.svelte';
    import ViewerOptions from '$lib/components/ViewerOptions.svelte';
    import { fetchFilterDomains } from '$lib/filters/filterDomains';
    import { createFilterRuntime, patchFilterResults } from '$lib/filters/filterRuntime.svelte';
    import NavigationPanel from '$lib/components/NavigationPanel.svelte';
    import NavigationToggle from '$lib/components/NavigationToggle.svelte';
    import ViewerDashboardSwitcher from '$lib/components/ViewerDashboardSwitcher.svelte';
    import SearchIcon from '@lucide/svelte/icons/search';
    import ThemeToggle from '$lib/components/ThemeToggle.svelte';
    import sqlvizIcon from '$lib/assets/sqlviz-icon.svg';
    import { resolveDashboardIcon } from '$lib/dashboardIcons';
    import { getPaletteById } from '$lib/charts/palettes';
    import { editMode } from '$lib/stores/editMode';
    import { uiStore } from '$lib/stores/uiStore.svelte';
    import type { ExecResult } from '$lib/api';
    import { createViewerClient, ViewerAccessError } from '$lib/viewerApi';
    import PanelLeftCloseIcon from '@lucide/svelte/icons/panel-left-close';
    import type { DashboardLayout, FilterControl, FilterDomain, InferenceResult } from '$lib/types';

    type ViewerState = 'loading' | 'locked' | 'unlocked' | 'error';
    type WsFolder = { id: string; name: string; parent_id: string | null; sort_order: number };
    type WsDashboard = {
        id: string; name: string; folder_id: string | null; sort_order: number;
        dashboard_hint: string | null; dashboard_domain: string | null; description: string | null;
    };
    type WorkspaceData = { folders: WsFolder[]; dashboards: WsDashboard[]; viewer_session?: string };
    type PanelInfo = { id: string; sql_content: string };

    let viewerState: ViewerState = $state('loading');
    let loadError: string | null = $state(null);
    let lockError: string | null = $state(null);
    let unlockPassword = $state('');
    let unlocking = $state(false);

    let folders: WsFolder[] = $state([]);
    let dashboards: WsDashboard[] = $state([]);
    let activeId: string | null = $state(null);
    let dashboardLoading = $state(false);
    let dashboardGeneration = 0;
    let switcherOpen = $state(false);
    const orderedDashboards = $derived(dashboards.slice().sort((a, b) => a.sort_order - b.sort_order));
    const destinations = $derived(orderedDashboards.map(d => ({
        id: d.id, name: d.name,
        folderName: folders.find(f => f.id === d.folder_id)?.name ?? '',
    })));
    let sidebarCollapsed = $state(true);
    let navigationSearch = $state('');
    const matchingDashboards = $derived(dashboards.filter(d => {
        const folder = folders.find(f => f.id === d.folder_id)?.name ?? '';
        return `${d.name} ${folder}`.toLocaleLowerCase().includes(navigationSearch.trim().toLocaleLowerCase());
    }));
    function setNavigationOpen(open: boolean) {
        sidebarCollapsed = !open;
        try { localStorage.setItem('sqlviz-viewer-navigation-hidden', open ? '0' : '1'); } catch { /* optional preference */ }
    }
    function openNavigationSearch() {
        if (dashboards.length < 2) return;
        switcherOpen = true;
    }
    function onNavigationKeydown(event: KeyboardEvent) {
        if (event.defaultPrevented || !(event.ctrlKey || event.metaKey) || event.altKey) return;
        if (event.target instanceof Element && event.target.closest('input, textarea, [contenteditable="true"]')) return;
        if (event.key.toLowerCase() === 'k') { event.preventDefault(); void openNavigationSearch(); }
        else if (event.key.toLowerCase() === 'b') { event.preventDefault(); setNavigationOpen(sidebarCollapsed); }
    }

    // Viewer-local chart palette (per-visitor, persisted per dashboard).
    let paletteId = $state('brand');
    const paletteColors = $derived(getPaletteById(paletteId).colors);
    const paletteKey = (id: string) => `sqlviz-viewer-palette:${id}`;
    function loadPalette(id: string) {
        try { paletteId = localStorage.getItem(paletteKey(id)) || 'brand'; }
        catch { paletteId = 'brand'; }
    }
    function setPalette(id: string) {
        paletteId = id;
        if (activeId) { try { localStorage.setItem(paletteKey(activeId), id); } catch { /* ignore */ } }
    }

    // Active-dashboard render state
    let layout: DashboardLayout | null = $state(null);
    let executedResults: ExecResult[] = $state([]);
    let viewerFilterValues: Record<string, unknown> = $state({});
    let viewerDomains: Record<string, FilterDomain> = $state({});

    const token = () => window.location.pathname.split('/').at(-1) ?? '';
    const viewer = createViewerClient(token);
    const apiPost = viewer.post;
    const recompose = viewer.recompose;
    const filterRuntime = createFilterRuntime({
        getScope: () => dashboardGeneration,
        getResults: () => executedResults,
        getValues: () => viewerFilterValues,
        execute: (id, variables) => apiPost(`/api/v1/panels/${id}/execute`, { variables }),
        commit: (results, values) => {
            if (layout) layout = patchFilterResults(layout, results);
            executedResults = results;
            viewerFilterValues = values;
        },
        onAccessFailure: handleAccessFailure,
    });
    onDestroy(() => filterRuntime.reset());


    function handleAccessFailure(error: unknown): boolean {
        if (!(error instanceof ViewerAccessError)) return false;
        dashboardGeneration += 1;
        dashboardLoading = false;
        switcherOpen = false;
        filterRuntime.reset();
        layout = null;
        executedResults = [];
        viewerDomains = {};
        viewerFilterValues = {};
        folders = [];
        dashboards = [];
        loadError = 'Workspace access has expired or was revoked. Open the link again.';
        viewerState = 'error';
        return true;
    }
    const activeName = $derived(dashboards.find(d => d.id === activeId)?.name ?? 'Dashboard');

    const nonEmptyFolders = $derived(
        folders.filter(f => dashboards.some(d => d.folder_id === f.id))
    );
    const ungrouped = $derived(
        dashboards.filter(d => !d.folder_id).sort((a, b) => a.sort_order - b.sort_order)
    );
    function inFolder(id: string): WsDashboard[] {
        return dashboards.filter(d => d.folder_id === id).sort((a, b) => a.sort_order - b.sort_order);
    }

    const allFilterControls = $derived.by(() => {
        const seen = new Set<string>();
        const controls: FilterControl[] = [];
        for (const r of executedResults) {
            for (const fc of r.inference_result.filter_controls) {
                if (!seen.has(fc.variable)) { seen.add(fc.variable); controls.push(fc); }
            }
        }
        return controls;
    });
    const hasFilters = $derived(allFilterControls.length > 0);

    // ── Navigation → execute the selected dashboard ────────────────────────────
    async function selectDashboard(id: string) {
        if (id === activeId || !dashboards.some(d => d.id === id)) return;
        const generation = ++dashboardGeneration;
        filterRuntime.reset();
        dashboardLoading = true;
        activeId = id;
        loadPalette(id);
        layout = null;
        viewerFilterValues = {};
        viewerDomains = {};
        executedResults = [];
        try {
            const panels = await apiGetJson<PanelInfo[]>(`/api/v1/panels?dashboard_id=${id}`);
            if (generation !== dashboardGeneration) return;
            await executeAllPanels(panels, generation);
        } catch (e) {
            if (handleAccessFailure(e)) return;
            if (generation !== dashboardGeneration) return;
            loadError = e instanceof Error ? e.message : 'Failed to load the dashboard.';
            viewerState = 'error';
        } finally {
            if (generation === dashboardGeneration) dashboardLoading = false;
        }
    }

    async function apiGetJson<T>(path: string): Promise<T> {
        return viewer.get<T>(path);
    }

    async function executeAllPanels(panels: PanelInfo[], generation: number): Promise<void> {
        const results: ExecResult[] = [];
        for (const panel of panels) {
            const exec = await apiPost<{ inference_result: InferenceResult; data: Record<string, unknown>[] }>(
                `/api/v1/panels/${panel.id}/execute`,
            );
            if (generation !== dashboardGeneration) return;
            results.push({ panel_id: panel.id, ...exec });
        }
        executedResults = results;
        const composed = await recompose(results);
        if (generation !== dashboardGeneration) return;
        layout = composed;
        await loadDomains(generation);
    }

    async function loadDomains(generation: number): Promise<void> {
        const isCurrent = () => generation === dashboardGeneration && viewerState === 'unlocked';
        const domains = await fetchFilterDomains({
            results: executedResults, isCurrent,
            fetch: (id, column, kind) => apiPost(`/api/v1/panels/${id}/filter-domain`, { column, kind }),
            onAccessFailure: handleAccessFailure,
        });
        if (isCurrent()) viewerDomains = domains;
    }

    function applyWorkspace(data: WorkspaceData) {
        folders = data.folders;
        dashboards = data.dashboards;
        viewerState = 'unlocked';
        if (dashboards.length > 0) {
            void selectDashboard(orderedDashboards[0].id);
        }
    }

    async function handleUnlock(e: SubmitEvent) {
        e.preventDefault();
        if (unlocking) return;
        unlocking = true;
        lockError = null;
        try {
            const resp = await fetch(`/view/workspace/${token()}/unlock`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
                body: JSON.stringify({ password: unlockPassword }),
            });
            if (!resp.ok) { lockError = 'Invalid password'; unlockPassword = ''; return; }
            const data = await resp.json() as WorkspaceData;
            viewer.setSession(data.viewer_session ?? '');
            unlockPassword = '';
            applyWorkspace(data);
        } catch {
            lockError = 'Could not reach the server.';
        } finally {
            unlocking = false;
        }
    }

    onMount(async () => {
        editMode.set(false);
        uiStore.initTheme();
        try { sidebarCollapsed = localStorage.getItem('sqlviz-viewer-navigation-hidden') !== '0'; } catch { /* optional preference */ }
        try {
            const resp = await fetch(`/view/workspace/${token()}`, {
                headers: { Accept: 'application/json' }, cache: 'no-store',
            });
            if (!resp.ok) { loadError = 'Workspace not found or link has expired.'; viewerState = 'error'; return; }
            const body = await resp.json() as { requires_password?: boolean } | WorkspaceData;
            if ('requires_password' in body && body.requires_password) { viewerState = 'locked'; return; }
            applyWorkspace(body as WorkspaceData);
        } catch (e) {
            loadError = e instanceof Error ? `Failed to load: ${e.message}` : 'Failed to load the workspace.';
            viewerState = 'error';
        }
    });
</script>

{#snippet dashboardRow(d: WsDashboard, onNavigate: () => void)}
    {@const Icon = resolveDashboardIcon(d.dashboard_hint, d.dashboard_domain)}
    <button class="ws-item" class:active={d.id === activeId} aria-current={d.id === activeId ? 'page' : undefined}
        onclick={() => { void selectDashboard(d.id); onNavigate(); }} title={d.description || d.name}>
        <Icon size={14} /><span class="ws-name">{d.name}</span>
    </button>
{/snippet}

<svelte:window onkeydown={onNavigationKeydown} />

<svelte:head><title>{activeName} — SQLviz</title></svelte:head>

{#if viewerState === 'loading'}
    <div class="viewer-center"><span class="viewer-spinner">⟳</span><span class="viewer-msg">Loading…</span></div>

{:else if viewerState === 'error'}
    <div class="viewer-center">
        <div class="auth-card">
            <div class="auth-logo">
                <img class="auth-logo-icon" src={sqlvizIcon} alt="" width="34" height="34" />
                <span class="auth-wordmark"><span class="brand-sql">SQL</span><span class="brand-viz">viz</span></span>
            </div>
            <p class="lock-hint">{loadError ?? 'An error occurred.'}</p>
        </div>
    </div>

{:else if viewerState === 'locked'}
    <div class="viewer-center">
        <div class="auth-card">
            <div class="auth-logo">
                <img class="auth-logo-icon" src={sqlvizIcon} alt="" width="34" height="34" />
                <span class="auth-wordmark"><span class="brand-sql">SQL</span><span class="brand-viz">viz</span></span>
            </div>
            <p class="lock-hint">This workspace is password protected.<br />Enter the password to continue.</p>
            <form class="auth-form" onsubmit={handleUnlock}>
                <label class="auth-label" for="unlock-pw">Password</label>
                <input id="unlock-pw" type="password" class="auth-input" bind:value={unlockPassword}
                    placeholder="Password" autocomplete="current-password" disabled={unlocking} />
                {#if lockError}<div class="auth-error" role="alert">{lockError}</div>{/if}
                <button type="submit" class="auth-btn" disabled={unlocking || unlockPassword.length === 0}>
                    {unlocking ? 'Unlocking…' : 'Unlock'}
                </button>
            </form>
        </div>
    </div>

{:else}
    <div class="ws-shell">
        <header class="viewer-bar">
            <NavigationToggle expanded={!sidebarCollapsed} onclick={() => setNavigationOpen(sidebarCollapsed)} />
            <ViewerDashboardSwitcher dashboards={destinations} {activeId} loading={dashboardLoading} compact
                bind:open={switcherOpen} onSelect={(id) => { void selectDashboard(id); }} />
            <div class="viewer-context-actions">
                {#if hasFilters}
                    {#key activeId}<FilterContext dashboardId={activeId} controls={allFilterControls}
                        values={viewerFilterValues} domains={viewerDomains} busy={filterRuntime.busy}
                        error={filterRuntime.error} disabled={dashboardLoading} onApply={filterRuntime.apply} />{/key}
                {/if}
                <ViewerOptions {paletteId} onPalette={setPalette} />
            </div>
        </header>
        <div class="ws-body-layout">
            <!-- Navigable sidebar -->
            <NavigationPanel open={!sidebarCollapsed} onOpenChange={setNavigationOpen}>
                {#snippet children(onNavigate, onClose, modal)}
                    <nav class="ws-sidebar" aria-label="Dashboard navigation">
                        <div class="ws-head">
                            <span class="library-title">Dashboards</span>
                            {#if modal}
                                <button class="hbtn" onclick={onClose} title="Hide navigation" aria-label="Hide navigation">
                                    <PanelLeftCloseIcon size={16} />
                                </button>
                            {/if}
                        </div>
                        <label class="ws-search">
                            <SearchIcon size={14} />
                            <input type="search" bind:value={navigationSearch} data-viewer-navigation-search
                                placeholder="Find a dashboard..." aria-label="Find a dashboard" />
                        </label>
                        <div class="ws-body">
                            {#if navigationSearch.trim()}
                                {#each matchingDashboards as d (d.id)}{@render dashboardRow(d, onNavigate)}{/each}
                                {#if matchingDashboards.length === 0}<p class="ws-empty" role="status">No matching dashboards.</p>{/if}
                            {:else}
                                {#each nonEmptyFolders as f (f.id)}
                                    <div class="ws-group"><span>{f.name}</span><span class="ws-group-line"></span></div>
                                    {#each inFolder(f.id) as d (d.id)}{@render dashboardRow(d, onNavigate)}{/each}
                                {/each}
                                {#if ungrouped.length > 0 && nonEmptyFolders.length > 0}<div class="ws-group-gap"></div>{/if}
                                {#each ungrouped as d (d.id)}{@render dashboardRow(d, onNavigate)}{/each}
                                {#if dashboards.length === 0}<p class="ws-empty">No dashboards.</p>{/if}
                            {/if}
                        </div>
                        <div class="ws-foot"><span class="foot-theme-label">Appearance</span><ThemeToggle /></div>
                    </nav>
                {/snippet}
            </NavigationPanel>

            <!-- Main column -->
            <div class="ws-main">
                <div class="ws-content" aria-busy={filterRuntime.busy}>
                    {#if dashboards.length === 0}
                        <div class="viewer-center-inner"><span class="viewer-msg">No dashboards have been shared.</span></div>
                    {:else if layout}
                        <DashboardGrid {layout} palette={paletteColors} />
                    {:else}
                        <div class="viewer-center-inner"><span class="viewer-spinner">⟳</span><span class="viewer-msg">Building dashboard…</span></div>
                    {/if}
                </div>
            </div>
        </div>
    </div>
{/if}

<style>
    .viewer-context-actions { margin-left: auto; display: flex; align-items: center; gap: 6px; flex-shrink: 0; }

    .viewer-center {
        min-height: 100vh; display: flex; flex-direction: column; align-items: center;
        justify-content: center; background: var(--sqlviz-bg); gap: 0.75rem; padding: 1.5rem;
    }
    .viewer-spinner { font-size: 2rem; animation: spin 1.2s linear infinite; display: inline-block; color: var(--sqlviz-text-muted); }
    @keyframes spin { to { transform: rotate(360deg); } }
    .viewer-msg { color: var(--sqlviz-text-muted); font-size: 0.9375rem; }

    .auth-card {
        width: 100%; max-width: 360px; background: var(--sqlviz-bg-surface);
        border: 1px solid var(--sqlviz-border); border-radius: var(--sqlviz-radius-lg);
        padding: 2rem 2rem 1.75rem; display: flex; flex-direction: column; gap: 1.25rem;
    }
    .auth-logo { display: flex; align-items: center; justify-content: center; gap: 0.625rem; }
    .auth-logo-icon { display: block; flex-shrink: 0; }
    .auth-wordmark {
        font-family: 'Geist Sans', var(--sqlviz-font-sans);
        font-size: 1.375rem; font-weight: 600; letter-spacing: -0.025em;
    }
    .lock-hint { margin: 0; font-size: 0.875rem; color: var(--sqlviz-text-muted); text-align: center; line-height: 1.5; }
    .auth-form { display: flex; flex-direction: column; gap: 0.75rem; }
    .auth-label { font-size: 0.8125rem; font-weight: 600; color: var(--sqlviz-text-muted); }
    .auth-input {
        width: 100%; height: 40px; padding: 0 0.875rem; background: var(--sqlviz-bg);
        border: 1px solid var(--sqlviz-border); border-radius: var(--sqlviz-radius);
        color: var(--sqlviz-text); font-size: 0.9375rem; outline: none; box-sizing: border-box;
    }
    .auth-input:focus { border-color: var(--sqlviz-primary); }
    .auth-error { font-size: 0.8125rem; color: var(--sqlviz-negative); padding: 0.375rem 0.625rem;
        background: color-mix(in srgb, var(--sqlviz-negative) 10%, transparent); border-radius: var(--sqlviz-radius); }
    .auth-btn {
        height: 40px; padding: 0 1rem; background: var(--sqlviz-primary); color: var(--sqlviz-on-primary);
        border: none; border-radius: var(--sqlviz-radius); font-size: 0.9375rem; font-weight: 600;
        cursor: pointer; margin-top: 0.25rem;
    }
    .auth-btn:disabled { opacity: 0.45; cursor: not-allowed; }

    /* Shell */
    .ws-shell { height: 100dvh; display: flex; flex-direction: column; background: var(--sqlviz-bg); overflow: hidden; }

    .ws-body-layout { flex: 1; display: flex; min-width: 0; min-height: 0; overflow: hidden; }

    .ws-sidebar {
        width: 100%; height: 100%; min-height: 0; display: flex; flex-direction: column;
        background: var(--sqlviz-bg-surface); overflow: hidden;
    }

    .ws-head {
        display: flex; align-items: center; justify-content: space-between; gap: 0.5rem;
        height: 52px; padding: 0 0.5rem 0 0.875rem; flex-shrink: 0; border-bottom: 1px solid var(--sqlviz-hairline);
    }

    .library-title { font-size: 0.8125rem; font-weight: 600; color: var(--sqlviz-text); }
    .brand-sql { color: var(--sqlviz-text-primary); font-weight: 600; }
    .brand-viz { color: var(--sqlviz-primary); font-weight: 600; }

    .hbtn {
        display: flex; align-items: center; justify-content: center; border: none; background: none;
        color: var(--sqlviz-text-muted); border-radius: var(--sqlviz-radius); cursor: pointer;
        transition: background 0.12s, color 0.12s;
    }
    .hbtn { width: 32px; height: 32px; }
    .hbtn:hover { background: var(--sqlviz-bg-base); color: var(--sqlviz-text); }

    .ws-body { flex: 1; overflow-y: auto; padding: 0.5rem 0.375rem; }
    .ws-group { display: flex; align-items: center; gap: 0.5rem; padding: 0.75rem 0.5rem 0.375rem; }
    .ws-group span:first-child {
        font-size: 0.6875rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;
        color: var(--sqlviz-text-muted); white-space: nowrap;
    }
    .ws-group-line { flex: 1; height: 1px; background: var(--sqlviz-hairline); }
    .ws-group-gap { height: 0.75rem; }
    .ws-item {
        display: flex; align-items: center; gap: 0.5rem; width: 100%; padding: 0.4375rem 0.5rem;
        background: none; border: none; border-radius: var(--sqlviz-radius); color: var(--sqlviz-text-muted);
        cursor: pointer; text-align: left; font-size: 0.8125rem; transition: background 0.12s, color 0.12s;
    }
    .ws-item:hover { background: var(--sqlviz-bg-base); color: var(--sqlviz-text); }
    .ws-item.active { background: color-mix(in srgb, var(--sqlviz-primary) 15%, transparent); color: var(--sqlviz-primary); }
    .ws-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

    .ws-empty { padding: 0.75rem 0.5rem; font-size: 0.75rem; color: var(--sqlviz-text-muted); }

    .ws-foot {
        display: flex; align-items: center; justify-content: space-between; height: 44px;
        padding: 0 0.75rem; border-top: 1px solid var(--sqlviz-hairline); flex-shrink: 0;
    }
    .foot-theme-label { font-size: 0.8125rem; color: var(--sqlviz-text-muted); }

    /* Main */
    .ws-main { flex: 1; display: flex; flex-direction: column; min-width: 0; overflow: hidden; }

    .viewer-bar {
        min-height: 52px; display: flex; align-items: center; gap: 0.625rem; padding: 0.5rem 0.875rem;
        background: var(--sqlviz-bg-surface); border-bottom: 1px solid var(--sqlviz-hairline); flex-shrink: 0;
    }

    .ws-content { flex: 1; overflow-y: auto; }
    .viewer-center-inner {
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        min-height: 200px; gap: 0.75rem;
    }
    .ws-search {
        display: flex; align-items: center; gap: 0.5rem; margin: 0.75rem 0.75rem 0;
        padding: 0.5rem; border: 1px solid var(--sqlviz-hairline); border-radius: 8px;
        color: var(--sqlviz-text-muted); background: var(--sqlviz-bg-base);
    }
    .ws-search:focus-within { border-color: var(--sqlviz-primary); box-shadow: var(--sqlviz-focus-ring); }
    .ws-search input:focus-visible { box-shadow: none; }
    .ws-search input { width: 100%; min-width: 0; border: 0; outline: none; background: none; color: var(--sqlviz-text); font: inherit; font-size: 0.75rem; }
    .hbtn:focus-visible, .ws-item:focus-visible { outline: 2px solid var(--sqlviz-primary); outline-offset: 2px; }
    @media (max-width: 600px) { .viewer-bar { padding-inline: 8px; gap: 6px; } }
</style>
