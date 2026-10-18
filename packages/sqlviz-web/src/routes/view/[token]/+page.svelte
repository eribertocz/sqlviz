<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import DashboardGrid from '$lib/components/DashboardGrid.svelte';
    import FilterContext from '$lib/components/FilterContext.svelte';
    import ViewerOptions from '$lib/components/ViewerOptions.svelte';
    import { fetchFilterDomains } from '$lib/filters/filterDomains';
    import { createFilterRuntime, patchFilterResults } from '$lib/filters/filterRuntime.svelte';
    import sqlvizIcon from '$lib/assets/sqlviz-icon.svg';
    import { getPaletteById } from '$lib/charts/palettes';
    import { editMode } from '$lib/stores/editMode';
    import { uiStore } from '$lib/stores/uiStore.svelte';
    import { createViewerClient, ViewerAccessError } from '$lib/viewerApi';
    import type { ExecResult } from '$lib/api';

    // Viewer-local chart palette (per-visitor, persisted by dashboard id).
    let paletteId = $state('brand');
    const paletteColors = $derived(getPaletteById(paletteId).colors);
    const paletteKey = (id: string) => `sqlviz-viewer-palette:${id}`;
    function loadPalette(id: string) {
        try { paletteId = localStorage.getItem(paletteKey(id)) || 'brand'; }
        catch { paletteId = 'brand'; }
    }
    function setPalette(id: string) {
        paletteId = id;
        if (sharedDashboardId) {
            try { localStorage.setItem(paletteKey(sharedDashboardId), id); } catch { /* ignore */ }
        }
    }
    import type {
        DashboardLayout,
        FilterControl,
        FilterDomain,
        InferenceResult,
    } from '$lib/types';

    // ── State machine ──────────────────────────────────────────────────────────
    type ViewerState = 'loading' | 'locked' | 'unlocked' | 'error';

    let viewerState: ViewerState = $state('loading');
    let dashboardName: string = $state('');
    let sharedDashboardId: string | null = $state(null);
    let loadError: string | null = $state(null);
    let lockError: string | null = $state(null);

    // Password unlock form
    let unlockPassword: string = $state('');
    let unlocking: boolean = $state(false);

    // Dashboard render state
    let layout: DashboardLayout | null = $state(null);
    let executedResults: ExecResult[] = $state([]);

    // Filter state — local to viewer, separate from admin page's store
    let viewerFilterValues: Record<string, unknown> = $state({});
    // Distinct values / numeric ranges per filter variable — without these,
    // dropdowns/multiselects fall back to a plain text input.
    let viewerDomains: Record<string, FilterDomain> = $state({});

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
    const viewer = createViewerClient(() => window.location.pathname.split('/').at(-1) ?? '');
    const apiPost = viewer.post;
    const recompose = viewer.recompose;
    const filterRuntime = createFilterRuntime({
        getScope: () => sharedDashboardId,
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
    let domainGeneration = 0;
    onDestroy(() => { domainGeneration++; filterRuntime.reset(); });


    function handleAccessFailure(error: unknown): boolean {
        if (!(error instanceof ViewerAccessError)) return false;
        filterRuntime.reset();
        layout = null;
        executedResults = [];
        viewerFilterValues = {};
        viewerDomains = {};
        loadError = 'Dashboard access has expired or was revoked. Open the link again.';
        viewerState = 'error';
        return true;
    }

    // ── Execute helpers ────────────────────────────────────────────────────────
    async function executeAllPanels(
        panels: Array<{ id: string; sql_content: string }>
    ): Promise<void> {
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
        await loadDomains();
    }

    // Load distinct values / ranges so dropdowns render as real dropdowns
    // (same source the admin app uses), authorized for this share on every request.
    async function loadDomains(): Promise<void> {
        const generation = ++domainGeneration;
        const dashboard = sharedDashboardId;
        // Initial execution loads domains before showing the unlocked view.
        const isCurrent = () => generation === domainGeneration && dashboard === sharedDashboardId && viewerState !== 'error';
        const domains = await fetchFilterDomains({
            results: executedResults, isCurrent,
            fetch: (id, column, kind) => apiPost(`/api/v1/panels/${id}/filter-domain`, { column, kind }),
            onAccessFailure: handleAccessFailure,
        });
        if (isCurrent()) viewerDomains = domains;
    }

    type ShareViewData = {
        viewer_session?: string;
        dashboard: { id: string; name: string };
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
            viewer.setSession(shareData.viewer_session ?? '');
            unlockPassword = '';
            dashboardName = shareData.dashboard.name;
            sharedDashboardId = shareData.dashboard.id;
            loadPalette(sharedDashboardId);
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
            sharedDashboardId = viewData.dashboard.id;
            loadPalette(sharedDashboardId);
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
            <div class="auth-logo">
                <img class="auth-logo-icon" src={sqlvizIcon} alt="" width="34" height="34" />
                <span class="auth-wordmark"><span class="brand-sql">SQL</span><span class="brand-viz">viz</span></span>
            </div>
            <p class="lock-hint">{loadError ?? 'An error occurred.'}</p>
        </div>
    </div>

<!-- ── Locked (password prompt) ─────────────────────────────── -->
{:else if viewerState === 'locked'}
    <div class="viewer-center">
        <div class="auth-card">
            <div class="auth-logo">
                <img class="auth-logo-icon" src={sqlvizIcon} alt="" width="34" height="34" />
                <span class="auth-wordmark"><span class="brand-sql">SQL</span><span class="brand-viz">viz</span></span>
            </div>
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

<!-- ── Unlocked (viewer) — single dashboard, no sidebar ──────── -->
{:else if viewerState === 'unlocked'}
    <div class="viewer-shell">
        <!-- Reader context: dashboard, filters and secondary options. -->
        <header class="viewer-bar">
            <span class="viewer-title">{dashboardName || 'Dashboard'}</span>
            <div class="viewer-context-actions">
                {#if hasFilters}
                    {#key sharedDashboardId}<FilterContext dashboardId={sharedDashboardId} controls={allFilterControls}
                        values={viewerFilterValues} domains={viewerDomains} busy={filterRuntime.busy}
                        error={filterRuntime.error} onApply={filterRuntime.apply} />{/key}
                {/if}
                <ViewerOptions {paletteId} onPalette={setPalette} />
            </div>
        </header>

        <div class="viewer-content" aria-busy={filterRuntime.busy}>
            {#if layout}
                <DashboardGrid {layout} palette={paletteColors} />
            {:else}
                <div class="viewer-center-inner">
                    <span class="viewer-spinner">⟳</span>
                    <span class="viewer-msg">Building dashboard…</span>
                </div>
            {/if}
        </div>
    </div>
{/if}

<style>
    .viewer-context-actions { margin-left: auto; display: flex; align-items: center; gap: 6px; flex-shrink: 0; }

    /* ── Loading / error centering ────────────────────────────── */
    .viewer-center {
        min-height: 100dvh;
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
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.625rem;
    }
    .auth-logo-icon { display: block; flex-shrink: 0; }
    .auth-wordmark {
        font-family: 'Geist Sans', var(--sqlviz-font-sans);
        font-size: 1.375rem;
        font-weight: 600;
        letter-spacing: -0.025em;
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

    /* ── Viewer shell (unlocked) — header + content, no sidebar ── */
    .viewer-shell {
        height: 100dvh;
        display: flex;
        flex-direction: column;
        background: var(--sqlviz-bg);
        overflow: hidden;
    }

    .brand-sql { color: var(--sqlviz-text-primary); font-weight: 600; }
    .brand-viz { color: var(--sqlviz-primary); font-weight: 600; }

    /* Header: logo + name + inline filters + theme toggle */
    .viewer-bar {
        min-height: 52px;
        display: flex;
        align-items: center;
        gap: 0.625rem;
        padding: 0 0.875rem;
        background: var(--sqlviz-bg-surface);
        border-bottom: 1px solid var(--sqlviz-hairline);
        flex-shrink: 0;
    }
    .viewer-title {
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--sqlviz-text);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        min-width: 0;
        flex: 1;
    }


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
