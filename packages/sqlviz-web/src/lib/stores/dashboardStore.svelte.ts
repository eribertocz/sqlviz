import { get } from 'svelte/store';
import { apiDelete, apiGet, apiPatch, apiPost, recompose, type ExecResult } from '$lib/api';
import type { DashboardInfo, DashboardLayout, FilterControl, FilterDomain, FolderInfo, InferenceResult } from '$lib/types';
import { editorRef } from './editorRef';
import { explainTarget } from './explainStore';
import { executionStore } from './executionStore.svelte';
import { filterValues } from './filterValues';
import { uiStore } from './uiStore.svelte';

export type { ExecResult };

/**
 * Owns the dashboard/panel state cluster that used to live directly in
 * routes/+page.svelte: which dashboard is active, its panels, their SQL,
 * the last executed results, and the composed layout. Methods here are
 * ported 1:1 from the pre-v0.2.5 +page.svelte — behavior is unchanged,
 * only where the state/logic lives.
 */
function createDashboardStore() {
    let dashboardId      = $state<string | null>(null);
    let allDashboards    = $state<DashboardInfo[]>([]);
    let folders          = $state<FolderInfo[]>([]);
    let dashboardsLoading = $state(true);
    let panelIds         = $state<string[]>([]);
    let panelSQLs        = $state<string[]>([]);
    let executedResults  = $state<ExecResult[]>([]);
    let layout           = $state<DashboardLayout | null>(null);
    let sql               = $state('');

    // Panel Properties panel (v0.2.9): which panel's side panel is open, plus
    // session-only palette overrides per panel (keyed by panel_id).
    let propertiesPanelId = $state<string | null>(null);
    let colorOverrides    = $state<Record<string, string[]>>({});

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

    let filterDebounceTimer = 0;
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
     * loads the target's draft + last-run info. Does NOT re-execute (UX spec
     * §"Cambiar de Dashboard": show last charts / Run Again, no auto-run).
     */
    async function loadDashboard(id: string) {
        if (id === dashboardId || executionStore.executing) return;

        // Silently persist the current dashboard's draft before leaving it.
        saveDraft();

        try {
            const [dash, panels] = await Promise.all([
                apiGet<DashboardInfo>(`/api/v1/dashboards/${id}`),
                fetch(`/api/v1/panels?dashboard_id=${id}`).then(r => r.json()) as Promise<
                    Array<{ id: string; sql_content: string; sort_order: number }>
                >,
            ]);
            panels.sort((a, b) => a.sort_order - b.sort_order);

            dashboardId = id;
            persistActive(id);
            panelIds    = panels.map(p => p.id);
            panelSQLs   = panels.map(p => p.sql_content);
            lastRunAt   = dash.last_run_at;
            lastRunSql  = dash.last_run_sql ?? '';
            executedResults = [];
            layout      = null;

            // Prefer the saved draft; fall back to the committed panel SQL.
            const draft = dash.sql_content || panelSQLs.join(';\n\n');
            sql = draft;
            markSqlSaved(draft);
            queueMicrotask(() => {
                get(editorRef).setContent?.(draft);
                get(editorRef).focusStatement?.(0);
            });
        } catch (e: unknown) {
            uiStore.showToast(e instanceof Error ? e.message : 'Could not load dashboard.');
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
            await apiPatch(`/api/v1/dashboards/${id}`, { folder_id: folderId ?? '' });
            await refreshExplorer();
        } catch (e: unknown) {
            uiStore.showToast(e instanceof Error ? e.message : 'Move failed.');
        }
    }

    /** Delete a dashboard from the Explorer; clears the view if it was active. */
    async function deleteDashboardById(id: string) {
        try {
            await apiDelete(`/api/v1/dashboards/${id}`);
            if (id === dashboardId) {
                dashboardId = null;
                panelIds = [];
                panelSQLs = [];
                sql = '';
                executedResults = [];
                layout = null;
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
                if (d.id === dragId && folderChanged) body.folder_id = targetFolderId ?? '';
                return Object.keys(body).length
                    ? apiPatch(`/api/v1/dashboards/${d.id}`, body)
                    : Promise.resolve();
            }));
            await refreshExplorer();
        } catch (e: unknown) {
            uiStore.showToast(e instanceof Error ? e.message : 'Could not reorder.');
        }
    }

    /** Chart type override: PATCH → re-execute → recompose (DOC6 §12.1). */
    async function handleChartOverride(panelId: string, chartType: string) {
        try {
            await apiPatch(`/api/v1/panels/${panelId}/override`, {
                field_name: 'chart_type',
                user_value: chartType,
            });
            const exec = await apiPost<{ inference_result: InferenceResult; data: Record<string, unknown>[] }>(
                `/api/v1/panels/${panelId}/execute`
            );
            executedResults = executedResults.map(r =>
                r.panel_id === panelId
                    ? { panel_id: panelId, inference_result: exec.inference_result, data: exec.data }
                    : r
            );
            layout = await recompose(executedResults);
        } catch (e: unknown) {
            uiStore.showToast(e instanceof Error ? e.message : 'Chart override failed.');
        }
    }

    /** Local col_span override — updates layout reactively (session-only). */
    function handleWidthOverride(panelId: string, cols: number | null) {
        if (!layout) return;
        layout = {
            ...layout,
            rows: layout.rows.map(row => ({
                panels: row.panels.map(p => {
                    if (p.panel_id !== panelId) return p;
                    return {
                        ...p,
                        final_col_span: cols ?? p.inference_result.col_span,
                    };
                }),
            })),
        };
    }

    /** Local panel_height_px override — updates layout reactively (session-only). */
    function handleHeightOverride(panelId: string, px: number | null) {
        if (!layout) return;
        layout = {
            ...layout,
            rows: layout.rows.map(row => ({
                panels: row.panels.map(p => {
                    if (p.panel_id !== panelId) return p;
                    return {
                        ...p,
                        inference_result: {
                            ...p.inference_result,
                            panel_height_px: px ?? p.inference_result.panel_height_px,
                        },
                    };
                }),
            })),
        };
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
     * control that renders a rich widget, so the FilterBar can show a real
     * dropdown / multiselect / slider. Best-effort: failures leave the entry
     * absent and the control falls back to a text/number input.
     *
     * Domains are computed from the panel SQL with its parametric WHERE
     * stripped, so they do not depend on the current filter selection and
     * only need to be loaded once per execution.
     */
    async function loadFilterDomains() {
        const domains: Record<string, FilterDomain> = {};
        await Promise.all(
            executedResults.flatMap((r, i) =>
                r.inference_result.filter_controls.map(async (fc) => {
                    const kind =
                        fc.control_type === 'dropdown' || fc.control_type === 'multiselect'
                            ? 'distinct'
                            : fc.control_type === 'range_slider'
                                ? 'range'
                                : null;
                    if (kind === null || domains[fc.variable]) return;

                    try {
                        const dom = await apiPost<FilterDomain>(
                            `/api/v1/panels/${panelIds[i]}/filter-domain`,
                            { column: fc.column_name, kind },
                        );
                        domains[fc.variable] = dom;
                    } catch {
                        // leave absent → control falls back to text/number input
                    }
                })
            )
        );
        filterDomains = domains;
    }

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

            if (!panelVars.includes(changedVar)) continue;

            // Send every variable, including empty ones. An empty value means
            // "All": the backend neutralizes that predicate and returns all
            // rows for the dimension. Skipping empties here is what previously
            // made the dropdown's "All" option render nothing.
            const variables = Object.fromEntries(
                panelVars.map(v => [v, currentFV[v] ?? '']),
            );
            const panelId = panelIds[i];

            try {
                const exec = await apiPost<{
                    inference_result: InferenceResult;
                    data: Record<string, unknown>[];
                }>(`/api/v1/panels/${panelId}/execute`, { variables });
                updatedResults[i] = { panel_id: panelId, ...exec };
                anyChanged = true;
            } catch {
                // Keep existing result
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

        clearTimeout(filterDebounceTimer);
        filterDebounceTimer = window.setTimeout(() => {
            const currentFV = { ...get(filterValues), [varName]: value };
            executeFilteredPanels(varName, currentFV);
        }, 350);
    }

    return {
        get dashboardId() { return dashboardId; },
        get allDashboards() { return allDashboards; },
        get folders() { return folders; },
        get dashboardsLoading() { return dashboardsLoading; },
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
        handleFilterChange,
        openPanelProperties,
        closePanelProperties,
        handleTitleOverride,
        handleAxisOverride,
        handleColorOverride,
        handlePanelSqlChange,
    };
}

export const dashboardStore = createDashboardStore();
