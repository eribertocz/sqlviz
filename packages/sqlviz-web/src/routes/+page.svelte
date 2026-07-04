<script lang="ts">
    import { goto } from '$app/navigation';
    import { onMount } from 'svelte';
    import DashboardGrid from '$lib/components/DashboardGrid.svelte';
    import ExplainPanel from '$lib/components/ExplainPanel.svelte';
    import FilterBar from '$lib/components/FilterBar.svelte';
    import SQLEditor from '$lib/components/SQLEditor.svelte';
    import { editMode } from '$lib/stores/editMode';
    import { editorRef } from '$lib/stores/editorRef';
    import { explainTarget } from '$lib/stores/explainStore';
    import { filterValues } from '$lib/stores/filterValues';
    import type { DashboardLayout, FilterControl, InferenceResult } from '$lib/types';

    // ── Core state ─────────────────────────────────────────────────────────────
    let sql        = $state('');
    let layout     = $state<DashboardLayout | null>(null);
    let executing  = $state(false);
    let statusMsg  = $state<string | null>(null);
    let errorMsg   = $state<string | null>(null);

    // ── Theme ──────────────────────────────────────────────────────────────────
    let theme = $state<'dark' | 'light'>('dark');

    function toggleTheme() {
        theme = theme === 'dark' ? 'light' : 'dark';
        if (theme === 'light') {
            document.documentElement.dataset.theme = 'light';
        } else {
            delete document.documentElement.dataset.theme;
        }
        localStorage.setItem('sqlviz-theme', theme);
    }

    // Parallel arrays: index = SQL statement position
    let dashboardId      = $state<string | null>(null);
    let panelIds         = $state<string[]>([]);
    let panelSQLs        = $state<string[]>([]);
    let executedResults  = $state<ExecResult[]>([]);

    // Toast for placeholder actions (e.g. Explain)
    let toast = $state<string | null>(null);
    let toastTimer = 0;

    const hasLayout = $derived(layout !== null && layout.rows.length > 0);

    // ── Filter state ──────────────────────────────────────────────────────────
    // Unique filter controls across all panels (by variable name).
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

    let filterDebounceTimer = 0;

    type ExecResult = {
        panel_id: string;
        inference_result: InferenceResult;
        data: Record<string, unknown>[];
    };

    // ── API helpers ────────────────────────────────────────────────────────────
    async function apiPost<T>(path: string, body?: unknown): Promise<T> {
        const r = await fetch(path, {
            method: 'POST',
            headers: body !== undefined ? { 'Content-Type': 'application/json' } : {},
            body:    body !== undefined ? JSON.stringify(body) : undefined,
        });
        if (!r.ok) {
            const err = await r.json().catch(() => null) as { detail?: string } | null;
            throw new Error(err?.detail ?? `${r.status} ${r.statusText}`);
        }
        return r.json() as Promise<T>;
    }

    async function apiPatch<T>(path: string, body: unknown): Promise<T> {
        const r = await fetch(path, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify(body),
        });
        if (!r.ok) {
            const err = await r.json().catch(() => null) as { detail?: string } | null;
            throw new Error(err?.detail ?? `${r.status} ${r.statusText}`);
        }
        return r.json() as Promise<T>;
    }

    // ── Compose helper ─────────────────────────────────────────────────────────
    async function recompose(results: ExecResult[]): Promise<DashboardLayout> {
        const composeBody = results.map(r => ({
            panel_id: r.panel_id,
            inference_result: r.inference_result,
        }));
        const layoutResponse = await apiPost<DashboardLayout>('/api/v1/compose', composeBody);
        const dataMap = new Map(results.map(r => [r.panel_id, r.data]));
        return {
            rows: layoutResponse.rows.map(row => ({
                panels: row.panels.map(p => ({
                    ...p,
                    data: dataMap.get(p.panel_id) ?? [],
                })),
            })),
        };
    }

    // ── Load existing state on mount ───────────────────────────────────────────
    onMount(async () => {
        // Restore saved theme before any render
        const savedTheme = localStorage.getItem('sqlviz-theme');
        if (savedTheme === 'light') {
            theme = 'light';
            document.documentElement.dataset.theme = 'light';
        }

        // Auth guard — redirect to /login if no valid session
        const meResp = await fetch('/api/v1/auth/me');
        if (meResp.status === 401) {
            await goto('/login');
            return;
        }
        // Demo mode: activate Edit mode automatically so Monaco is visible
        const meData = await meResp.json() as { status: string; demo: boolean };
        if (meData.demo) {
            editMode.set(true);
        }

        try {
            const dashboards = await fetch('/api/v1/dashboards')
                .then(r => r.json()) as Array<{ id: string }>;
            if (dashboards.length === 0) {
                if (meData.demo) {
                    // Demo mode with no panels: auto-seed the example dashboard.
                    const { sql: demoSql } = await fetch('/api/v1/demo/sql')
                        .then(r => r.json()) as { sql: string };
                    sql = demoSql;
                    run();
                }
                return;
            }

            dashboardId = dashboards[0].id;
            const panels = await fetch(`/api/v1/panels?dashboard_id=${dashboardId}`)
                .then(r => r.json()) as Array<{ id: string; sql_content: string; sort_order: number }>;
            if (panels.length === 0) return;

            panels.sort((a, b) => a.sort_order - b.sort_order);
            panelIds  = panels.map(p => p.id);
            panelSQLs = panels.map(p => p.sql_content);
            sql = panelSQLs.join(';\n\n');
        } catch {
            // Fresh install — no existing state
        }
    });

    // ── Run ───────────────────────────────────────────────────────────────────
    async function run() {
        if (executing) return;

        const statements = sql
            .split(';')
            .map(s => s.trim())
            .filter(s => s.length > 0);

        if (statements.length === 0) {
            errorMsg = 'No SQL statements found. Write at least one query separated by ";".';
            return;
        }

        executing = true;
        errorMsg  = null;

        try {
            if (!dashboardId) {
                const dash = await apiPost<{ id: string }>('/api/v1/dashboards', {
                    name: 'My Dashboard',
                    sort_order: 0,
                });
                dashboardId = dash.id;
            }

            const results: ExecResult[] = [];
            const newPanelIds: string[] = [];

            for (let i = 0; i < statements.length; i++) {
                const stmt = statements[i];
                statusMsg = `Statement ${i + 1} / ${statements.length}…`;

                let panelId: string;
                if (panelIds[i]) {
                    await apiPatch(`/api/v1/panels/${panelIds[i]}`, {
                        sql_content: stmt,
                        sort_order: i,
                    });
                    panelId = panelIds[i];
                } else {
                    const panel = await apiPost<{ id: string }>('/api/v1/panels', {
                        dashboard_id: dashboardId,
                        name: `Panel ${i + 1}`,
                        sql_content: stmt,
                        sort_order: i,
                    });
                    panelId = panel.id;
                }
                newPanelIds.push(panelId);

                const exec = await apiPost<{ inference_result: InferenceResult; data: Record<string, unknown>[] }>(
                    `/api/v1/panels/${panelId}/execute`
                );
                results.push({ panel_id: panelId, ...exec });
            }

            panelIds        = newPanelIds;
            panelSQLs       = statements;
            executedResults = results;

            statusMsg = 'Composing layout…';
            layout    = await recompose(results);
            statusMsg = null;
        } catch (e: unknown) {
            errorMsg  = e instanceof Error ? e.message : String(e);
            statusMsg = null;
        } finally {
            executing = false;
        }
    }

    // ── Panel actions ──────────────────────────────────────────────────────────
    async function handleDelete(panelId: string) {
        const idx = panelIds.indexOf(panelId);
        if (idx < 0) return;

        try {
            await fetch(`/api/v1/panels/${panelId}`, { method: 'DELETE' });
        } catch {
            showToast('Delete failed — check the API server.');
            return;
        }

        const newResults  = executedResults.filter((_, i) => i !== idx);
        const newPanelIds = panelIds.filter((_, i) => i !== idx);
        const newSQLs     = panelSQLs.filter((_, i) => i !== idx);

        executedResults = newResults;
        panelIds        = newPanelIds;
        panelSQLs       = newSQLs;
        sql             = newSQLs.join(';\n\n');

        if (newResults.length === 0) {
            layout = null;
            return;
        }

        try {
            layout = await recompose(newResults);
        } catch (e: unknown) {
            showToast(e instanceof Error ? e.message : 'Compose failed after delete.');
        }
    }

    function handleEditSQL(panelId: string) {
        const idx = panelIds.indexOf(panelId);
        if (idx < 0) return;
        $editorRef.focusStatement?.(idx);
    }

    function handleExplain(panelId: string) {
        const result = executedResults.find(r => r.panel_id === panelId);
        if (!result) {
            showToast('Run the dashboard first to see explainability data.');
            return;
        }
        explainTarget.set(result);
    }

    // ── Filter execution ───────────────────────────────────────────────────────
    /**
     * Re-execute only the panels that use `changedVar`, and only when all of
     * the panel's $variables have values in `currentFV`.
     * Other panels are left unchanged.
     */
    async function executeFilteredPanels(
        changedVar: string,
        currentFV: Record<string, unknown>,
    ) {
        const updatedResults = [...executedResults];
        let anyChanged = false;

        for (let i = 0; i < executedResults.length; i++) {
            const controls = executedResults[i].inference_result.filter_controls;
            const panelVars = controls.flatMap(fc =>
                fc.variable.split(',').map(v => v.trim())
            );

            // Only process panels that actually use changedVar
            if (!panelVars.includes(changedVar)) continue;

            // Skip if any required variable is missing or empty
            const allProvided = panelVars.every(v => {
                const val = currentFV[v];
                return val !== undefined && val !== '' && val !== null;
            });
            if (!allProvided) continue;

            const variables = Object.fromEntries(panelVars.map(v => [v, currentFV[v]]));
            const panelId = panelIds[i];

            try {
                const exec = await apiPost<{
                    inference_result: InferenceResult;
                    data: Record<string, unknown>[];
                }>(`/api/v1/panels/${panelId}/execute`, { variables });
                updatedResults[i] = { panel_id: panelId, ...exec };
                anyChanged = true;
            } catch {
                // Keep existing result; don't propagate to avoid disrupting UX
            }
        }

        if (!anyChanged) return;
        executedResults = updatedResults;
        try {
            layout = await recompose(updatedResults);
        } catch {
            // Layout stays as-is if recompose fails
        }
    }

    function handleFilterChange(varName: string, value: unknown) {
        filterValues.update(fv => ({ ...fv, [varName]: value }));

        // Debounce to avoid re-executing on every keystroke (search / numeric)
        clearTimeout(filterDebounceTimer);
        filterDebounceTimer = window.setTimeout(() => {
            const currentFV = { ...$filterValues, [varName]: value };
            executeFilteredPanels(varName, currentFV);
        }, 350);
    }

    // ── Toast ──────────────────────────────────────────────────────────────────
    function showToast(msg: string, durationMs = 3500) {
        toast = msg;
        clearTimeout(toastTimer);
        toastTimer = window.setTimeout(() => { toast = null; }, durationMs);
    }
</script>

<div class="app-shell">
    <!-- App bar -->
    <header class="app-bar">
        <span class="app-logo">SQLviz</span>

        <div class="bar-right">
            <div class="mode-toggle" role="group" aria-label="Dashboard mode">
                <button
                    class="mode-btn"
                    class:active={!$editMode}
                    onclick={() => editMode.set(false)}
                >Preview</button>
                <button
                    class="mode-btn"
                    class:active={$editMode}
                    onclick={() => editMode.set(true)}
                >Edit</button>
            </div>

            <button
                class="theme-btn"
                onclick={toggleTheme}
                aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
                title={theme === 'dark' ? 'Light mode' : 'Dark mode'}
            >{theme === 'dark' ? '☀' : '☾'}</button>
        </div>
    </header>

    <!-- Filter bar — visible in both Preview and Edit modes when panels have $variables -->
    {#if hasFilters}
        <FilterBar
            controls={allFilterControls}
            filterVals={$filterValues}
            onChange={handleFilterChange}
        />
    {/if}

    <!-- Dashboard area -->
    <div class="dashboard-area" class:empty={!hasLayout && !executing}>
        {#if executing && !hasLayout}
            <div class="state-msg">
                <span class="spinner">⟳</span>
                <span>{statusMsg ?? 'Executing…'}</span>
            </div>
        {:else if !hasLayout}
            <div class="empty-state">
                <div class="empty-arrow">⬇</div>
                <p>
                    {$editMode
                        ? 'Write SQL below and press Ctrl+Enter to run'
                        : 'Switch to Edit mode to write SQL and create panels'}
                </p>
                {#if $editMode}
                    <p class="hint">Separate multiple queries with <code>;</code> — each becomes a panel</p>
                {/if}
            </div>
        {:else if layout}
            <DashboardGrid
                {layout}
                onEditSQL={handleEditSQL}
                onExplain={handleExplain}
                onDelete={handleDelete}
            />
        {/if}
    </div>

    <!-- Editor section — hidden in Preview mode -->
    {#if $editMode}
        <div class="editor-section">
            <div class="editor-toolbar">
                <button class="run-btn" onclick={run} disabled={executing}>
                    <span class="run-icon" class:spinning={executing}>▶</span>
                    {executing ? (statusMsg ?? 'Running…') : 'Run'}
                </button>
                <kbd class="shortcut">Ctrl+Enter</kbd>

                {#if errorMsg}
                    <div class="error-chip" title={errorMsg}>
                        <span>✕</span>
                        <span class="error-text">{errorMsg}</span>
                    </div>
                {:else if executing && statusMsg && hasLayout}
                    <span class="exec-inline">{statusMsg}</span>
                {/if}
            </div>

            <div class="editor-wrapper">
                <SQLEditor bind:value={sql} onRun={run} disabled={executing} {theme} />
            </div>
        </div>
    {/if}
</div>

<!-- Toast notification -->
{#if toast}
    <div class="toast" role="status" aria-live="polite">{toast}</div>
{/if}

<!-- Explainability drawer (Phase 5.6) — always mounted, visible when explainTarget is set -->
<ExplainPanel />

<style>
    .app-shell {
        height: 100vh;
        display: flex;
        flex-direction: column;
        background: var(--sqlviz-bg-base);
        overflow: hidden;
    }

    /* ── App bar ──────────────────────────────────────────────── */
    .app-bar {
        height: 48px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 1rem;
        background: var(--sqlviz-bg-surface);
        border-bottom: 1px solid var(--sqlviz-border);
        flex-shrink: 0;
    }

    .app-logo {
        font-size: 1rem;
        font-weight: 700;
        color: var(--sqlviz-primary);
        letter-spacing: -0.02em;
    }

    .mode-toggle {
        display: flex;
        border: 1px solid var(--sqlviz-border);
        border-radius: var(--sqlviz-radius);
        overflow: hidden;
    }

    .mode-btn {
        padding: 0.25rem 0.875rem;
        background: none;
        border: none;
        cursor: pointer;
        font-size: 0.8125rem;
        font-weight: 500;
        color: var(--sqlviz-text-muted);
        transition: background 0.15s, color 0.15s;
    }

    .mode-btn.active {
        background: var(--sqlviz-primary);
        color: #fff;
    }

    .mode-btn:not(.active):hover {
        background: var(--sqlviz-bg-base);
        color: var(--sqlviz-text);
    }

    .bar-right {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .theme-btn {
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: none;
        border: 1px solid var(--sqlviz-border);
        border-radius: var(--sqlviz-radius);
        cursor: pointer;
        font-size: 1rem;
        color: var(--sqlviz-text-muted);
        transition: background 0.15s, color 0.15s, border-color 0.15s;
        line-height: 1;
    }

    .theme-btn:hover {
        background: var(--sqlviz-bg);
        color: var(--sqlviz-text);
        border-color: var(--sqlviz-primary);
    }

    /* ── Dashboard area ──────────────────────────────────────── */
    .dashboard-area {
        flex: 1;
        overflow-y: auto;
        min-height: 0;
    }

    .dashboard-area.empty {
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .state-msg {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.75rem;
        color: var(--sqlviz-text-muted);
        font-size: 0.9375rem;
    }

    .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.5rem;
        color: var(--sqlviz-text-muted);
        text-align: center;
    }

    .empty-arrow {
        font-size: 2.5rem;
        opacity: 0.2;
        margin-bottom: 0.25rem;
    }

    .empty-state p {
        margin: 0;
        font-size: 0.9375rem;
    }

    .hint {
        font-size: 0.8125rem !important;
        opacity: 0.6;
    }

    .spinner {
        font-size: 2rem;
        animation: spin 1.2s linear infinite;
        display: inline-block;
    }

    @keyframes spin { to { transform: rotate(360deg); } }

    /* ── Editor section ──────────────────────────────────────── */
    .editor-section {
        height: 300px;
        flex-shrink: 0;
        border-top: 1px solid var(--sqlviz-border);
        display: flex;
        flex-direction: column;
    }

    .editor-toolbar {
        height: 44px;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0 0.875rem;
        background: var(--sqlviz-bg-surface);
        border-bottom: 1px solid var(--sqlviz-border);
        flex-shrink: 0;
        overflow: hidden;
    }

    .run-btn {
        display: flex;
        align-items: center;
        gap: 0.375rem;
        padding: 0.3125rem 0.875rem;
        background: var(--sqlviz-primary);
        color: #fff;
        border: none;
        border-radius: var(--sqlviz-radius);
        font-size: 0.8125rem;
        font-weight: 600;
        cursor: pointer;
        white-space: nowrap;
        transition: opacity 0.15s;
    }

    .run-btn:hover:not(:disabled) { opacity: 0.85; }
    .run-btn:disabled { opacity: 0.5; cursor: not-allowed; }

    .run-icon {
        font-size: 0.625rem;
        line-height: 1;
    }

    .run-icon.spinning {
        animation: spin 1s linear infinite;
        display: inline-block;
    }

    .shortcut {
        font-family: var(--sqlviz-font-mono);
        font-size: 0.6875rem;
        background: var(--sqlviz-bg-base);
        border: 1px solid var(--sqlviz-border);
        border-radius: var(--sqlviz-radius);
        padding: 0.125rem 0.375rem;
        color: var(--sqlviz-text-muted);
    }

    .error-chip {
        display: flex;
        align-items: center;
        gap: 0.375rem;
        color: var(--sqlviz-negative);
        font-size: 0.8125rem;
        min-width: 0;
    }

    .error-text {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .exec-inline {
        font-size: 0.8125rem;
        color: var(--sqlviz-text-muted);
    }

    .editor-wrapper {
        flex: 1;
        min-height: 0;
    }

    /* ── Toast ───────────────────────────────────────────────── */
    .toast {
        position: fixed;
        bottom: 1.25rem;
        left: 50%;
        transform: translateX(-50%);
        background: var(--sqlviz-bg-surface);
        border: 1px solid var(--sqlviz-border);
        border-radius: var(--sqlviz-radius-lg);
        padding: 0.625rem 1.125rem;
        font-size: 0.875rem;
        color: var(--sqlviz-text);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        z-index: 1000;
        white-space: nowrap;
        pointer-events: none;
    }

    kbd {
        font-family: var(--sqlviz-font-mono);
    }

    code {
        font-family: var(--sqlviz-font-mono);
        font-size: 0.875em;
        background: var(--sqlviz-bg-surface);
        border: 1px solid var(--sqlviz-border);
        border-radius: var(--sqlviz-radius);
        padding: 0.1em 0.35em;
    }
</style>
