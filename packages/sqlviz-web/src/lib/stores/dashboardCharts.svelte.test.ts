import { beforeEach, expect, it, vi } from 'vitest';
import { apiGet, apiPatch, apiPost, recompose, type ExecResult } from '$lib/api';
import type { DashboardLayout, InferenceResult } from '$lib/types';
import { dashboardCache } from './dashboardCache.svelte';
import { createDashboardStore } from './dashboardStore.svelte';
import { filterValues } from './filterValues.svelte';

vi.mock('$lib/api', () => ({ apiGet: vi.fn(), apiPatch: vi.fn(), apiPost: vi.fn(), apiDelete: vi.fn(), recompose: vi.fn() }));
vi.mock('$app/environment', () => ({ browser: false }));

beforeEach(() => {
    vi.resetAllMocks(); dashboardCache.clear(); filterValues.replace({});
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ json: async () => [] }));
    vi.mocked(apiGet).mockResolvedValue({ sql_content: 'SELECT 1', last_run_at: null });
    vi.mocked(recompose).mockImplementation(async (results: ExecResult[]) => ({ rows: [{ panels: results.map(r => ({ ...r, final_col_span: 6, col_offset: 0, row_index: 0 })) }] }));
});

async function loaded() {
    const results: ExecResult[] = [{ panel_id: 'p', data: [{ amount: 7 }], inference_result: {
        chart_winner: 'bar', chart_user_override: null, filter_controls: [], visual_spec: { chart_type: 'bar' },
    } as unknown as InferenceResult }];
    dashboardCache.set('d', { sql: 'SELECT 1', panelIds: ['p'], panelSQLs: ['SELECT 1'], executedResults: results,
        layout: { rows: [{ panels: [{ ...results[0], final_col_span: 6, col_offset: 0, row_index: 0 }] }] }, filterDomains: {}, filterValues: {},
    });
    const store = createDashboardStore(); await store.loadDashboard('d'); return store;
}

function execution(store: ReturnType<typeof createDashboardStore>) {
    return { data: [{ amount: 9 }], inference_result: { ...store.executedResults[0].inference_result,
        chart_winner: 'line', chart_user_override: 'line', visual_spec: { chart_type: 'line' },
    } };
}

it('publishes the confirmed execution and layout together, with current filters', async () => {
    const store = await loaded();
    filterValues.replace({ region: 'North' });
    vi.mocked(apiPatch).mockResolvedValueOnce({ chart_user_override: 'line' });
    vi.mocked(apiPost).mockResolvedValueOnce(execution(store));
    let finish!: (value: DashboardLayout) => void;
    vi.mocked(recompose).mockImplementationOnce(() => new Promise(r => { finish = r; }));
    const before = store.layout;
    const save = store.handleChartOverride('p', 'line');
    await vi.waitFor(() => expect(recompose).toHaveBeenCalledTimes(1));
    expect(store.layout).toEqual(before);
    expect(store.executedResults[0].inference_result.chart_winner).toBe('bar');
    const next = vi.mocked(recompose).mock.calls[0][0];
    finish({ rows: [{ panels: [{ ...next[0], final_col_span: 6, col_offset: 0, row_index: 0 }] }] });
    expect(await save).toEqual({ saved: true, error: null });
    expect(apiPost).toHaveBeenCalledWith('/api/v1/panels/p/execute', { variables: { region: 'North' } });
    expect(store.layout?.rows[0].panels[0].inference_result.chart_winner).toBe('line');
    expect(store.executedResults[0].data).toEqual([{ amount: 9 }]);
});

it('rejecting a save preserves all chart data and allows a later retry', async () => {
    const store = await loaded(); const before = store.layout;
    vi.mocked(apiPatch).mockRejectedValueOnce(new Error('Conflict'));
    expect(await store.handleChartOverride('p', 'line')).toMatchObject({ saved: false, error: expect.stringContaining('Conflict') });
    expect(store.layout).toEqual(before); expect(apiPost).not.toHaveBeenCalled();
    vi.mocked(apiPatch).mockResolvedValueOnce({});
    vi.mocked(apiPost).mockResolvedValueOnce(execution(store));
    expect(await store.handleChartOverride('p', 'line')).toEqual({ saved: true, error: null });
});

it.each(['execute', 'compose'])('preserves the old view when %s fails after save; retry does not teach again', async (stage) => {
    const store = await loaded(); const before = store.layout;
    vi.mocked(apiPatch).mockResolvedValueOnce({});
    if (stage === 'execute') vi.mocked(apiPost).mockRejectedValueOnce(new Error('timeout'));
    else { vi.mocked(apiPost).mockResolvedValueOnce(execution(store)); vi.mocked(recompose).mockRejectedValueOnce(new Error('unavailable')); }
    expect(await store.handleChartOverride('p', 'line')).toMatchObject({ saved: true, error: expect.stringContaining('saved') });
    expect(store.layout).toEqual(before);
    expect(store.executedResults[0].inference_result.chart_winner).toBe('bar');
    vi.mocked(apiPost).mockResolvedValueOnce(execution(store));
    expect(await store.handleChartOverride('p', 'line', true)).toEqual({ saved: true, error: null });
    expect(apiPatch).toHaveBeenCalledTimes(1);
});

it('reset sends explicit null, rather than pinning the engine winner', async () => {
    const store = await loaded(); vi.mocked(apiPatch).mockResolvedValueOnce({});
    vi.mocked(apiPost).mockResolvedValueOnce({ ...execution(store), inference_result: { ...execution(store).inference_result, chart_user_override: null } });
    await store.handleChartOverride('p', null);
    expect(apiPatch).toHaveBeenCalledWith('/api/v1/panels/p/override', { field_name: 'chart_type', user_value: null });
    expect(store.executedResults[0].inference_result.chart_user_override).toBeNull();
});

it('a late refresh cannot replace the next dashboard and invalidates the old cache', async () => {
    const store = await loaded(); const response = execution(store);
    let finish!: (value: unknown) => void;
    vi.mocked(apiPatch).mockResolvedValueOnce({});
    vi.mocked(apiPost).mockImplementationOnce(() => new Promise(r => { finish = r; }));
    const save = store.handleChartOverride('p', 'line');
    await vi.waitFor(() => expect(apiPost).toHaveBeenCalledTimes(1));
    await store.loadDashboard('other');
    finish(response); await save;
    expect(store.dashboardId).toBe('other'); expect(store.layout).toBeNull();
    expect(dashboardCache.get('d')).toBeUndefined(); expect(recompose).not.toHaveBeenCalled();
});

it('serializes chart writes so a reset cannot finish before an earlier choice', async () => {
    const store = await loaded();
    let finish!: (value: unknown) => void;
    vi.mocked(apiPatch).mockImplementationOnce(() => new Promise(r => { finish = r; })).mockResolvedValueOnce({});
    vi.mocked(apiPost).mockResolvedValue(execution(store));
    const first = store.handleChartOverride('p', 'line'), second = store.handleChartOverride('p', null);
    await Promise.resolve(); expect(apiPatch).toHaveBeenCalledTimes(1);
    finish({}); await Promise.all([first, second]);
    expect(apiPatch).toHaveBeenNthCalledWith(2, '/api/v1/panels/p/override', { field_name: 'chart_type', user_value: null });
});

it('a concurrent confirmed edit is not overwritten by an older chart refresh', async () => {
    const store = await loaded(); const response = execution(store);
    let finish!: (value: unknown) => void;
    vi.mocked(apiPatch).mockResolvedValueOnce({}).mockResolvedValueOnce({ field: 'title', value: 'New title' });
    vi.mocked(apiPost).mockImplementationOnce(() => new Promise(r => { finish = r; }));
    const save = store.handleChartOverride('p', 'line');
    await vi.waitFor(() => expect(apiPost).toHaveBeenCalledTimes(1));
    await store.setViewOverride('p', 'title', 'New title');
    finish(response);
    expect(await save).toMatchObject({ saved: true, error: expect.stringContaining('view changed') });
    expect(store.layout?.rows[0].panels[0].inference_result.title).toBe('New title');
    expect(store.executedResults[0].inference_result.chart_winner).toBe('bar');
});
