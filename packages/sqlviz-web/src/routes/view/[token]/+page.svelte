<script lang="ts">
    import { onMount } from 'svelte';
    import DashboardGrid from '$lib/components/DashboardGrid.svelte';
    import FilterControlComponent from '$lib/components/FilterControl.svelte';
    import BrandMark from '$lib/components/BrandMark.svelte';
    import { editMode } from '$lib/stores/editMode';
    import { uiStore } from '$lib/stores/uiStore.svelte';
    import SunIcon from '@lucide/svelte/icons/sun';
    import MoonIcon from '@lucide/svelte/icons/moon';
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
            const resp = await fetch(`/view/${token}`);
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
        } catch {
            loadError = 'Failed to load the dashboard.';
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
        <!-- Sidebar — navigation only, no management (Section 5) -->
        <nav class="viewer-sidebar" aria-label="Dashboard navigation">
            <div class="viewer-sidebar-header">
                <BrandMark size={18} />
                <span class="viewer-brand-name">SQLviz</span>
            </div>

            <div class="viewer-sidebar-body">
                <button class="viewer-nav-item active" aria-current="page">
                    <span class="nav-dot" aria-hidden="true"></span>
                    <span class="nav-name">{dashboardName || 'Dashboard'}</span>
                </button>
            </div>

            <!-- Footer — only the theme toggle for viewers -->
            <div class="viewer-sidebar-footer">
                <button
                    class="foot-btn wide"
                    onclick={uiStore.toggleTheme}
                    aria-label={uiStore.theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
                >
                    {#if uiStore.theme === 'dark'}
                        <SunIcon size={16} /> <span>Light mode</span>
                    {:else}
                        <MoonIcon size={16} /> <span>Dark mode</span>
                    {/if}
                </button>
            </div>
        </nav>

        <!-- Main column -->
        <div class="viewer-main">
            <header class="viewer-bar">
                <span class="viewer-title">{dashboardName || 'Dashboard'}</span>
                {#if hasFilters}
                    <span class="viewer-sep" aria-hidden="true"></span>
                    <div class="viewer-filters" role="group" aria-label="Dashboard filters">
                        {#each allFilterControls as control (control.variable)}
                            <FilterControlComponent
                                {control}
                                pill
                                filterVals={viewerFilterValues}
                                onChange={handleFilterChange}
                            />
                        {/each}
                    </div>
                {/if}
            </header>

            <div class="viewer-content">
                {#if layout}
                    <DashboardGrid {layout} />
                {:else}
                    <div class="viewer-center-inner">
                        <span class="viewer-spinner">⟳</span>
                        <span class="viewer-msg">Building dashboard…</span>
                    </div>
                {/if}
            </div>
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
        color: #fff;
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

    /* Sidebar */
    .viewer-sidebar {
        width: 240px;
        flex-shrink: 0;
        display: flex;
        flex-direction: column;
        background: var(--sqlviz-bg-surface);
        border-right: 1px solid var(--sqlviz-hairline);
        overflow: hidden;
    }

    .viewer-sidebar-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        height: 44px;
        padding: 0 0.875rem;
        flex-shrink: 0;
        border-bottom: 1px solid var(--sqlviz-hairline);
    }

    .viewer-brand-name {
        font-size: 0.9375rem;
        font-weight: 700;
        color: var(--sqlviz-text);
        letter-spacing: -0.01em;
    }

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
        padding: 0.375rem;
        border-top: 1px solid var(--sqlviz-hairline);
        flex-shrink: 0;
    }
    .foot-btn {
        display: flex;
        align-items: center;
        gap: 0.625rem;
        width: 100%;
        height: 32px;
        padding: 0 0.5rem;
        border: none;
        background: none;
        color: var(--sqlviz-text-muted);
        border-radius: var(--sqlviz-radius);
        cursor: pointer;
        font-size: 0.8125rem;
        transition: background 0.12s, color 0.12s;
    }
    .foot-btn:hover { background: var(--sqlviz-bg-base); color: var(--sqlviz-text); }

    /* Main column */
    .viewer-main {
        flex: 1;
        display: flex;
        flex-direction: column;
        min-width: 0;
        overflow: hidden;
    }

    .viewer-bar {
        height: 44px;
        display: flex;
        align-items: center;
        gap: 0.625rem;
        padding: 0 0.875rem;
        background: var(--sqlviz-bg-surface);
        border-bottom: 1px solid var(--sqlviz-hairline);
        flex-shrink: 0;
    }

    .viewer-sep {
        width: 1px;
        height: 20px;
        background: var(--sqlviz-border);
        flex-shrink: 0;
    }

    .viewer-title {
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--sqlviz-text);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        flex-shrink: 0;
    }

    .viewer-filters {
        display: flex;
        align-items: center;
        gap: 1rem;
        min-width: 0;
        overflow-x: auto;
        overflow-y: hidden;
        scrollbar-width: none;
    }
    .viewer-filters::-webkit-scrollbar { display: none; }

    .viewer-content {
        flex: 1;
        overflow-y: auto;
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
