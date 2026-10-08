import { browser } from '$app/environment';
import { get } from 'svelte/store';
import { apiDelete, apiGet, apiPatch, apiPost, recompose, type ExecResult } from '$lib/api';
import type { DashboardInfo, DashboardLayout, FilterControl, FilterDomain, FolderInfo, InferenceResult } from '$lib/types';
import { dashboardCache } from './dashboardCache.svelte';
import { editorRef } from './editorRef';
import { explainTarget } from './explainStore';
import { executionStore } from './executionStore.svelte';
import { filterValues } from './filterValues.svelte';
import { uiStore } from './uiStore.svelte';
import { getPaletteById } from '$lib/charts/palettes';
import { fetchFilterDomains } from '$lib/filters/filterDomains';
import { createFilterRuntime, patchFilterResults } from '$lib/filters/filterRuntime.svelte';

export type { ExecResult };

export type ChartOverrideResult = { saved: boolean; error: string | null };

/**
 * Owns the author workspace: active dashboard, SQL drafts, panel execution,
 * confirmed results, layout and cache. Preview adapts the shared filter runtime
 * to this state; scoped viewers keep their own state and transport.
 */
export function createDashboardStore() {
    let viewGeneration = 0;
    let domainGeneration = 0;
    let sizeWrites: Promise<void> = Promise.resolve();
    let presentationWrites: Promise<void> = Promise.resolve();
    let chartWrites: Promise<void> = Promise.resolve();
    let dashboardId      = $state<string | null>(null);
    let allDashboards    = $state<DashboardInfo[]>([]);
    let folders          = $state<FolderInfo[]>([]);
    let dashboardsLoading = $state(true);
    let viewLoading = $state(false);
    let panelIds         = $state<string[]>([]);
    let panelSQLs        = $state<string[]>([]);
    let executedResults  = $state<ExecResult[]>([]);
    let layout           = $state<DashboardLayout | null>(null);
    let sql               = $state('');

    // Panel Properties panel (v0.2.9): which panel's side panel is open, plus
    // session-only palette overrides per panel (keyed by panel_id).
    let propertiesPanelId = $state<string | null>(null);
    let colorOverrides    = $state<Record<string, string[]>>({});

    // Dashboard-level chart palette (one palette for every panel, so the whole
    // dashboard reads as one system). Stored by id, persisted per dashboard.
    let dashboardPaletteId = $state<string>('brand');
    function paletteKey(id: string) { return `sqlviz-dashboard-palette:${id}`; }
    function loadPaletteFor(id: string | null) {
        if (!id || !browser) { dashboardPaletteId = 'brand'; return; }
        try { dashboardPaletteId = localStorage.getItem(paletteKey(id)) || 'brand'; }
        catch { dashboardPaletteId = 'brand'; }
    }
    function setDashboardPalette(paletteId: string) {
        dashboardPaletteId = paletteId;
        if (dashboardId && browser) {
            try { localStorage.setItem(paletteKey(dashboardId), paletteId); } catch { /* ignore */ }
        }
    }

    // Domain (distinct values / numeric bounds) per filter variable, keyed by
    // control.variable. Populated lazily after execution so dropdown / multiselect
    // / range_slider controls can render real options instead of a text box.
    let filterDomains    = $state<Record<string, FilterDomain>>({});

    // Draft auto-save (sqlviz-ux-dashboard-editing-v1.0 §1). last_run_at drives
    // the "Last run X min ago" prompt after a refresh.
    let lastRunAt        = $state<string | null>(null);
    // Exact SQL of the last successful run (persisted, separate from the draft)
    // so the header can offer "Restore last run" while the two differ.
    let lastRunSql       = $state('');
    // The SQL last persisted to the dashboard draft — used to tell a real user
    // edit apart from a programmatic load (which must not mark the draft dirty).
    let lastSavedSql     = '';

    let saveDebounceTimer   = 0;
    const ACTIVE_KEY = 'sqlviz-active-dashboard';

    const hasLayout = $derived(layout !== null && layout.rows.length > 0);
    const activeDashboard = $derived(allDashboards.find(d => d.id === dashboardId) ?? null);

    // Score button: utility_score from DashboardLayout (DOC6 §12.3).
    const utilityPct = $derived(
        layout?.utility_score != null
            ? Math.round(layout.utility_score * 100)
            : null
    );

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
    const filterRuntime = createFilterRuntime({
        getScope: () => viewGeneration,
        getResults: () => executedResults,
        getValues: () => filterValues.current,
        execute: (id, variables) => apiPost(`/api/v1/panels/${id}/execute`, { variables }),
        commit: (results, values) => {
            if (layout) layout = patchFilterResults(layout, results);
            executedResults = results;
            filterValues.replace(values);
        },
    });


    // The panel whose Properties panel is currently open (looked up in layout).
    const selectedPanel = $derived.by(() => {
        if (!layout || !propertiesPanelId) return null;
        for (const row of layout.rows) {
            for (const p of row.panels) {
                if (p.panel_id === propertiesPanelId) return p;
            }
        }
        return null;
    });

    /** Splits editor SQL into individual statements — one statement becomes one panel. */
    function splitStatements(text: string): string[] {
        return text.split(';').map(s => s.trim()).filter(s => s.length > 0);
    }

    const statementCount = $derived(splitStatements(sql).length);

    // "Restore last run" is offered while there is a prior successful run whose
    // SQL differs from the current draft.
    const canRestoreLastRun = $derived(lastRunSql !== '' && sql !== lastRunSql);

    /** Reloads the dashboards + folders lists (after any create/rename/move/delete). */
    async function refreshExplorer() {
        try {
            const [dashboards, fldrs] = await Promise.all([
                apiGet<DashboardInfo[]>('/api/v1/dashboards'),
                apiGet<FolderInfo[]>('/api/v1/folders'),
            ]);
            allDashboards = dashboards;
            folders = fldrs;
        } catch {
            // keep current lists on failure
        }
    }

    // ── Draft auto-save (UX spec §1) ─────────────────────────────────────────
    function persistActive(id: string | null) {
        try {
            if (id) localStorage.setItem(ACTIVE_KEY, id);
            else localStorage.removeItem(ACTIVE_KEY);
        } catch { /* private mode / no storage */ }
    }

    /** Adopt a set of SQL as the current, already-saved baseline (on load/run). */
    function markSqlSaved(text: string) {
        lastSavedSql = text;
        clearTimeout(saveDebounceTimer);
        if (executionStore.saveStatus === 'draft') executionStore.saveStatus = 'idle';
    }

    /** Called from the public `sql` setter on every editor change. */
    function onSqlChanged(v: string) {
        if (!dashboardId) return;
        // The cached view is only valid while the draft matches the SQL that
        // produced it. Any divergence makes those charts stale — drop the entry
        // so navigating back shows an empty editor (a re-run) rather than results
        // that no longer match the query.
        const cached = dashboardCache.get(dashboardId);
        if (cached && cached.sql !== v) dashboardCache.invalidate(dashboardId);
        if (v === lastSavedSql) {
            // Back to the saved state (e.g. programmatic load / undo) — clean.
            clearTimeout(saveDebounceTimer);
            if (executionStore.saveStatus !== 'saving') executionStore.saveStatus = 'idle';
            return;
        }
        // A real edit supersedes a prior error indicator.
        executionStore.errorMsg = null;
        executionStore.saveStatus = 'draft';
        clearTimeout(saveDebounceTimer);
        // 2 seconds after the user stops typing.
        saveDebounceTimer = window.setTimeout(() => saveDraft(), 2000);
    }

    /**
     * Persist the current editor text as the dashboard's draft. Silent — only
     * the subtle header indicator reflects it. `useBeacon` fires a fire-and-forget
     * request that survives page unload.
     */
    function saveDraft(useBeacon = false) {
        clearTimeout(saveDebounceTimer);
        if (!dashboardId || sql === lastSavedSql) return;
        const id = dashboardId;
        const text = sql;
        const path = `/api/v1/dashboards/${id}`;

        if (useBeacon) {
            // Page is unloading — keepalive lets the PATCH outlive the document.
            fetch(path, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sql_content: text }),
                keepalive: true,
            }).catch(() => {});
            lastSavedSql = text;
            return;
        }

        executionStore.saveStatus = 'saving';
        apiPatch(path, { sql_content: text })
            .then(() => {
                lastSavedSql = text;
                // Only flip to "saved" if nothing newer is pending.
                if (sql === text) {
                    executionStore.saveStatus = 'saved';
                    window.setTimeout(() => {
                        if (executionStore.saveStatus === 'saved') executionStore.saveStatus = 'idle';
                    }, 2000);
                }
            })
            .catch(() => { executionStore.saveStatus = 'draft'; });
    }

    /**
     * Replace the current draft with the SQL of the last successful run.
     * The change is treated like any edit — it auto-saves and the "Restore"
     * affordance disappears once the two match again.
     */
    function restoreLastRun() {
        if (lastRunSql === '' || sql === lastRunSql) return;
        sql = lastRunSql;
        onSqlChanged(sql);
        queueMicrotask(() => {
            get(editorRef).setContent?.(lastRunSql);
            get(editorRef).focusStatement?.(0);
        });
    }

    /** Loads the first existing dashboard, if any. Called once on mount. */
    async function bootstrap() {
        dashboardsLoading = true;
        try {
            const [dashboards, fldrs] = await Promise.all([
                apiGet<DashboardInfo[]>('/api/v1/dashboards'),
                apiGet<FolderInfo[]>('/api/v1/folders').catch(() => [] as FolderInfo[]),
            ]);
            allDashboards = dashboards;
            folders = fldrs;
            if (dashboards.length === 0) {
                // No auto-seeded example data — a fresh install shows the
                // welcome screen so the user creates their first dashboard.
                return;
            }

            // Restore the last active dashboard (refresh), else the first one.
            let saved: string | null = null;
            try { saved = localStorage.getItem(ACTIVE_KEY); } catch { /* no storage */ }
            const active = dashboards.find(d => d.id === saved) ?? dashboards[0];
            dashboardId = active.id;
            loadPaletteFor(active.id);
            persistActive(active.id);
            lastRunAt = active.last_run_at;
            lastRunSql = active.last_run_sql ?? '';

            const panels = await fetch(`/api/v1/panels?dashboard_id=${dashboardId}`)
                .then(r => r.json()) as Array<{ id: string; sql_content: string; sort_order: number }>;
            panels.sort((a, b) => a.sort_order - b.sort_order);
            panelIds  = panels.map(p => p.id);
            panelSQLs = panels.map(p => p.sql_content);

            // Prefer the saved draft (exact editor text); fall back to the
            // committed panel SQL for dashboards created before draft auto-save.
            const draft = active.sql_content || panelSQLs.join(';\n\n');
            sql = draft;
            markSqlSaved(draft);
            queueMicrotask(() => get(editorRef).setContent?.(draft));
            // Do NOT auto-run — refresh shows "Last run X ago" + Run Again.
        } catch {
            // Fresh install — no existing state
        } finally {
            dashboardsLoading = false;
        }
    }

    async function run() {
        if (executionStore.executing) return;

        const statements = splitStatements(sql);

        if (statements.length === 0) {
            executionStore.errorMsg = 'No SQL statements found. Write at least one query separated by ";".';
            return;
        }

        resetFilterUpdates();
        executionStore.executing = true;
        executionStore.errorMsg  = null;

        // Snapshot mutable state so mid-flight dashboard switches don't corrupt this run.
        let activeDashId = dashboardId;
        const activePanelIds = [...panelIds];

        try {
            if (!activeDashId) {
                const dash = await apiPost<{ id: string }>('/api/v1/dashboards', {
                    name: 'My Dashboard',
                    sort_order: 0,
                });
                activeDashId = dash.id;
                dashboardId  = activeDashId;
            }

            const results: ExecResult[] = [];
            const newPanelIds: string[] = [];

            for (let i = 0; i < statements.length; i++) {
                const stmt = statements[i];
                executionStore.statusMsg = `Statement ${i + 1} / ${statements.length}…`;

                let panelId: string;
                if (activePanelIds[i]) {
                    await apiPatch(`/api/v1/panels/${activePanelIds[i]}`, {
                        sql_content: stmt,
                        sort_order: i,
                    });
                    panelId = activePanelIds[i];
                } else {
                    const panel = await apiPost<{ id: string }>('/api/v1/panels', {
                        dashboard_id: activeDashId,
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

            // Only commit results if the dashboard hasn't changed mid-flight.
            if (dashboardId !== activeDashId) {
                executionStore.statusMsg = null;
                return;
            }

            panelIds        = newPanelIds;
            panelSQLs       = statements;
            executedResults = results;

            executionStore.statusMsg = 'Composing layout…';
            layout = await recompose(results);
            filterValues.reset();
            executionStore.statusMsg = null;

            // Successful run: persist the exact draft + a last-run timestamp so a
            // refresh can show "Last run X ago" (UX spec §"Run exitoso").
            const runAt = new Date().toISOString();
            const ranSql = sql;
            lastRunAt = runAt;
            lastRunSql = ranSql;
            markSqlSaved(ranSql);
            apiPatch(`/api/v1/dashboards/${activeDashId}`, {
                sql_content: ranSql,
                last_run_at: runAt,
                last_run_sql: ranSql,
            }).catch(() => {});

            // Load rich-control domains (dropdown options / slider bounds).
            loadFilterDomains();

            // Refresh dashboard list to pick up updated hint/domain from classifier.
            try {
                allDashboards = await fetch('/api/v1/dashboards')
                    .then(r => r.json()) as DashboardInfo[];
            } catch { /* non-critical */ }
        } catch (e: unknown) {
            executionStore.errorMsg  = e instanceof Error ? e.message : String(e);
            executionStore.statusMsg = null;
        } finally {
            executionStore.executing = false;
        }
    }

    async function handleDelete(panelId: string) {
        const idx = panelIds.indexOf(panelId);
        if (idx < 0) return;

        try {
            await fetch(`/api/v1/panels/${panelId}`, { method: 'DELETE' });
        } catch {
            uiStore.showToast('Delete failed — check the API server.');
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
            // No results left to cache — drop the stale entry so navigating back
            // doesn't restore the just-deleted panels (the auto-cache effect skips
            // empty views, so it can't clear this on its own).
            if (dashboardId) dashboardCache.invalidate(dashboardId);
            return;
        }

        try {
            layout = await recompose(newResults);
        } catch (e: unknown) {
            uiStore.showToast(e instanceof Error ? e.message : 'Compose failed after delete.');
        }
    }

    function handleEditSQL(panelId: string) {
        const idx = panelIds.indexOf(panelId);
        if (idx < 0) return;
        get(editorRef).focusStatement?.(idx);
    }

    function handleExplain(panelId: string) {
        const result = executedResults.find(r => r.panel_id === panelId);
        if (!result) {
            uiStore.showToast('Run the dashboard first to see explainability data.');
            return;
        }
        explainTarget.set(result);
    }

    /**
     * Create a new dashboard (optionally inside a folder), then switch to it —
     * empty, no query carried over from the previous dashboard.
     */
    async function createDashboard(name = 'New Dashboard', folderId: string | null = null) {
        const finalName = name.trim() || 'New Dashboard';
        uiStore.creatingDashboard = false;
        uiStore.newDashboardName  = '';
        try {
            const dash = await apiPost<{ id: string; name: string }>('/api/v1/dashboards', {
                name: finalName,
                folder_id: folderId,
                sort_order: allDashboards.length,
            });
            await refreshExplorer();
            resetFilterUpdates();
            // Switch to the empty new dashboard without running anything.
            dashboardId     = dash.id;
            persistActive(dash.id);
            panelIds        = [];
            panelSQLs       = [];
            sql             = '';
            markSqlSaved('');
            lastRunAt       = null;
            lastRunSql      = '';
            executedResults = [];
            layout          = null;
            filterDomains   = {};
            filterValues.reset();
            // Force the Monaco editor empty — a new dashboard must never inherit
            // the previous dashboard's query — then place the cursor at the start.
            queueMicrotask(() => {
                get(editorRef).setContent?.('');
                get(editorRef).focusStatement?.(0);
            });
        } catch (e: unknown) {
            uiStore.showToast(e instanceof Error ? e.message : 'Could not create dashboard.');
        }
    }

    /**
     * Switch to a different dashboard. Auto-saves the current draft first, then
     * loads the target's draft + last-run info.
     *
     * Navigation is now instant when the target has a cached view (a prior run
     * this session): its charts, layout, filter domains and filter selection are
     * restored from memory. With no cache the view is empty — the user re-runs.
     * Either way the Monaco editor shows the selected dashboard's own SQL, and
     * nothing is auto-executed (UX spec §"Cambiar de Dashboard").
     */
    async function loadDashboard(id: string) {
        if (id === dashboardId || executionStore.executing) return;

        const generation = ++viewGeneration;
        viewLoading = true;
        // Silently persist the current dashboard's draft before leaving it.
        saveDraft();

        // Drop any pending filter re-execution meant for the dashboard we leave.
        resetFilterUpdates();

        try {
            const [dash, panels] = await Promise.all([
                apiGet<DashboardInfo>(`/api/v1/dashboards/${id}`),
                fetch(`/api/v1/panels?dashboard_id=${id}`).then(r => r.json()) as Promise<
                    Array<{ id: string; sql_content: string; sort_order: number }>
                >,
            ]);
            if (generation !== viewGeneration) return;
            panels.sort((a, b) => a.sort_order - b.sort_order);

            dashboardId = id;
            loadPaletteFor(id);
            persistActive(id);
            lastRunAt   = dash.last_run_at;
            lastRunSql  = dash.last_run_sql ?? '';

            const cached = dashboardCache.get(id);
            if (cached) {
                // Cache hit — restore the executed view instantly (no re-run).
                panelIds        = [...cached.panelIds];
                panelSQLs       = [...cached.panelSQLs];
                executedResults = cached.executedResults;
                layout          = cached.layout;
                filterDomains   = cached.filterDomains;
                // Restore the filter selection; sync the change-detection
                // snapshot so this does NOT trigger a filter re-execution.
                filterValues.replace(cached.filterValues);
            } else {
                // Cache miss — empty view; results appear only on a manual re-run.
                panelIds        = panels.map(p => p.id);
                panelSQLs       = panels.map(p => p.sql_content);
                executedResults = [];
                layout          = null;
                filterDomains   = {};
                filterValues.reset();
            }

            // Prefer the saved draft; fall back to the committed panel SQL.
            const draft = dash.sql_content || panelSQLs.join(';\n\n');
            sql = draft;
            markSqlSaved(draft);
            queueMicrotask(() => {
                get(editorRef).setContent?.(draft);
                get(editorRef).focusStatement?.(0);
            });
        } catch (e: unknown) {
            if (generation === viewGeneration) uiStore.showToast(e instanceof Error ? e.message : 'Could not load dashboard.');
        } finally {
            if (generation === viewGeneration) viewLoading = false;
        }
    }

    /** Rename a dashboard (Explorer action). */
    async function renameDashboard(id: string, name: string) {
        const trimmed = name.trim();
        if (!trimmed) return;
        try {
            await apiPatch(`/api/v1/dashboards/${id}`, { name: trimmed });
            await refreshExplorer();
        } catch (e: unknown) {
            uiStore.showToast(e instanceof Error ? e.message : 'Rename failed.');
        }
    }

    /** Set (or clear, with "") a dashboard's description. */
    async function setDashboardDescription(id: string, description: string) {
        try {
            await apiPatch(`/api/v1/dashboards/${id}`, { description });
            await refreshExplorer();
        } catch (e: unknown) {
            uiStore.showToast(e instanceof Error ? e.message : 'Could not save description.');
        }
    }

    /** Move a dashboard to a folder (folderId=null → root). */
    async function moveDashboardToFolder(id: string, folderId: string | null) {
        try {
            // Backend treats "" as "move to root".
            await apiPatch(`/api/v1/dashboards/${id}`, { folder_id: folderId });
            await refreshExplorer();
        } catch (e: unknown) {
            uiStore.showToast(e instanceof Error ? e.message : 'Move failed.');
        }
    }

    /** Delete a dashboard from the Explorer; clears the view if it was active. */
    async function deleteDashboardById(id: string) {
        try {
            await apiDelete(`/api/v1/dashboards/${id}`);
            // Drop its cached view regardless of whether it was the active one.
            dashboardCache.invalidate(id);
            if (id === dashboardId) {
                dashboardId = null;
                panelIds = [];
                panelSQLs = [];
                sql = '';
                executedResults = [];
                layout = null;
                filterDomains = {};
                filterValues.reset();
            }
            await refreshExplorer();
        } catch (e: unknown) {
            uiStore.showToast(e instanceof Error ? e.message : 'Delete failed.');
        }
    }

    /** Create a new folder (group) in the Explorer. */
    async function createFolder(name: string) {
        const trimmed = name.trim();
        if (!trimmed) return;
        try {
            await apiPost('/api/v1/folders', { name: trimmed, sort_order: folders.length });
            await refreshExplorer();
        } catch (e: unknown) {
            uiStore.showToast(e instanceof Error ? e.message : 'Could not create group.');
        }
    }

    /** Update a dashboard's name and description in a single request. */
    async function updateDashboard(id: string, name: string, description: string) {
        const trimmed = name.trim();
        if (!trimmed) return;
        try {
            await apiPatch(`/api/v1/dashboards/${id}`, { name: trimmed, description: description.trim() });
            await refreshExplorer();
        } catch (e: unknown) {
            uiStore.showToast(e instanceof Error ? e.message : 'Could not save dashboard.');
        }
    }

    /** Rename a folder (group). */
    async function renameFolder(id: string, name: string) {
        const trimmed = name.trim();
        if (!trimmed) return;
        try {
            await apiPatch(`/api/v1/folders/${id}`, { name: trimmed });
            await refreshExplorer();
        } catch (e: unknown) {
            uiStore.showToast(e instanceof Error ? e.message : 'Could not rename group.');
        }
    }

    /**
     * Delete a folder (group). The backend re-parents its dashboards to root
     * (folder_id → NULL), so nothing is lost — only the container is removed.
     */
    async function deleteFolder(id: string) {
        try {
            await apiDelete(`/api/v1/folders/${id}`);
            await refreshExplorer();
        } catch (e: unknown) {
            uiStore.showToast(e instanceof Error ? e.message : 'Could not delete group.');
        }
    }

    /**
     * Drag-and-drop reorder / move. Places `dragId` before/after `targetId`
     * inside `targetFolderId` (null = root) and persists the new order via
     * per-dashboard sort_order, plus the dragged item's folder_id if it moved.
     */
    async function reorderDashboard(
        dragId: string,
        targetId: string | null,
        position: 'before' | 'after',
        targetFolderId: string | null,
    ) {
        if (dragId === targetId) return;
        const dragged = allDashboards.find(d => d.id === dragId);
        if (!dragged) return;

        // Ordered list of the destination folder, excluding the dragged item.
        const dest = allDashboards
            .filter(d => (d.folder_id ?? null) === targetFolderId && d.id !== dragId)
            .sort((a, b) => a.sort_order - b.sort_order);

        let insertAt = dest.length;
        if (targetId) {
            const ti = dest.findIndex(d => d.id === targetId);
            if (ti !== -1) insertAt = position === 'before' ? ti : ti + 1;
        }
        dest.splice(insertAt, 0, dragged);

        const folderChanged = (dragged.folder_id ?? null) !== targetFolderId;
        try {
            await Promise.all(dest.map((d, i) => {
                const body: Record<string, unknown> = {};
                if (d.sort_order !== i) body.sort_order = i;
                if (d.id === dragId && folderChanged) body.folder_id = targetFolderId;
                return Object.keys(body).length
                    ? apiPatch(`/api/v1/dashboards/${d.id}`, body)
                    : Promise.resolve();
            }));
            await refreshExplorer();
        } catch (e: unknown) {
            uiStore.showToast(e instanceof Error ? e.message : 'Could not reorder.');
        }
    }

    /** Publish a confirmed chart and composition together; keep the last chart on failure. */
    function handleChartOverride(
        panelId: string, chartType: string | null, refreshOnly = false,
    ): Promise<ChartOverrideResult> {
        const generation = viewGeneration;
        const targetDashboard = dashboardId;
        const current = () => generation === viewGeneration && targetDashboard === dashboardId;
        const task = chartWrites.then(async (): Promise<ChartOverrideResult> => {
            try {
                if (!refreshOnly) {
                    try {
                        await apiPatch(`/api/v1/panels/${panelId}/override`, {
                            field_name: 'chart_type', user_value: chartType,
                        });
                    } catch (cause: unknown) {
                        const reason = cause instanceof Error ? cause.message : 'Could not save chart type.';
                        return { saved: false, error: `${reason} The previous chart is kept; retry when ready.` };
                    }
                }
                if (!current()) return { saved: true, error: null };
                const snapshot = executedResults;
                try {
                    const exec = await apiPost<{
                        inference_result: InferenceResult; data: Record<string, unknown>[];
                    }>(`/api/v1/panels/${panelId}/execute`, { variables: { ...filterValues.current } });
                    if (!current()) return { saved: true, error: null };
                    const next = snapshot.map(r => r.panel_id === panelId ? { ...r, ...exec } : r);
                    const composed = await recompose(next);
                    if (!current()) return { saved: true, error: null };
                    if (snapshot !== executedResults) {
                        return { saved: true, error: 'Chart type saved. The view changed during refresh; retry refresh.' };
                    }
                    executedResults = next;
                    layout = composed;
                    return { saved: true, error: null };
                } catch {
                    return { saved: true, error: 'Chart type saved. Could not refresh the chart; retry refresh or run it again.' };
                }
            } finally {
                // Also invalidate after transport failures whose commit status is unknown.
                if (targetDashboard) dashboardCache.invalidate(targetDashboard);
            }
        });
        chartWrites = task.then(() => {}, () => {});
        return task;
    }

    /** Immutably patch one panel's inference_result inside executedResults. */
    function patchExecutedResult(panelId: string, patch: Partial<InferenceResult>) {
        executedResults = executedResults.map(r =>
            r.panel_id === panelId
                ? { ...r, inference_result: { ...r.inference_result, ...patch } }
                : r
        );
    }

    /** Re-execute one panel and recompose, so the view matches persisted state. */
    async function refreshPanel(panelId: string) {
        const exec = await apiPost<{ inference_result: InferenceResult; data: Record<string, unknown>[] }>(
            `/api/v1/panels/${panelId}/execute`
        );
        executedResults = executedResults.map(r =>
            r.panel_id === panelId
                ? { panel_id: panelId, inference_result: exec.inference_result, data: exec.data }
                : r
        );
        layout = await recompose(executedResults);
    }

    /** Serialize size saves; reflect only values confirmed by the project. */
    function persistSizeOverride(
        panelId: string,
        field: 'col_span' | 'height_px',
        value: number | null,
    ): Promise<void> {
        if (!layout) return Promise.resolve();
        const generation = viewGeneration;
        const targetDashboard = dashboardId;
        const task = sizeWrites.then(async () => {
            let saved: { selected_col_span: number | null; selected_height_px: number | null };
            try {
                saved = await apiPatch(`/api/v1/panels/${panelId}/override`, {
                    field_name: field,
                    user_value: value === null ? null : String(value),
                });
            } catch (e: unknown) {
                uiStore.showToast(e instanceof Error ? e.message : 'Could not save the panel size.');
                return;
            }
            if (targetDashboard) dashboardCache.invalidate(targetDashboard);
            if (generation !== viewGeneration || targetDashboard !== dashboardId) return;
            const effective = field === 'col_span' ? saved.selected_col_span : saved.selected_height_px;
            if (effective === null) return;
            const patch = field === 'col_span' ? { col_span: effective } : { panel_height_px: effective };
            patchPanelResult(panelId, patch);
            patchExecutedResult(panelId, patch);
            if (field === 'col_span' && layout) {
                layout = {
                    ...layout,
                    rows: layout.rows.map(row => ({
                        ...row,
                        panels: row.panels.map(p => p.panel_id === panelId
                            ? { ...p, final_col_span: effective } : p),
                    })),
                };
            }
            const snapshot = executedResults;
            try {
                const composed = await recompose(snapshot);
                if (generation === viewGeneration && snapshot === executedResults) layout = composed;
            } catch {
                uiStore.showToast('Size saved. Could not refresh the dashboard layout; run it again.');
            }
        });
        sizeWrites = task.catch(() => {});
        return task;
    }

    function handleWidthOverride(panelId: string, cols: number | null) {
        return persistSizeOverride(panelId, 'col_span', cols);
    }

    function handleHeightOverride(panelId: string, px: number | null) {
        return persistSizeOverride(panelId, 'height_px', px);
    }

    // ── Panel Properties panel (v0.2.9) ──────────────────────────────────────
    function openPanelProperties(panelId: string) { propertiesPanelId = panelId; }
    function closePanelProperties() { propertiesPanelId = null; }

    /** Immutably replace one panel's inference_result in the local layout. */
    function patchPanelResult(panelId: string, patch: Partial<InferenceResult>) {
        if (!layout) return;
        layout = {
            ...layout,
            rows: layout.rows.map(row => ({
                panels: row.panels.map(p =>
                    p.panel_id === panelId
                        ? { ...p, inference_result: { ...p.inference_result, ...patch } }
                        : p
                ),
            })),
        };
    }

    /** Session-only title override — updates the panel header immediately. */
    function handleTitleOverride(panelId: string, title: string) {
        patchPanelResult(panelId, { title });
    }

    /** Immutably patch one panel's visual_spec in the local layout. */
    function patchPanelVisualSpec(panelId: string, patch: Record<string, unknown>) {
        if (!layout) return;
        layout = {
            ...layout,
            rows: layout.rows.map(row => ({
                panels: row.panels.map(p =>
                    p.panel_id === panelId && p.inference_result.visual_spec
                        ? { ...p, inference_result: { ...p.inference_result, visual_spec: { ...p.inference_result.visual_spec, ...patch } } }
                        : p
                ),
            })),
        };
    }

    /**
     * Presentation override (panel title / axis label). Patches the local layout
     * after confirmation, so rejected writes never replace the current chart.
     * Returns an actionable error while the input retains its unsaved draft.
     */
    function setViewOverride(
        panelId: string, field: 'title' | 'x_label' | 'y_label', value: string,
    ): Promise<string | null> {
        const generation = viewGeneration;
        const targetDashboard = dashboardId;
        const current = () => generation === viewGeneration && targetDashboard === dashboardId;
        const task = presentationWrites.then(async () => {
            try {
                let saved: { field: string; value: string | null };
                try {
                    saved = await apiPatch(`/api/v1/panels/${panelId}/view-override`, { field, value });
                } catch (cause: unknown) {
                    const reason = cause instanceof Error ? cause.message : 'Could not save.';
                    return `${reason} Your text is kept; retry when ready.`;
                }
                if (!current()) return null;
                if (field === 'title' && saved.value === null) {
                    // An incoming result already contains its persisted title:
                    // clearing it requires the engine's actual automatic title.
                    const snapshot = executedResults;
                    try {
                        const exec = await apiPost<{
                            inference_result: InferenceResult; data: Record<string, unknown>[];
                        }>(`/api/v1/panels/${panelId}/execute`, { variables: { ...filterValues.current } });
                        if (!current() || snapshot !== executedResults) return null;
                        const next = snapshot.map(r => r.panel_id === panelId ? { ...r, ...exec } : r);
                        const composed = await recompose(next);
                        if (current() && snapshot === executedResults) {
                            executedResults = next;
                            layout = composed;
                        }
                    } catch {
                        return 'Title reset saved. Could not refresh the chart; retry or run it again.';
                    }
                } else if (field === 'title') {
                    patchPanelResult(panelId, { title: saved.value! });
                    patchExecutedResult(panelId, { title: saved.value! });
                } else {
                    patchPanelVisualSpec(panelId, { [field]: saved.value });
                    executedResults = executedResults.map(r =>
                        r.panel_id === panelId && r.inference_result.visual_spec
                            ? { ...r, inference_result: { ...r.inference_result, visual_spec: {
                                ...r.inference_result.visual_spec, [field]: saved.value,
                            } } } : r,
                    );
                }
                return null;
            } finally {
                // Navigation may have cached the old chart while the save was
                // pending. Also invalidate after an ambiguous transport failure.
                if (targetDashboard) dashboardCache.invalidate(targetDashboard);
            }
        });
        presentationWrites = task.then(() => {}, () => {});
        return task;
    }

    /** Session-only X/Y axis override — mutates the panel's visual_spec. */
    function handleAxisOverride(
        panelId: string,
        patch: { x_field?: string | null; y_fields?: string[] },
    ) {
        if (!layout) return;
        layout = {
            ...layout,
            rows: layout.rows.map(row => ({
                panels: row.panels.map(p => {
                    if (p.panel_id !== panelId || !p.inference_result.visual_spec) return p;
                    return {
                        ...p,
                        inference_result: {
                            ...p.inference_result,
                            visual_spec: { ...p.inference_result.visual_spec, ...patch },
                        },
                    };
                }),
            })),
        };
    }

    /** Session-only palette override; null clears it (back to theme palette). */
    function handleColorOverride(panelId: string, palette: string[] | null) {
        const next = { ...colorOverrides };
        if (palette) next[panelId] = palette;
        else delete next[panelId];
        colorOverrides = next;
    }

    /** Edit a single panel's SQL: PATCH → re-execute that panel → recompose. */
    async function handlePanelSqlChange(panelId: string, newSql: string) {
        const trimmed = newSql.trim();
        if (!trimmed) return;
        try {
            await apiPatch(`/api/v1/panels/${panelId}`, { sql_content: trimmed });
            const exec = await apiPost<{ inference_result: InferenceResult; data: Record<string, unknown>[] }>(
                `/api/v1/panels/${panelId}/execute`
            );
            executedResults = executedResults.map(r =>
                r.panel_id === panelId ? { panel_id: panelId, ...exec } : r
            );
            const idx = panelIds.indexOf(panelId);
            if (idx >= 0) panelSQLs[idx] = trimmed;
            layout = await recompose(executedResults);
        } catch (e: unknown) {
            uiStore.showToast(e instanceof Error ? e.message : 'Could not run panel SQL.');
        }
    }

    /**
     * Fetch the domain (distinct values / numeric bounds) for every filter
     * control that renders a rich widget, so the filter editor can show a real
     * dropdown / multiselect / slider. Best-effort: failures leave the entry
     * absent and the control falls back to a text/number input.
     *
     * Domains are computed from the panel SQL with its parametric WHERE
     * stripped, so they do not depend on the current filter selection and
     * only need to be loaded once per execution.
     */
    function resetFilterUpdates() {
        domainGeneration++;
        filterRuntime.reset();
    }

    async function loadFilterDomains() {
        const request = ++domainGeneration;
        const generation = viewGeneration;
        const isCurrent = () => request === domainGeneration && generation === viewGeneration;
        const domains = await fetchFilterDomains({
            results: executedResults, isCurrent,
            fetch: (id, column, kind) => apiPost(`/api/v1/panels/${id}/filter-domain`, { column, kind }),
        });
        if (isCurrent()) filterDomains = domains;
    }

    /**
     * Refresh changed panels' data + inference in the CURRENT layout, keyed by
     * panel_id, without touching their position or size. This is what makes a
     * filter change update the charts in place: re-running `recompose` instead
     * would send the new results back through the layout optimizer, which can
     * reorder / re-flow the panels — exactly the "charts jump around when I
     * filter" bug. Geometry (final_col_span, col_offset, row_index) and the
     * row/panel ordering are preserved verbatim.
     */
    function applyResultsToLayout(current: DashboardLayout, results: ExecResult[]): DashboardLayout {
        const byId = new Map(results.map(r => [r.panel_id, r]));
        return {
            ...current,
            rows: current.rows.map(row => ({
                panels: row.panels.map(p => {
                    const r = byId.get(p.panel_id);
                    return r
                        ? { ...p, inference_result: r.inference_result, data: r.data }
                        : p;
                }),
            })),
        };
    }

    /**
     * Snapshot the current dashboard's executed view into the in-memory cache,
     * keyed by dashboard_id, so navigating back restores it instantly. `sql` is
     * stored as `lastRunSql` — the query these results actually correspond to —
     * which is what `onSqlChanged` compares against to invalidate.
     */
    function cacheCurrentView() {
        if (!dashboardId || executedResults.length === 0) return;
        dashboardCache.set(dashboardId, {
            sql: lastRunSql,
            panelIds: [...panelIds],
            panelSQLs: [...panelSQLs],
            executedResults,
            layout,
            filterDomains,
            filterValues: { ...filterValues.current },
        });
    }

    // Cache only confirmed results and filters. Drafts belong to FilterContext.
    if (browser) {
        $effect.root(() => {
            // Auto-cache: whenever the active dashboard's executed view changes
            // (run, filter re-exec, chart/panel override, delete), mirror it into
            // the results cache. Reads dashboardId + executedResults + layout +
            // filterDomains, so it re-runs on any of them. Fires once per batch
            // with the final values, so the transient empty state during a
            // dashboard switch is never observed.
            $effect(() => {
                void dashboardId;
                void executedResults;
                void layout;
                void filterDomains;
                cacheCurrentView();
            });

        });
    }

    return {
        get dashboardId() { return dashboardId; },
        get allDashboards() { return allDashboards; },
        get folders() { return folders; },
        get dashboardsLoading() { return dashboardsLoading; },
        get viewLoading() { return viewLoading; },
        get panelIds() { return panelIds; },
        get panelSQLs() { return panelSQLs; },
        get executedResults() { return executedResults; },
        get layout() { return layout; },
        get sql() { return sql; },
        set sql(v: string) { sql = v; onSqlChanged(v); },

        get hasLayout() { return hasLayout; },
        get lastRunAt() { return lastRunAt; },
        get canRestoreLastRun() { return canRestoreLastRun; },
        get propertiesPanelId() { return propertiesPanelId; },
        get selectedPanel() { return selectedPanel; },
        get colorOverrides() { return colorOverrides; },
        get dashboardPaletteId() { return dashboardPaletteId; },
        get dashboardPalette() { return getPaletteById(dashboardPaletteId).colors; },
        setDashboardPalette,
        setViewOverride,
        get activeDashboard() { return activeDashboard; },
        get utilityPct() { return utilityPct; },
        get allFilterControls() { return allFilterControls; },
        get filterDomains() { return filterDomains; },
        get hasFilters() { return hasFilters; },
        get statementCount() { return statementCount; },

        bootstrap,
        run,
        saveDraft,
        restoreLastRun,
        handleDelete,
        handleEditSQL,
        handleExplain,
        createDashboard,
        loadDashboard,
        renameDashboard,
        setDashboardDescription,
        updateDashboard,
        moveDashboardToFolder,
        reorderDashboard,
        deleteDashboardById,
        createFolder,
        renameFolder,
        deleteFolder,
        handleChartOverride,
        handleWidthOverride,
        handleHeightOverride,
        applyFilters: filterRuntime.apply,
        resetFilterUpdates,
        get filterBusy() { return filterRuntime.busy; },
        get filterError() { return filterRuntime.error; },
        openPanelProperties,
        closePanelProperties,
        handleTitleOverride,
        handleAxisOverride,
        handleColorOverride,
        handlePanelSqlChange,
    };
}

export const dashboardStore = createDashboardStore();
