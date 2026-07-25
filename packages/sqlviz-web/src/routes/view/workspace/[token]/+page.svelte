<script lang="ts">
    import { onMount } from 'svelte';
    import DashboardGrid from '$lib/components/DashboardGrid.svelte';
    import FilterControlComponent from '$lib/components/FilterControl.svelte';
    import FilterViews from '$lib/components/FilterViews.svelte';
    import ThemeToggle from '$lib/components/ThemeToggle.svelte';
    import sqlvizIcon from '$lib/assets/sqlviz-icon.svg';
    import { resolveDashboardIcon } from '$lib/dashboardIcons';
    import { editMode } from '$lib/stores/editMode';
    import { uiStore } from '$lib/stores/uiStore.svelte';
    import { apiPost, recompose, type ExecResult } from '$lib/api';
    import PanelLeftCloseIcon from '@lucide/svelte/icons/panel-left-close';
    import type { DashboardLayout, FilterControl, FilterDomain, InferenceResult } from '$lib/types';

    type ViewerState = 'loading' | 'locked' | 'unlocked' | 'error';
    type WsFolder = { id: string; name: string; parent_id: string | null; sort_order: number };
    type WsDashboard = {
        id: string; name: string; folder_id: string | null; sort_order: number;
        dashboard_hint: string | null; dashboard_domain: string | null; description: string | null;
    };
    type WorkspaceData = { folders: WsFolder[]; dashboards: WsDashboard[] };
    type PanelInfo = { id: string; sql_content: string };

    let viewerState: ViewerState = $state('loading');
    let loadError: string | null = $state(null);
    let lockError: string | null = $state(null);
    let unlockPassword = $state('');
    let unlocking = $state(false);

    let folders: WsFolder[] = $state([]);
    let dashboards: WsDashboard[] = $state([]);
    let activeId: string | null = $state(null);
    let sidebarCollapsed = $state(false);

    // Active-dashboard render state
    let layout: DashboardLayout | null = $state(null);
    let panelIds: string[] = $state([]);
    let executedResults: ExecResult[] = $state([]);
    let viewerFilterValues: Record<string, unknown> = $state({});
    let viewerDomains: Record<string, FilterDomain> = $state({});
    let filterDebounceTimer = 0;

    const token = () => window.location.pathname.split('/').at(-1) ?? '';
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
        if (id === activeId) return;
        activeId = id;
        layout = null;
        viewerFilterValues = {};
        viewerDomains = {};
        executedResults = [];
        try {
            const panels = await apiGetJson<PanelInfo[]>(`/api/v1/panels?dashboard_id=${id}`);
            await executeAllPanels(panels);
        } catch (e) {
            loadError = e instanceof Error ? e.message : 'Failed to load the dashboard.';
            viewerState = 'error';
        }
    }

    async function apiGetJson<T>(path: string): Promise<T> {
        const r = await fetch(path, { headers: { Accept: 'application/json' } });
        if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
        return r.json() as Promise<T>;
    }

    async function executeAllPanels(panels: PanelInfo[]): Promise<void> {
        panelIds = panels.map(p => p.id);
        const results: ExecResult[] = [];
        for (const panel of panels) {
            const exec = await apiPost<{ inference_result: InferenceResult; data: Record<string, unknown>[] }>(
                `/api/v1/panels/${panel.id}/execute`,
            );
            results.push({ panel_id: panel.id, ...exec });
        }
        executedResults = results;
        layout = await recompose(results);
        await loadDomains();
    }

    async function loadDomains(): Promise<void> {
        const domains: Record<string, FilterDomain> = {};
        await Promise.all(
            executedResults.flatMap((r, i) =>
                r.inference_result.filter_controls.map(async (fc) => {
                    const kind = fc.control_type === 'dropdown' || fc.control_type === 'multiselect'
                        ? 'distinct'
                        : fc.control_type === 'range_slider' ? 'range' : null;
                    if (kind === null || domains[fc.variable]) return;
                    try {
                        domains[fc.variable] = await apiPost<FilterDomain>(
                            `/api/v1/panels/${panelIds[i]}/filter-domain`,
                            { column: fc.column_name, kind },
                        );
                    } catch { /* fall back to text input */ }
                })
            )
        );
        viewerDomains = domains;
    }

    function applyResultsToLayout(current: DashboardLayout, results: ExecResult[]): DashboardLayout {
        const byId = new Map(results.map(r => [r.panel_id, r]));
        return {
            ...current,
            rows: current.rows.map(row => ({
                panels: row.panels.map(p => {
                    const r = byId.get(p.panel_id);
                    return r ? { ...p, inference_result: r.inference_result, data: r.data } : p;
                }),
            })),
        };
    }

    async function executeFilteredPanels(changedVar: string, currentFV: Record<string, unknown>) {
        const updated = [...executedResults];
        let anyChanged = false;
        for (let i = 0; i < executedResults.length; i++) {
            const panelVars = executedResults[i].inference_result.filter_controls.flatMap(
                (fc: FilterControl) => fc.variable.split(',').map((v: string) => v.trim())
            );
            if (!panelVars.includes(changedVar)) continue;
            const variables = Object.fromEntries(panelVars.map((v: string) => [v, currentFV[v] ?? '']));
            try {
                const exec = await apiPost<{ inference_result: InferenceResult; data: Record<string, unknown>[] }>(
                    `/api/v1/panels/${panelIds[i]}/execute`, { variables },
                );
                updated[i] = { panel_id: panelIds[i], ...exec };
                anyChanged = true;
            } catch { /* keep existing */ }
        }
        if (!anyChanged) return;
        executedResults = updated;
        if (layout) layout = applyResultsToLayout(layout, updated);
        else { try { layout = await recompose(updated); } catch { /* keep */ } }
    }

    function handleFilterChange(varName: string, value: unknown) {
        viewerFilterValues = { ...viewerFilterValues, [varName]: value };
        clearTimeout(filterDebounceTimer);
        filterDebounceTimer = window.setTimeout(
            () => executeFilteredPanels(varName, { ...viewerFilterValues, [varName]: value }), 350,
        );
    }

    // ── Load workspace + unlock ────────────────────────────────────────────────
    function applyWorkspace(data: WorkspaceData) {
        folders = data.folders;
        dashboards = data.dashboards;
        viewerState = 'unlocked';
        if (dashboards.length > 0) {
            void selectDashboard(dashboards.slice().sort((a, b) => a.sort_order - b.sort_order)[0].id);
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
            applyWorkspace(await resp.json() as WorkspaceData);
        } catch {
            lockError = 'Could not reach the server.';
        } finally {
            unlocking = false;
        }
    }

    onMount(async () => {
        editMode.set(false);
        uiStore.initTheme();
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

<svelte:head><title>{activeName} — SQLviz</title></svelte:head>

{#if viewerState === 'loading'}
    <div class="viewer-center"><span class="viewer-spinner">⟳</span><span class="viewer-msg">Loading…</span></div>

{:else if viewerState === 'error'}
    <div class="viewer-center">
        <div class="auth-card">
            <div class="auth-logo">SQLviz</div>
            <p class="lock-hint">{loadError ?? 'An error occurred.'}</p>
        </div>
    </div>

{:else if viewerState === 'locked'}
    <div class="viewer-center">
        <div class="auth-card">
            <div class="auth-logo">SQLviz</div>
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
        <!-- Navigable sidebar -->
        <nav class="ws-sidebar" class:collapsed={sidebarCollapsed} aria-label="Dashboard navigation">
            <div class="ws-head" class:collapsed={sidebarCollapsed}>
                {#if !sidebarCollapsed}
                    <div class="brand">
                        <img class="brand-icon" src={sqlvizIcon} alt="" width="26" height="26" />
                        <span class="brand-name"><span class="brand-sql">SQL</span><span class="brand-viz">viz</span></span>
                    </div>
                    <button class="hbtn" onclick={() => (sidebarCollapsed = true)} title="Collapse sidebar" aria-label="Collapse sidebar">
                        <PanelLeftCloseIcon size={16} />
                    </button>
                {:else}
                    <button class="brand-btn" onclick={() => (sidebarCollapsed = false)} title="Expand sidebar" aria-label="Expand sidebar">
                        <img class="brand-icon" src={sqlvizIcon} alt="SQLviz" width="26" height="26" />
                    </button>
                {/if}
            </div>

            <div class="ws-body">
                {#if !sidebarCollapsed}
                    {#each nonEmptyFolders as f (f.id)}
                        <div class="ws-group">{f.name}</div>
                        {#each inFolder(f.id) as d (d.id)}
                            {@const Icon = resolveDashboardIcon(d.dashboard_hint, d.dashboard_domain)}
                            <button class="ws-item" class:active={d.id === activeId} onclick={() => selectDashboard(d.id)} title={d.name}>
                                <Icon size={14} /><span class="ws-name">{d.name}</span>
                            </button>
                        {/each}
                    {/each}
                    {#each ungrouped as d (d.id)}
                        {@const Icon = resolveDashboardIcon(d.dashboard_hint, d.dashboard_domain)}
                        <button class="ws-item" class:active={d.id === activeId} onclick={() => selectDashboard(d.id)} title={d.name}>
                            <Icon size={14} /><span class="ws-name">{d.name}</span>
                        </button>
                    {/each}
                    {#if dashboards.length === 0}<p class="ws-empty">No dashboards.</p>{/if}
                {:else}
                    {#each dashboards as d (d.id)}
                        {@const Icon = resolveDashboardIcon(d.dashboard_hint, d.dashboard_domain)}
                        <button class="ws-rail {d.id === activeId ? 'active' : ''}" onclick={() => selectDashboard(d.id)} title={d.name} aria-label={d.name}>
                            <Icon size={16} />
                        </button>
                    {/each}
                {/if}
            </div>

            <div class="ws-foot" class:collapsed={sidebarCollapsed}>
                {#if !sidebarCollapsed}<span class="foot-theme-label">Theme</span><ThemeToggle />{:else}<ThemeToggle compact />{/if}
            </div>
        </nav>

        <!-- Main column -->
        <div class="ws-main">
            <header class="viewer-bar">
                <span class="viewer-title">{activeName}</span>
                {#if hasFilters}
                    <span class="viewer-sep" aria-hidden="true"></span>
                    <div class="viewer-filters" role="group" aria-label="Dashboard filters">
                        {#each allFilterControls as control (control.variable)}
                            <FilterControlComponent {control} pill filterVals={viewerFilterValues}
                                domain={viewerDomains[control.variable]} onChange={handleFilterChange} />
                        {/each}
                        <FilterViews dashboardId={activeId} currentValues={viewerFilterValues}
                            onApply={(vals) => { for (const [k, v] of Object.entries(vals)) handleFilterChange(k, v); }} />
                    </div>
                {/if}
            </header>

            <div class="ws-content">
                {#if layout}
                    <DashboardGrid {layout} />
                {:else}
                    <div class="viewer-center-inner"><span class="viewer-spinner">⟳</span><span class="viewer-msg">Building dashboard…</span></div>
                {/if}
            </div>
        </div>
    </div>
{/if}

<style>
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
    .auth-logo { font-size: 1.375rem; font-weight: 800; color: var(--sqlviz-primary); letter-spacing: -0.03em; text-align: center; }
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
    .ws-shell { height: 100vh; display: flex; flex-direction: row; background: var(--sqlviz-bg); overflow: hidden; }

    .ws-sidebar {
        width: 240px; flex-shrink: 0; display: flex; flex-direction: column;
        background: var(--sqlviz-bg-surface); border-right: 1px solid var(--sqlviz-hairline);
        overflow: hidden; transition: width 0.2s ease;
    }
    .ws-sidebar.collapsed { width: 44px; }

    .ws-head {
        display: flex; align-items: center; justify-content: space-between; gap: 0.5rem;
        height: 44px; padding: 0 0.5rem 0 0.875rem; flex-shrink: 0; border-bottom: 1px solid var(--sqlviz-hairline);
    }
    .ws-head.collapsed { justify-content: center; padding: 0; }

    .brand { display: flex; align-items: center; gap: 0.5rem; min-width: 0; }
    .brand-icon { display: block; flex-shrink: 0; }
    .brand-name { font-size: 0.9375rem; letter-spacing: -0.01em; white-space: nowrap; overflow: hidden; }
    .brand-sql { color: var(--sqlviz-text-primary); font-weight: 600; }
    .brand-viz { color: #06b6d4; font-weight: 600; }

    .hbtn, .brand-btn {
        display: flex; align-items: center; justify-content: center; border: none; background: none;
        color: var(--sqlviz-text-muted); border-radius: var(--sqlviz-radius); cursor: pointer;
        transition: background 0.12s, color 0.12s;
    }
    .hbtn { width: 24px; height: 24px; }
    .brand-btn { width: 34px; height: 34px; }
    .hbtn:hover, .brand-btn:hover { background: var(--sqlviz-bg-base); color: var(--sqlviz-text); }

    .ws-body { flex: 1; overflow-y: auto; padding: 0.5rem 0.375rem; }
    .ws-sidebar.collapsed .ws-body { display: flex; flex-direction: column; align-items: center; gap: 0.125rem; padding: 0.375rem 0; }

    .ws-group {
        font-size: 0.6875rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;
        color: var(--sqlviz-text-muted); padding: 0.75rem 0.5rem 0.375rem;
    }
    .ws-item {
        display: flex; align-items: center; gap: 0.5rem; width: 100%; padding: 0.4375rem 0.5rem;
        background: none; border: none; border-radius: var(--sqlviz-radius); color: var(--sqlviz-text-muted);
        cursor: pointer; text-align: left; font-size: 0.8125rem; transition: background 0.12s, color 0.12s;
    }
    .ws-item:hover { background: var(--sqlviz-bg-base); color: var(--sqlviz-text); }
    .ws-item.active { background: color-mix(in srgb, var(--sqlviz-primary) 15%, transparent); color: var(--sqlviz-primary); }
    .ws-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

    .ws-rail {
        display: flex; align-items: center; justify-content: center; width: 34px; height: 34px;
        border: none; background: none; color: var(--sqlviz-text-muted); border-radius: var(--sqlviz-radius);
        cursor: pointer; transition: background 0.12s, color 0.12s;
    }
    .ws-rail:hover { background: var(--sqlviz-bg-base); color: var(--sqlviz-text); }
    .ws-rail.active { background: color-mix(in srgb, var(--sqlviz-primary) 15%, transparent); color: var(--sqlviz-primary); }

    .ws-empty { padding: 0.75rem 0.5rem; font-size: 0.75rem; color: var(--sqlviz-text-muted); }

    .ws-foot {
        display: flex; align-items: center; justify-content: space-between; height: 44px;
        padding: 0 0.75rem; border-top: 1px solid var(--sqlviz-hairline); flex-shrink: 0;
    }
    .ws-foot.collapsed { justify-content: center; padding: 0; }
    .foot-theme-label { font-size: 0.8125rem; color: var(--sqlviz-text-muted); }

    /* Main */
    .ws-main { flex: 1; display: flex; flex-direction: column; min-width: 0; overflow: hidden; }

    .viewer-bar {
        height: 44px; display: flex; align-items: center; gap: 0.625rem; padding: 0 0.875rem;
        background: var(--sqlviz-bg-surface); border-bottom: 1px solid var(--sqlviz-hairline); flex-shrink: 0;
    }
    .viewer-title {
        font-size: 0.875rem; font-weight: 600; color: var(--sqlviz-text);
        overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex-shrink: 0;
    }
    .viewer-sep { width: 1px; height: 20px; background: var(--sqlviz-border); flex-shrink: 0; }
    .viewer-filters {
        display: flex; align-items: center; gap: 1rem; min-width: 0;
        overflow-x: auto; overflow-y: hidden; scrollbar-width: none;
    }
    .viewer-filters::-webkit-scrollbar { display: none; }

    .ws-content { flex: 1; overflow-y: auto; }
    .viewer-center-inner {
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        min-height: 200px; gap: 0.75rem;
    }
</style>
