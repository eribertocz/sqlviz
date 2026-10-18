import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { apiGet, apiPatch, apiPost } from '$lib/api';
import { legacySqlSnapshot } from '$lib/sql/sqlSnapshot.testFixtures';
import { createDashboardStore } from './dashboardStore.svelte';
import { dashboardCache } from './dashboardCache.svelte';
import { editorRef } from './editorRef';
import { executionStore } from './executionStore.svelte';
import { filterValues } from './filterValues.svelte';
import { uiStore } from './uiStore.svelte';

vi.mock('$lib/api', () => ({ apiGet: vi.fn(), apiPatch: vi.fn(), apiPost: vi.fn(), apiDelete: vi.fn(), recompose: vi.fn() }));
vi.mock('$app/environment', () => ({ browser: false }));

beforeEach(() => {
    vi.resetAllMocks(); vi.useFakeTimers(); dashboardCache.clear(); filterValues.reset();
    executionStore.executing = false; executionStore.errorMsg = null; executionStore.saveStatus = 'idle';
    editorRef.set({}); vi.stubGlobal('fetch', vi.fn());
    vi.spyOn(uiStore, 'showToast').mockImplementation(() => {});
    vi.mocked(apiPatch).mockResolvedValue({});
    vi.mocked(apiGet).mockImplementation(async path => path.endsWith('/sql-script')
        ? legacySqlSnapshot(path.split('/').at(-2)!, [{ id: 'p', sql_content: 'SELECT 1' }], 'SELECT 1') : []);
});
afterEach(() => { vi.clearAllTimers(); vi.useRealTimers(); vi.restoreAllMocks(); vi.unstubAllGlobals(); editorRef.set({}); });

function pending() {
    let resolve!: (value: unknown) => void;
    const promise = new Promise<unknown>(r => resolve = r);
    return { resolve, promise };
}

it('uses only the snapshot for definitions and does not query the panel or dashboard endpoints', async () => {
    const store = createDashboardStore(); await store.loadDashboard('d');
    expect(apiGet).toHaveBeenCalledExactlyOnceWith('/api/v1/dashboards/d/sql-script');
    expect(fetch).not.toHaveBeenCalled(); expect(apiPost).not.toHaveBeenCalled(); expect(apiPatch).not.toHaveBeenCalled();
    expect(store.sql).toBe('SELECT 1'); expect(store.panelIds).toEqual(['p']);
});

it('a late dashboard response cannot overwrite a newer navigation', async () => {
    const delayed = pending(); const regular = vi.mocked(apiGet).getMockImplementation()!;
    vi.mocked(apiGet).mockImplementation(path => path.includes('/a/') ? delayed.promise : regular(path));
    const store = createDashboardStore(); const load = store.loadDashboard('a');
    expect(store.viewLoading).toBe(true); await store.loadDashboard('b');
    delayed.resolve(legacySqlSnapshot('a', [], 'SELECT old')); await load;
    expect(store.dashboardId).toBe('b'); expect(store.sql).toBe('SELECT 1'); expect(store.viewLoading).toBe(false);
});

it('a draft edited while navigation is pending is preserved instead of replaced', async () => {
    const delayed = pending(); vi.mocked(apiGet).mockReturnValue(delayed.promise);
    const store = createDashboardStore(); const load = store.loadDashboard('d');
    store.sql = 'SELECT local_draft'; delayed.resolve(legacySqlSnapshot('d', [], 'SELECT persisted')); await load;
    expect(store.sql).toBe('SELECT local_draft'); expect(store.dashboardId).toBeNull();
    expect(store.viewLoading).toBe(false); expect(uiStore.showToast).toHaveBeenCalledWith(expect.stringContaining('draft was preserved'));
});

it('a failed snapshot cannot replace the active definition or use legacy fetching as fallback', async () => {
    const store = createDashboardStore(); await store.loadDashboard('a');
    vi.mocked(apiGet).mockRejectedValueOnce(new Error('Snapshot unavailable'));
    await store.loadDashboard('b');
    expect(store.dashboardId).toBe('a'); expect(store.panelIds).toEqual(['p']); expect(store.sql).toBe('SELECT 1');
    expect(fetch).not.toHaveBeenCalled(); expect(uiStore.showToast).toHaveBeenCalledWith('Snapshot unavailable');
});

it('cached deleted IDs cannot supply definitions or results during navigation', async () => {
    dashboardCache.set('d', { sql: 'SELECT 1', panelIds: ['deleted'], panelSQLs: ['SELECT 1'],
        executedResults: [], layout: { rows: [] }, filterDomains: {}, filterValues: { old: true } });
    const store = createDashboardStore(); await store.loadDashboard('d');
    expect(store.panelIds).toEqual(['p']); expect(store.layout).toBeNull(); expect(filterValues.current).toEqual({});
    expect(dashboardCache.has('d')).toBe(false);
});

it('bootstrap cannot replace a dashboard created while its explorer request is pending', async () => {
    const delayed = pending(); const regular = vi.mocked(apiGet).getMockImplementation()!;
    let firstList = true;
    vi.mocked(apiGet).mockImplementation(path => {
        if (path === '/api/v1/dashboards' && firstList) { firstList = false; return delayed.promise; }
        return regular(path);
    });
    vi.mocked(apiPost).mockResolvedValue({ id: 'new', name: 'New' });
    const store = createDashboardStore(); const boot = store.bootstrap(); await store.createDashboard('New');
    delayed.resolve([{ id: 'old' }]); await boot;
    expect(store.dashboardId).toBe('new'); expect(store.sql).toBe(''); expect(store.panelIds).toEqual([]);
    expect(vi.mocked(apiGet).mock.calls.some(([path]) => path.includes('/old/'))).toBe(false);
});

it('Run waits for pending navigation rather than executing the previous dashboard', async () => {
    const delayed = pending(); vi.mocked(apiGet).mockReturnValue(delayed.promise);
    const store = createDashboardStore(); const load = store.loadDashboard('d'); await store.run();
    expect(apiPost).not.toHaveBeenCalled();
    delayed.resolve(legacySqlSnapshot('d')); await load;
});
