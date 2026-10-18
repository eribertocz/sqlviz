import { legacySqlSnapshot } from '$lib/sql/sqlSnapshot.testFixtures';
import { beforeEach, expect, it, vi } from 'vitest';
import { apiGet, apiPatch, recompose, type ExecResult } from '$lib/api';
import type { DashboardLayout, InferenceResult } from '$lib/types';
import { dashboardCache } from './dashboardCache.svelte';
import { createDashboardStore } from './dashboardStore.svelte';
import { uiStore } from './uiStore.svelte';

vi.mock('$lib/api', () => ({
    apiGet: vi.fn(), apiPatch: vi.fn(), apiPost: vi.fn(), apiDelete: vi.fn(), recompose: vi.fn(),
}));
vi.mock('./uiStore.svelte', () => ({ uiStore: { showToast: vi.fn() } }));
// Exercise commands independently from the singleton's browser subscriptions.
vi.mock('$app/environment', () => ({ browser: false }));

beforeEach(() => {
    vi.clearAllMocks();
    dashboardCache.clear();
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ json: async () => [] }));
    vi.mocked(apiGet).mockImplementation(async path => {
        const id = path.split('/').at(-2)!;
        return legacySqlSnapshot(id, id === 'd' ? [{ id: 'p', sql_content: 'SELECT 1' }] : [], id === 'd' ? 'SELECT 1' : '');
    });
    vi.mocked(recompose).mockImplementation(async (results: ExecResult[]) => ({
        rows: [{ panels: results.map(r => ({
            ...r, final_col_span: r.inference_result.col_span, col_offset: 0, row_index: 0,
        })) }],
    }));
});

async function loadedStore() {
    const inference = { col_span: 12, panel_height_px: 360, filter_controls: [] } as unknown as InferenceResult;
    const results = [{ panel_id: 'p', data: [{ total: 3 }], inference_result: inference }];
    const layout: DashboardLayout = { rows: [{ panels: [{
        ...results[0], final_col_span: 12, col_offset: 0, row_index: 0,
    }] }] };
    dashboardCache.set('d', {
        sql: 'SELECT 1', panelIds: ['p'], panelSQLs: ['SELECT 1'],
        executedResults: results, layout, filterDomains: {}, filterValues: {},
    });
    const store = createDashboardStore();
    await store.loadDashboard('d');
    return store;
}

it('keeps the chart and size unchanged when saving is rejected', async () => {
    const store = await loadedStore();
    vi.mocked(apiPatch).mockRejectedValueOnce(new Error('409 conflict'));
    await store.handleWidthOverride('p', 6);
    expect(store.layout?.rows[0].panels[0].final_col_span).toBe(12);
    expect(store.executedResults[0].inference_result.col_span).toBe(12);
    expect(store.layout?.rows[0].panels[0].data).toEqual([{ total: 3 }]);
    expect(recompose).not.toHaveBeenCalled();
    expect(uiStore.showToast).toHaveBeenCalledWith('409 conflict');
});

it('waits for persistence before showing the new dimensions', async () => {
    const store = await loadedStore();
    let resolve!: (value: unknown) => void;
    vi.mocked(apiPatch).mockImplementationOnce(() => new Promise(r => { resolve = r; }));
    const save = store.handleHeightOverride('p', 480);
    await Promise.resolve();
    expect(store.layout?.rows[0].panels[0].inference_result.panel_height_px).toBe(360);
    resolve({ selected_height_px: 480 });
    await save;
    expect(store.layout?.rows[0].panels[0].inference_result.panel_height_px).toBe(480);
});

it('serializes rapid saves and continues after a rejected save', async () => {
    const store = await loadedStore();
    let reject!: (error: Error) => void;
    vi.mocked(apiPatch).mockImplementationOnce(() => new Promise((_, r) => { reject = r; }));
    vi.mocked(apiPatch).mockResolvedValueOnce({ selected_col_span: 8 });
    const first = store.handleWidthOverride('p', 6);
    const second = store.handleWidthOverride('p', 8);
    await Promise.resolve();
    expect(apiPatch).toHaveBeenCalledTimes(1);
    reject(new Error('failed'));
    await Promise.all([first, second]);
    expect(store.layout?.rows[0].panels[0].final_col_span).toBe(8);
    expect(store.executedResults[0].inference_result.col_span).toBe(8);
});

it('reset uses the confirmed inferred value and repacks the layout', async () => {
    const store = await loadedStore();
    vi.mocked(apiPatch).mockResolvedValueOnce({ selected_col_span: 4 });
    await store.handleWidthOverride('p', null);
    expect(apiPatch).toHaveBeenCalledWith('/api/v1/panels/p/override', {
        field_name: 'col_span', user_value: null,
    });
    expect(store.layout?.rows[0].panels[0].final_col_span).toBe(4);
});

it('a completed save cannot replace the dashboard navigated to meanwhile', async () => {
    const store = await loadedStore();
    let resolve!: (value: unknown) => void;
    vi.mocked(apiPatch).mockImplementationOnce(() => new Promise(r => { resolve = r; }));
    const save = store.handleWidthOverride('p', 6);
    await Promise.resolve();
    await store.loadDashboard('other');
    resolve({ selected_col_span: 6 });
    await save;
    expect(store.dashboardId).toBe('other');
    expect(store.layout).toBeNull();
    expect(recompose).not.toHaveBeenCalled();
    expect(dashboardCache.has('d')).toBe(false);
});

it('keeps the confirmed size and explains a failure to recompose', async () => {
    const store = await loadedStore();
    vi.mocked(apiPatch).mockResolvedValueOnce({ selected_col_span: 6 });
    vi.mocked(recompose).mockRejectedValueOnce(new Error('compose unavailable'));
    await store.handleWidthOverride('p', 6);
    expect(store.layout?.rows[0].panels[0].final_col_span).toBe(6);
    expect(uiStore.showToast).toHaveBeenCalledWith(expect.stringContaining('Size saved'));
});
