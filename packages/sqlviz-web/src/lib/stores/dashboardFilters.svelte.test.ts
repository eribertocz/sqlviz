import { legacySqlSnapshot } from '$lib/sql/sqlSnapshot.testFixtures';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { apiGet, apiPost, type ExecResult } from '$lib/api';
import { createDashboardStore } from './dashboardStore.svelte';
import { dashboardCache } from './dashboardCache.svelte';
import { filterValues } from './filterValues.svelte';
import type { InferenceResult } from '$lib/types';

vi.mock('$lib/api', () => ({ apiGet: vi.fn(), apiPost: vi.fn(), apiPatch: vi.fn(), apiDelete: vi.fn(), recompose: vi.fn() }));
vi.mock('$app/environment', () => ({ browser: false }));
beforeEach(() => {
    vi.clearAllMocks(); dashboardCache.clear(); filterValues.reset();
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ json: async () => [] }));
    vi.mocked(apiGet).mockImplementation(async path => {
        const id = path.split('/').at(-2)!;
        return legacySqlSnapshot(id, id === 'filters-dashboard' ? [
            { id: 'a', sql_content: 'SELECT 1' }, { id: 'b', sql_content: 'SELECT 2' },
        ] : []);
    });
});
afterEach(() => vi.unstubAllGlobals());

async function reader() {
    const results: ExecResult[] = ['a', 'b'].map(variable => ({ panel_id: variable, data: [{ total: 100 }],
        inference_result: { col_span: 6, row_span: 1, panel_height_px: 360, filter_controls: [{ variable, label: variable,
            column_name: variable, column_type: 'INTEGER', control_type: 'numeric', scope: 'global' }] } as InferenceResult }));
    dashboardCache.set('filters-dashboard', { sql: 'SELECT 1\n;\n\nSELECT 2', panelIds: ['a', 'b'], panelSQLs: ['SELECT 1', 'SELECT 2'],
        executedResults: results, layout: { rows: [{ panels: results.map(r => ({ ...r, final_col_span: 6, col_offset: 0, row_index: 0 })) }] },
        filterDomains: {}, filterValues: {} });
    const store = createDashboardStore(); await store.loadDashboard('filters-dashboard'); return store;
}

it('publishes author Preview filters and data together after all responses', async () => {
    const store = await reader(); let finish!: (value: unknown) => void;
    vi.mocked(apiPost).mockResolvedValueOnce({ ...store.executedResults[0], data: [{ total: 10 }] })
        .mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
    const operation = store.applyFilters({ a: 10, b: 0 });
    await vi.waitFor(() => expect(apiPost).toHaveBeenCalledTimes(2));
    expect(filterValues.current).toEqual({}); expect(store.layout?.rows[0].panels[0].data).toEqual([{ total: 100 }]);
    finish({ ...store.executedResults[1], data: [] }); expect(await operation).toBe(true);
    expect(filterValues.current).toEqual({ a: 10, b: 0 });
    expect(store.layout?.rows[0].panels[0].data).toEqual([{ total: 10 }]);
    expect(store.layout?.rows[0].panels[1].data).toEqual([]);
});
it('preserves Preview context and every chart when the second source fails', async () => {
    const store = await reader();
    vi.mocked(apiPost).mockResolvedValueOnce({ ...store.executedResults[0], data: [] }).mockRejectedValueOnce(new Error('Timeout'));
    expect(await store.applyFilters({ a: 1, b: 2 })).toBe(false);
    expect(filterValues.current).toEqual({}); expect(store.layout?.rows[0].panels[0].data).toEqual([{ total: 100 }]);
    expect(store.filterError).toBe('Timeout'); expect(store.filterBusy).toBe(false);
});
it('cannot restore old filter data after navigating in Preview', async () => {
    const store = await reader(); let finish!: (value: unknown) => void;
    vi.mocked(apiPost).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
    const operation = store.applyFilters({ a: 1 });
    await store.loadDashboard('another-dashboard');
    finish({ inference_result: {} as InferenceResult, data: [{ total: 999 }] });
    expect(await operation).toBe(false); expect(store.executedResults).toEqual([]); expect(filterValues.current).toEqual({});
});
