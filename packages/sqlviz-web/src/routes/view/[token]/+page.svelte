<script lang="ts">
    import { onMount } from 'svelte';
    import DashboardGrid from '$lib/components/DashboardGrid.svelte';
    import FilterControlComponent from '$lib/components/FilterControl.svelte';
    import ThemeToggle from '$lib/components/ThemeToggle.svelte';
    import * as Popover from '$lib/components/ui/popover/index.js';
    import sqlvizIcon from '$lib/assets/sqlviz-icon.svg';
    import { editMode } from '$lib/stores/editMode';
    import { uiStore } from '$lib/stores/uiStore.svelte';
    import PanelLeftCloseIcon from '@lucide/svelte/icons/panel-left-close';
    import SlidersHorizontalIcon from '@lucide/svelte/icons/sliders-horizontal';

    // Viewer-local UI state (independent of the admin app).
    let sidebarCollapsed = $state(false);
    let filtersOpen = $state(false);
    import type {
        DashboardLayout,
        FilterControl,
        InferenceResult,
    } from '$lib/types';

    // ── State machine ──────────────────────────────────────────────────────────
    type ViewerState = 'loading' | 'locked' | 'unlocked' | 'error';

    let viewerState: ViewerState = $state('loading');
    let dashboardName: string = $state('');
    let loadError: string | null = $state(null);
    let lockError: string | null = $state(null);

    // Password unlock form
    let unlockPassword: string = $state('');
    let unlocking: boolean = $state(false);

    // Dashboard render state
    type ExecResult = {
        panel_id: string;
        inference_result: InferenceResult;
        data: Record<string, unknown>[];
    };
    let layout: DashboardLayout | null = $state(null);
    let panelIds: string[] = $state([]);
    let executedResults: ExecResult[] = $state([]);

    // Filter state — local to viewer, separate from admin page's store
    let viewerFilterValues: Record<string, unknown> = $state({});
    let filterDebounceTimer = 0;

    const allFilterControls = $derived.by(() => {
        const seen = new Set<string>();
        const controls: FilterControl[] = [];
        for (const r of executedResults) {
            for (const fc of r.inference_result.filter_controls) {
                if (!seen.has(fc.variable)) {
                    seen.add(fc.variable);
                    controls.push(fc);
                }
            }
        }
        return controls;
    });

    const hasFilters = $derived(allFilterControls.length > 0);

    const activeFilterCount = $derived(
        allFilterControls.filter((c) => {
            const v = viewerFilterValues[c.variable.split(',')[0].trim()];
            return v !== undefined && v !== '' && v !== null
                && !(Array.isArray(v) && v.length === 0);
        }).length
    );

    // ── API helpers ────────────────────────────────────────────────────────────
    async function apiPost<T>(path: string, body?: unknown): Promise<T> {
        const r = await fetch(path, {
            method: 'POST',
            headers: body !== undefined ? { 'Content-Type': 'application/json' } : {},
            body: body !== undefined ? JSON.stringify(body) : undefined,
        });
        if (!r.ok) {
            const err = await r.json().catch(() => null) as { detail?: string } | null;
            throw new Error(err?.detail ?? `${r.status} ${r.statusText}`);
        }
        return r.json() as Promise<T>;
    }

    async function recompose(results: ExecResult[]): Promise<DashboardLayout> {
        const body = results.map(r => ({
            panel_id: r.panel_id,
            inference_result: r.inference_result,
        }));
        const response = await apiPost<DashboardLayout>('/api/v1/compose', body);
        const dataMap = new Map(results.map(r => [r.panel_id, r.data]));
        return {
            rows: response.rows.map(row => ({
                panels: row.panels.map(p => ({
                    ...p,
                    data: dataMap.get(p.panel_id) ?? [],
                })),
            })),
        };
    }

    // ── Execute helpers ────────────────────────────────────────────────────────
    async function executeAllPanels(
        panels: Array<{ id: string; sql_content: string }>
    ): Promise<void> {
        panelIds = panels.map(p => p.id);
        const results: ExecResult[] = [];
        for (const panel of panels) {
            const exec = await apiPost<{
                inference_result: InferenceResult;
                data: Record<string, unknown>[];
            }>(`/api/v1/panels/${panel.id}/execute`);
            results.push({ panel_id: panel.id, ...exec });
        }
        executedResults = results;
        layout = await recompose(results);
    }

    async function executeFilteredPanels(
        changedVar: string,
        currentFV: Record<string, unknown>,
    ): Promise<void> {
        const updatedResults = [...executedResults];
        let anyChanged = false;

        for (let i = 0; i < executedResults.length; i++) {
            const controls = executedResults[i].inference_result.filter_controls;
            const panelVars = controls.flatMap((fc: FilterControl) =>
                fc.variable.split(',').map((v: string) => v.trim())
            );
            if (!panelVars.includes(changedVar)) continue;

            const allProvided = panelVars.every((v: string) => {
                const val = currentFV[v];
                return val !== undefined && val !== '' && val !== null;
            });
            if (!allProvided) continue;

            const variables = Object.fromEntries(
                panelVars.map((v: string) => [v, currentFV[v]])
            );

            try {
                const exec = await apiPost<{
                    inference_result: InferenceResult;
                    data: Record<string, unknown>[];
                }>(`/api/v1/panels/${panelIds[i]}/execute`, { variables });
                updatedResults[i] = { panel_id: panelIds[i], ...exec };
                anyChanged = true;
            } catch {
                // Keep existing result on error
            }
        }

        if (!anyChanged) return;
        executedResults = updatedResults;
        try {
            layout = await recompose(updatedResults);
        } catch {
            // Layout stays as-is
        }
    }

    function handleFilterChange(varName: string, value: unknown) {
        viewerFilterValues = { ...viewerFilterValues, [varName]: value };
        clearTimeout(filterDebounceTimer);
        filterDebounceTimer = window.setTimeout(() => {
            executeFilteredPanels(
                varName,
                { ...viewerFilterValues, [varName]: value }
            );
        }, 350);
    }

    // ── Unlock (password-protected share) ─────────────────────────────────────
    type ShareViewData = {
        dashboard: { name: string };
        panels: Array<{ id: string; sql_content: string }>;
    };

    async function handleUnlock(e: SubmitEvent) {
        e.preventDefault();
        if (unlocking) return;
        unlocking = true;
        lockError = null;

        const token = window.location.pathname.split('/').at(-1) ?? '';
        try {
            const resp = await fetch(`/view/${token}/unlock`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password: unlockPassword }),
            });
            if (!resp.ok) {
                lockError = 'Invalid password';
                unlockPassword = '';
                return;
            }
            const shareData = await resp.json() as ShareViewData;
            dashboardName = shareData.dashboard.name;
            await executeAllPanels(shareData.panels);
            viewerState = 'unlocked';
        } catch {
            lockError = 'Could not reach the server.';
        } finally {
            unlocking = false;
        }
    }

    // ── Mount ──────────────────────────────────────────────────────────────────
    onMount(async () => {
        editMode.set(false);
        uiStore.initTheme();
        const token = window.location.pathname.split('/').at(-1) ?? '';

        try {
            // Explicit JSON + no-store so the browser never reuses the cached
            // SPA-shell HTML (same URL as this data fetch) — that would make
            // resp.json() throw "Unexpected token '<'".
            const resp = await fetch(`/view/${token}`, {
                headers: { Accept: 'application/json' },
                cache: 'no-store',
            });
            if (!resp.ok) {
                loadError = 'Dashboard not found or link has expired.';
                viewerState = 'error';
                return;
            }
            const body = await resp.json() as
                | { requires_password: boolean; mode: string }
                | ShareViewData;

            if ('requires_password' in body && body.requires_password) {
                viewerState = 'locked';
                return;
            }

            const viewData = body as ShareViewData;
            dashboardName = viewData.dashboard.name;
            await executeAllPanels(viewData.panels);
            viewerState = 'unlocked';
        } catch (e) {
            loadError = e instanceof Error
                ? `Failed to load the dashboard: ${e.message}`
                : 'Failed to load the dashboard.';
            viewerState = 'error';
        }
    });
</script>

<svelte:head>
    <title>{dashboardName || 'Dashboard'} — SQLviz</title>
</svelte:head>

<!-- ── Loading ──────────────────────────────────────────────── -->
{#if viewerState === 'loading'}
    <div class="viewer-center">
        <span class="viewer-spinner">⟳</span>
        <span class="viewer-msg">Loading…</span>
    </div>

<!-- ── Error ────────────────────────────────────────────────── -->
{:else if viewerState === 'error'}
    <div class="viewer-center">
        <div class="auth-card">
            <div class="auth-logo">SQLviz</div>
            <p class="lock-hint">{loadError ?? 'An error occurred.'}</p>
        </div>
    </div>

<!-- ── Locked (password prompt) ─────────────────────────────── -->
{:else if viewerState === 'locked'}
    <div class="viewer-center">
        <div class="auth-card">
            <div class="auth-logo">SQLviz</div>
            <p class="lock-hint">
                This dashboard is password protected.<br />
                Enter the password to continue.
            </p>
            <form class="auth-form" onsubmit={handleUnlock}>
                <label class="auth-label" for="unlock-pw">Password</label>
                <input
                    id="unlock-pw"
                    type="password"
                    class="auth-input"
                    bind:value={unlockPassword}
                    placeholder="Dashboard password"
                    autocomplete="current-password"
                    disabled={unlocking}
                    autofocus
                />
                {#if lockError}
                    <div class="auth-error" role="alert">{lockError}</div>
                {/if}
                <button
                    type="submit"
                    class="auth-btn"
                    disabled={unlocking || unlockPassword.length === 0}
                >
                    {unlocking ? 'Unlocking…' : 'Unlock'}
                </button>
            </form>
        </div>
    </div>

<!-- ── Unlocked (viewer) ─────────────────────────────────────── -->
{:else if viewerState === 'unlocked'}
    <div class="viewer-shell">
        <!-- Sidebar — navigation only, collapsible, no management/edit/share -->
        <nav class="viewer-sidebar" class:collapsed={sidebarCollapsed} aria-label="Dashboard navigation">
            <div class="viewer-sidebar-header" class:collapsed={sidebarCollapsed}>
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

            {#if !sidebarCollapsed}
                <div class="viewer-sidebar-body">
                    <button class="viewer-nav-item active" aria-current="page">
                        <span class="nav-dot" aria-hidden="true"></span>
                        <span class="nav-name">{dashboardName || 'Dashboard'}</span>
                    </button>
                </div>
            {:else}
                <div class="viewer-sidebar-body"></div>
            {/if}

            <!-- Footer — only the theme toggle for viewers -->
            <div class="viewer-sidebar-footer" class:collapsed={sidebarCollapsed}>
                {#if !sidebarCollapsed}
                    <span class="foot-theme-label">Theme</span>
                    <ThemeToggle />
                {:else}
                    <ThemeToggle compact />
                {/if}
            </div>
        </nav>

        <!-- Main column — the dashboard owns the whole area; filters float -->
        <div class="viewer-main">
            <div class="viewer-content" class:has-filters={hasFilters}>
                {#if layout}
                    <DashboardGrid {layout} />
                {:else}
                    <div class="viewer-center-inner">
                        <span class="viewer-spinner">⟳</span>
                        <span class="viewer-msg">Building dashboard…</span>
                    </div>
                {/if}
            </div>

            <!-- Collapsible filters (Vercel/Linear-style), floating over the top -->
            {#if hasFilters}
                <div class="filters-launch">
                    <Popover.Root bind:open={filtersOpen}>
                        <Popover.Trigger class="filters-btn {activeFilterCount > 0 ? 'active' : ''}">
                            <SlidersHorizontalIcon class="size-4" />
                            Filters
                            {#if activeFilterCount > 0}<span class="filters-badge">{activeFilterCount}</span>{/if}
                        </Popover.Trigger>
                        <Popover.Content class="w-auto max-w-[92vw] p-3" align="start">
                            <div class="filter-panel" role="group" aria-label="Dashboard filters">
                                {#each allFilterControls as control (control.variable)}
                                    <FilterControlComponent
                                        {control}
                                        pill
                                        filterVals={viewerFilterValues}
                                        onChange={handleFilterChange}
                                    />
                                {/each}
                            </div>
                        </Popover.Content>
                    </Popover.Root>
                </div>
            {/if}
        </div>
    </div>
{/if}

<style>
    /* ── Loading / error centering ────────────────────────────── */
    .viewer-center {
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background: var(--sqlviz-bg);
        gap: 0.75rem;
        padding: 1.5rem;
    }

    .viewer-spinner {
        font-size: 2rem;
        animation: spin 1.2s linear infinite;
        display: inline-block;
        color: var(--sqlviz-text-muted);
    }

    @keyframes spin { to { transform: rotate(360deg); } }

    .viewer-msg {
        color: var(--sqlviz-text-muted);
        font-size: 0.9375rem;
    }

    /* ── Auth card (lock screen + error screen) ─────────────── */
    .auth-card {
        width: 100%;
        max-width: 360px;
        background: var(--sqlviz-bg-surface);
        border: 1px solid var(--sqlviz-border);
        border-radius: var(--sqlviz-radius-lg);
        padding: 2rem 2rem 1.75rem;
        display: flex;
        flex-direction: column;
        gap: 1.25rem;
    }

    .auth-logo {
        font-size: 1.375rem;
        font-weight: 800;
        color: var(--sqlviz-primary);
        letter-spacing: -0.03em;
        text-align: center;
    }

    .lock-hint {
        margin: 0;
        font-size: 0.875rem;
        color: var(--sqlviz-text-muted);
        text-align: center;
        line-height: 1.5;
    }

    .auth-form {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }

    .auth-label {
        font-size: 0.8125rem;
        font-weight: 600;
        color: var(--sqlviz-text-muted);
    }

    .auth-input {
        width: 100%;
        height: 40px;
        padding: 0 0.875rem;
        background: var(--sqlviz-bg);
        border: 1px solid var(--sqlviz-border);
        border-radius: var(--sqlviz-radius);
        color: var(--sqlviz-text);
        font-size: 0.9375rem;
        font-family: var(--sqlviz-font-sans);
        outline: none;
        box-sizing: border-box;
        transition: border-color 0.15s;
    }

    .auth-input:focus { border-color: var(--sqlviz-primary); }
    .auth-input:disabled { opacity: 0.5; }

    .auth-error {
        font-size: 0.8125rem;
        color: var(--sqlviz-negative);
        padding: 0.375rem 0.625rem;
        background: color-mix(in srgb, var(--sqlviz-negative) 10%, transparent);
        border-radius: var(--sqlviz-radius);
    }

    .auth-btn {
        height: 40px;
        padding: 0 1rem;
        background: var(--sqlviz-primary);
        color: var(--sqlviz-on-primary);
        border: none;
        border-radius: var(--sqlviz-radius);
        font-size: 0.9375rem;
        font-weight: 600;
        cursor: pointer;
        transition: opacity 0.15s;
        margin-top: 0.25rem;
    }

    .auth-btn:hover:not(:disabled) { opacity: 0.85; }
    .auth-btn:disabled { opacity: 0.45; cursor: not-allowed; }

    /* ── Viewer shell (unlocked) — sidebar + main ────────────── */
    .viewer-shell {
        height: 100vh;
        display: flex;
        flex-direction: row;
        background: var(--sqlviz-bg);
        overflow: hidden;
    }

    /* Sidebar — collapsible rail */
    .viewer-sidebar {
        width: 240px;
        flex-shrink: 0;
        display: flex;
        flex-direction: column;
        background: var(--sqlviz-bg-surface);
        border-right: 1px solid var(--sqlviz-hairline);
        overflow: hidden;
        transition: width 0.2s ease;
    }
    .viewer-sidebar.collapsed { width: 44px; }

    .viewer-sidebar-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.5rem;
        height: 44px;
        padding: 0 0.5rem 0 0.875rem;
        flex-shrink: 0;
        border-bottom: 1px solid var(--sqlviz-hairline);
    }
    .viewer-sidebar-header.collapsed { justify-content: center; padding: 0; }

    .brand { display: flex; align-items: center; gap: 0.5rem; min-width: 0; }
    .brand-icon { display: block; flex-shrink: 0; }
    .brand-name { font-size: 0.9375rem; letter-spacing: -0.01em; white-space: nowrap; overflow: hidden; }
    .brand-sql { color: var(--sqlviz-text-primary); font-weight: 600; }
    .brand-viz { color: #06b6d4; font-weight: 600; }

    .hbtn, .brand-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        border: none;
        background: none;
        color: var(--sqlviz-text-muted);
        border-radius: var(--sqlviz-radius);
        cursor: pointer;
        transition: background 0.12s, color 0.12s;
    }
    .hbtn { width: 24px; height: 24px; }
    .brand-btn { width: 34px; height: 34px; }
    .hbtn:hover, .brand-btn:hover { background: var(--sqlviz-bg-base); color: var(--sqlviz-text); }

    .viewer-sidebar-body { flex: 1; overflow-y: auto; padding: 0.5rem 0.375rem; }

    .viewer-nav-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        width: 100%;
        padding: 0.4375rem 0.5rem;
        background: none;
        border: none;
        border-radius: var(--sqlviz-radius);
        color: var(--sqlviz-text-muted);
        cursor: default;
        text-align: left;
        font-size: 0.8125rem;
    }
    .viewer-nav-item.active {
        background: color-mix(in srgb, var(--sqlviz-primary) 15%, transparent);
        color: var(--sqlviz-primary);
    }
    .nav-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: currentColor;
        flex-shrink: 0;
    }
    .nav-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

    .viewer-sidebar-footer {
        display: flex;
        align-items: center;
        justify-content: space-between;
        height: 44px;
        padding: 0 0.75rem;
        border-top: 1px solid var(--sqlviz-hairline);
        flex-shrink: 0;
    }
    .viewer-sidebar-footer.collapsed { justify-content: center; padding: 0; }
    .foot-theme-label { font-size: 0.8125rem; color: var(--sqlviz-text-muted); }

    /* Main column — the dashboard owns the whole area */
    .viewer-main {
        position: relative;
        flex: 1;
        display: flex;
        flex-direction: column;
        min-width: 0;
        overflow: hidden;
    }

    .viewer-content {
        flex: 1;
        overflow-y: auto;
    }
    /* Reserve room so the floating Filters button never overlaps panels */
    .viewer-content.has-filters { padding-top: 52px; }

    /* ── Collapsible filters (Vercel/Linear-style), floating over the top ── */
    .filters-launch {
        position: absolute;
        top: 12px;
        left: 14px;
        z-index: 20;
    }
    :global(.filters-btn) {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        height: 32px;
        padding: 0 0.75rem;
        font-size: 0.8125rem;
        font-weight: 600;
        color: var(--sqlviz-text-muted);
        background: var(--sqlviz-bg-surface);
        border: 1px solid var(--sqlviz-border);
        border-radius: 100px;
        cursor: pointer;
        box-shadow: var(--sqlviz-shadow-card);
        transition: border-color 0.12s, color 0.12s;
    }
    :global(.filters-btn:hover) { border-color: var(--sqlviz-primary); color: var(--sqlviz-text); }
    :global(.filters-btn.active) { color: var(--sqlviz-primary); border-color: var(--sqlviz-primary); }
    .filters-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 16px;
        height: 16px;
        padding: 0 4px;
        font-size: 10px;
        border-radius: 100px;
        background: var(--sqlviz-primary);
        color: var(--sqlviz-on-primary);
    }
    .filter-panel {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.625rem;
        max-width: 520px;
    }

    .viewer-center-inner {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 200px;
        gap: 0.75rem;
    }
</style>
