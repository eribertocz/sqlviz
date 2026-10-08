import { beforeEach, expect, it, vi } from 'vitest';
import { apiGet, apiPatch, apiPost, recompose, type ExecResult } from '$lib/api';
import type { DashboardInfo, DashboardLayout, InferenceResult } from '$lib/types';
import { dashboardCache } from './dashboardCache.svelte';
import { createDashboardStore } from './dashboardStore.svelte';
import { filterValues } from './filterValues.svelte';

vi.mock('$lib/api', () => ({
    apiGet: vi.fn(), apiPatch: vi.fn(), apiPost: vi.fn(), apiDelete: vi.fn(), recompose: vi.fn(),
}));
vi.mock('$app/environment', () => ({ browser: false }));

beforeEach(() => {
    vi.resetAllMocks();
    dashboardCache.clear();
    filterValues.replace({});
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ json: async () => [] }));
    vi.mocked(apiGet).mockResolvedValue({ sql_content: 'SELECT 1', last_run_at: null } as DashboardInfo);
    vi.mocked(recompose).mockImplementation(async (results: ExecResult[]) => ({
        rows: [{ panels: results.map(r => ({ ...r, final_col_span: 6, col_offset: 0, row_index: 0 })) }],
    }));
});

async function loadedStore() {
    const inference = { title: 'Confirmed', col_span: 6, panel_height_px: 300, filter_controls: [],
        visual_spec: { chart_type: 'bar', x_label: 'Year', y_label: 'Revenue' },
    } as unknown as InferenceResult;
    const results: ExecResult[] = [{ panel_id: 'p', data: [{ amount: 7 }], inference_result: inference }];
    const layout: DashboardLayout = { rows: [{ panels: [{
        ...results[0], final_col_span: 6, col_offset: 0, row_index: 0,
    }] }] };
    dashboardCache.set('d', { sql: 'SELECT 1', panelIds: ['p'], panelSQLs: ['SELECT 1'],
        executedResults: results, layout, filterDomains: {}, filterValues: {},
    });
    const store = createDashboardStore();
    await store.loadDashboard('d');
    return store;
}

it('changes title only after confirmation and preserves exact text in both result stores', async () => {
    const store = await loadedStore();
    let resolve!: (value: unknown) => void;
    vi.mocked(apiPatch).mockImplementationOnce(() => new Promise(r => { resolve = r; }));
    const save = store.setViewOverride('p', 'title', '  Nueva · ñ  ');
    await Promise.resolve();
    expect(store.layout?.rows[0].panels[0].inference_result.title).toBe('Confirmed');
    resolve({ field: 'title', value: '  Nueva · ñ  ' });
    expect(await save).toBeNull();
    expect(apiPatch).toHaveBeenCalledWith('/api/v1/panels/p/view-override', {
        field: 'title', value: '  Nueva · ñ  ',
    });
    expect(store.layout?.rows[0].panels[0].inference_result.title).toBe('  Nueva · ñ  ');
    expect(store.executedResults[0].inference_result.title).toBe('  Nueva · ñ  ');
    expect(store.layout?.rows[0].panels[0].data).toEqual([{ amount: 7 }]);
    expect(apiPost).not.toHaveBeenCalled();
});

it('a rejected save preserves the chart and returns an error for the draft input', async () => {
    const store = await loadedStore();
    const before = store.layout;
    vi.mocked(apiPatch).mockRejectedValueOnce(new Error('Panel changed concurrently.'));
    expect(await store.setViewOverride('p', 'title', 'Rejected')).toContain('Panel changed concurrently');
    expect(store.layout).toEqual(before);
    expect(store.executedResults[0].inference_result.title).toBe('Confirmed');
});

it('serializes writes and continues after a rejected save', async () => {
    const store = await loadedStore();
    let reject!: (error: Error) => void;
    vi.mocked(apiPatch).mockImplementationOnce(() => new Promise((_, r) => { reject = r; }));
    vi.mocked(apiPatch).mockResolvedValueOnce({ field: 'x_label', value: 'Period' });
    const first = store.setViewOverride('p', 'title', 'First');
    const second = store.setViewOverride('p', 'x_label', 'Period');
    await Promise.resolve();
    expect(apiPatch).toHaveBeenCalledTimes(1);
    reject(new Error('failed'));
    await Promise.all([first, second]);
    expect(store.executedResults[0].inference_result.visual_spec?.x_label).toBe('Period');
    expect(store.layout?.rows[0].panels[0].inference_result.visual_spec?.x_label).toBe('Period');
});

it('clearing an axis label uses the confirmed null without executing SQL', async () => {
    const store = await loadedStore();
    vi.mocked(apiPatch).mockResolvedValueOnce({ field: 'y_label', value: null });
    expect(await store.setViewOverride('p', 'y_label', '')).toBeNull();
    expect(store.executedResults[0].inference_result.visual_spec?.y_label).toBeNull();
    expect(apiPost).not.toHaveBeenCalled();
});

it('resetting the title retrieves the engine title while preserving current filters', async () => {
    const store = await loadedStore();
    filterValues.replace({ region: 'North' });
    vi.mocked(apiPatch).mockResolvedValueOnce({ field: 'title', value: null });
    vi.mocked(apiPost).mockResolvedValueOnce({ data: [{ amount: 7 }], inference_result: {
        ...store.executedResults[0].inference_result, title: 'Automatic',
    } });
    expect(await store.setViewOverride('p', 'title', '')).toBeNull();
    expect(apiPost).toHaveBeenCalledWith('/api/v1/panels/p/execute', { variables: { region: 'North' } });
    expect(store.executedResults[0].inference_result.title).toBe('Automatic');
    expect(store.layout?.rows[0].panels[0].inference_result.title).toBe('Automatic');
});

it('explains a saved reset whose refresh fails and keeps the previous chart', async () => {
    const store = await loadedStore();
    const before = store.layout;
    vi.mocked(apiPatch).mockResolvedValueOnce({ field: 'title', value: null });
    vi.mocked(apiPost).mockRejectedValueOnce(new Error('unavailable'));
    expect(await store.setViewOverride('p', 'title', '')).toContain('Title reset saved');
    expect(store.layout).toEqual(before);
});

it('a late save invalidates the old cache without replacing another dashboard', async () => {
    const store = await loadedStore();
    let resolve!: (value: unknown) => void;
    vi.mocked(apiPatch).mockImplementationOnce(() => new Promise(r => { resolve = r; }));
    const save = store.setViewOverride('p', 'title', 'New');
    await Promise.resolve();
    await store.loadDashboard('other');
    resolve({ field: 'title', value: 'New' });
    await save;
    expect(store.dashboardId).toBe('other');
    expect(store.layout).toBeNull();
    expect(dashboardCache.has('d')).toBe(false);
});
