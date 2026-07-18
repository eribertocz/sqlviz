import { get } from 'svelte/store';
import { apiPatch, apiPost, recompose, type ExecResult } from '$lib/api';
import type { DashboardInfo, DashboardLayout, FilterControl, InferenceResult } from '$lib/types';
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
    let panelIds         = $state<string[]>([]);
    let panelSQLs        = $state<string[]>([]);
    let executedResults  = $state<ExecResult[]>([]);
    let layout           = $state<DashboardLayout | null>(null);
    let sql               = $state('');

    let filterDebounceTimer = 0;

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

    /** Splits editor SQL into individual statements — one statement becomes one panel. */
    function splitStatements(text: string): string[] {
        return text.split(';').map(s => s.trim()).filter(s => s.length > 0);
    }

    const statementCount = $derived(splitStatements(sql).length);

    /** Loads the first existing dashboard (or bootstraps the demo query). Called once on mount. */
    async function bootstrap(isDemo: boolean) {
        try {
            const dashboards = await fetch('/api/v1/dashboards')
                .then(r => r.json()) as DashboardInfo[];
            allDashboards = dashboards;
            if (dashboards.length === 0) {
                if (isDemo) {
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

    /** Create a new dashboard, then switch to it (empty — no query carried over). */
    async function createDashboard() {
        const name = uiStore.newDashboardName.trim() || 'New Dashboard';
        uiStore.creatingDashboard = false;
        uiStore.newDashboardName  = '';
        try {
            const dash = await apiPost<{ id: string; name: string }>('/api/v1/dashboards', {
                name,
                sort_order: allDashboards.length,
            });
            allDashboards = await fetch('/api/v1/dashboards')
                .then(r => r.json()) as DashboardInfo[];
            // Switch to the empty new dashboard without running anything.
            dashboardId     = dash.id;
            panelIds        = [];
            panelSQLs       = [];
            sql             = '';
            executedResults = [];
            layout          = null;
        } catch (e: unknown) {
            uiStore.showToast(e instanceof Error ? e.message : 'Could not create dashboard.');
        }
    }

    /** Switch to a different dashboard: load its panels and re-execute. */
    async function loadDashboard(id: string) {
        if (id === dashboardId || executionStore.executing) return;

        try {
            const panels = await fetch(`/api/v1/panels?dashboard_id=${id}`)
                .then(r => r.json()) as Array<{ id: string; sql_content: string; sort_order: number }>;
            panels.sort((a, b) => a.sort_order - b.sort_order);

            dashboardId = id;
            panelIds    = panels.map(p => p.id);
            panelSQLs   = panels.map(p => p.sql_content);
            sql         = panelSQLs.join(';\n\n');
            executedResults = [];
            layout      = null;

            if (panels.length > 0) run();
        } catch (e: unknown) {
            uiStore.showToast(e instanceof Error ? e.message : 'Could not load dashboard.');
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
        get panelIds() { return panelIds; },
        get panelSQLs() { return panelSQLs; },
        get executedResults() { return executedResults; },
        get layout() { return layout; },
        get sql() { return sql; },
        set sql(v: string) { sql = v; },

        get hasLayout() { return hasLayout; },
        get activeDashboard() { return activeDashboard; },
        get utilityPct() { return utilityPct; },
        get allFilterControls() { return allFilterControls; },
        get hasFilters() { return hasFilters; },
        get statementCount() { return statementCount; },

        bootstrap,
        run,
        handleDelete,
        handleEditSQL,
        handleExplain,
        createDashboard,
        loadDashboard,
        handleChartOverride,
        handleWidthOverride,
        handleHeightOverride,
        handleFilterChange,
    };
}

export const dashboardStore = createDashboardStore();
