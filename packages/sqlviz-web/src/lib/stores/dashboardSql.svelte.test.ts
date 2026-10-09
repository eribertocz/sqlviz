import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { apiGet, apiPatch, apiPost, recompose } from '$lib/api';
import type { InferenceResult } from '$lib/types';
import { createDashboardStore } from './dashboardStore.svelte';
import { dashboardCache } from './dashboardCache.svelte';
import { editorRef } from './editorRef';
import { executionStore } from './executionStore.svelte';
import { filterValues } from './filterValues.svelte';

vi.mock('$lib/api', () => ({ apiGet: vi.fn(), apiPost: vi.fn(), apiPatch: vi.fn(), apiDelete: vi.fn(), recompose: vi.fn() }));
vi.mock('$app/environment', () => ({ browser: false }));

const result = { inference_result: { filter_controls: [] } as unknown as InferenceResult, data: [{ total: 1 }] };
const first = "SELECT 'a;b'"; const second = 'SELECT 2 -- tail;';
const source = `${first};\n${second}`;
const parsed = { version: 1, dialect: 'duckdb', statements: [
    { sql: first, start_offset: 0, end_offset: first.length },
    { sql: second, start_offset: first.length + 2, end_offset: source.length },
] };

beforeEach(() => {
    vi.clearAllMocks(); vi.useFakeTimers(); dashboardCache.clear(); filterValues.reset();
    executionStore.executing = false; executionStore.errorMsg = null; executionStore.statusMsg = null;
    editorRef.set({});
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ json: async () => [] }));
    vi.mocked(apiPatch).mockResolvedValue({});
    vi.mocked(apiGet).mockImplementation(async path =>
        path === '/api/v1/dashboards' || path === '/api/v1/folders' ? [] : { sql_content: '', last_run_at: null });
    vi.mocked(recompose).mockResolvedValue({ rows: [] });
});
afterEach(() => { vi.clearAllTimers(); vi.useRealTimers(); vi.unstubAllGlobals(); editorRef.set({}); });

function deferred() {
    let resolve!: (value: unknown) => void;
    let reject!: (error: Error) => void;
    const promise = new Promise<unknown>((r, j) => { resolve = r; reject = j; });
    return { promise, resolve, reject };
}

function transport() {
    let panels = 0;
    vi.mocked(apiPost).mockImplementation(async path => {
        if (path === '/api/v1/sql/parse') return parsed;
        if (path === '/api/v1/dashboards') return { id: 'd' };
        if (path === '/api/v1/panels') return { id: `p${++panels}` };
        if (path.endsWith('/execute')) return result;
        throw new Error(`Unexpected request: ${path}`);
    });
}

it('uses native slices for panel SQL, count and exact last-run source', async () => {
    transport(); const store = createDashboardStore(); store.sql = source;
    expect(store.statementCount).toBe(0); expect(store.sqlCheckReady).toBe(false);
    await store.run();
    expect(apiPost).toHaveBeenNthCalledWith(1, '/api/v1/sql/parse', { sql: source });
    expect(apiPost).toHaveBeenCalledWith('/api/v1/panels', expect.objectContaining({ sql_content: first }));
    expect(apiPost).toHaveBeenCalledWith('/api/v1/panels', expect.objectContaining({ sql_content: second }));
    expect(store.statementCount).toBe(2); expect(store.panelSQLs).toEqual([first, second]);
    expect(apiPatch).toHaveBeenCalledWith('/api/v1/dashboards/d', expect.objectContaining({ last_run_sql: source }));
});

it.each(['Invalid syntax', 'Network unavailable'])('a parse failure (%s) performs no panel or dashboard writes', async message => {
    vi.mocked(apiPost).mockRejectedValueOnce(new Error(message));
    const store = createDashboardStore(); store.sql = source; await store.run();
    expect(apiPost).toHaveBeenCalledTimes(1); expect(apiPatch).not.toHaveBeenCalled();
    expect(recompose).not.toHaveBeenCalled(); expect(store.dashboardId).toBeNull();
    expect(executionStore.errorMsg).toBe(message); expect(executionStore.executing).toBe(false);
    expect(store.sqlCheckError).toBe(message); expect(store.statementCount).toBe(0);
});

it('comment-only input creates no phantom panel or dashboard', async () => {
    vi.mocked(apiPost).mockResolvedValueOnce({ ...parsed, statements: [] });
    const store = createDashboardStore(); store.sql = '-- only;'; await store.run();
    expect(apiPost).toHaveBeenCalledTimes(1); expect(apiPatch).not.toHaveBeenCalled();
    expect(store.panelIds).toEqual([]); expect(store.sqlCheckReady).toBe(true);
});

it('a syntax failure preserves the confirmed panels, layout and applied filters', async () => {
    transport();
    vi.mocked(recompose).mockResolvedValue({ rows: [{ panels: [{ panel_id: 'p1', ...result,
        final_col_span: 6, col_offset: 0, row_index: 0 }] }] });
    const store = createDashboardStore(); store.sql = source; await store.run();
    const before = { layout: store.layout, results: store.executedResults, panelIds: store.panelIds, panelSQLs: store.panelSQLs };
    filterValues.replace({ period: '2026' }); store.sql = "SELECT 'unfinished";
    vi.mocked(apiPost).mockRejectedValueOnce(new Error('Invalid SQL')); vi.mocked(apiPatch).mockClear();
    await store.run();
    expect(store.layout).toEqual(before.layout); expect(store.executedResults).toEqual(before.results);
    expect(store.panelIds).toEqual(before.panelIds); expect(store.panelSQLs).toEqual(before.panelSQLs);
    expect(filterValues.current).toEqual({ period: '2026' }); expect(apiPatch).not.toHaveBeenCalled();
});

it('editing after a failed first run clears its stale error without creating a dashboard', async () => {
    vi.mocked(apiPost).mockRejectedValueOnce(new Error('Invalid SQL'));
    const store = createDashboardStore(); store.sql = "SELECT 'unfinished"; await store.run();
    store.sql = 'SELECT 1'; expect(executionStore.errorMsg).toBeNull(); expect(store.sqlCheckError).toBeNull();
    expect(store.dashboardId).toBeNull();
});

it('switching to a newly created dashboard while parsing cannot overwrite that view', async () => {
    const response = deferred(); vi.mocked(apiPost).mockReturnValueOnce(response.promise).mockResolvedValueOnce({ id: 'other' });
    const store = createDashboardStore(); store.sql = source; const operation = store.run();
    await store.createDashboard('Other'); response.resolve(parsed); await operation;
    expect(apiPost).toHaveBeenCalledTimes(2); expect(apiPatch).not.toHaveBeenCalled();
    expect(store.dashboardId).toBe('other'); expect(store.sql).toBe(''); expect(store.layout).toBeNull();
});

it('a source edit while parsing prevents executing the outdated snapshot', async () => {
    const response = deferred(); vi.mocked(apiPost).mockReturnValueOnce(response.promise);
    const store = createDashboardStore(); store.sql = source; const operation = store.run();
    store.sql = 'SELECT 3'; response.resolve(parsed); await operation;
    expect(apiPost).toHaveBeenCalledTimes(1); expect(apiPatch).not.toHaveBeenCalled();
    expect(store.sqlCheckReady).toBe(false); expect(store.statementCount).toBe(0);
});

it('focus uses the backend source offset instead of counting semicolons', async () => {
    transport(); const store = createDashboardStore(); store.sql = source; await store.run();
    const focusOffset = vi.fn(); editorRef.set({ focusOffset });
    await store.handleEditSQL('p2');
    expect(focusOffset).toHaveBeenCalledWith(first.length + 2);
    expect(vi.mocked(apiPost).mock.calls.filter(([path]) => path === '/api/v1/sql/parse')).toHaveLength(1);
});

it('a late parse failure cannot attach an error to a different dashboard', async () => {
    const response = deferred(); vi.mocked(apiPost).mockReturnValueOnce(response.promise).mockResolvedValueOnce({ id: 'other' });
    const store = createDashboardStore(); store.sql = source; const operation = store.run();
    await store.createDashboard('Other'); response.reject(new Error('Invalid old script')); await operation;
    expect(executionStore.errorMsg).toBeNull(); expect(store.sqlCheckError).toBeNull();
});

it('retains the exact executed snapshot if the draft changes after execution starts', async () => {
    transport(); const response = deferred();
    const regular = vi.mocked(apiPost).getMockImplementation()!;
    vi.mocked(apiPost).mockImplementation((path, body) => path === '/api/v1/panels/p1/execute' ? response.promise : regular(path, body));
    const store = createDashboardStore(); store.sql = source; const operation = store.run();
    await vi.waitFor(() => expect(apiPost).toHaveBeenCalledWith('/api/v1/panels/p1/execute'));
    store.sql = 'SELECT 3'; response.resolve(result); await operation;
    expect(apiPatch).toHaveBeenCalledWith('/api/v1/dashboards/d', expect.objectContaining({ last_run_sql: source }));
    expect(store.sql).toBe('SELECT 3'); expect(store.canRestoreLastRun).toBe(true);
    store.restoreLastRun();
    expect(store.sqlIdentity?.statements.map(item => item.panel_id)).toEqual(['p1', 'p2']);
});

it('tracks a Monaco interior edit without losing its binding to an existing panel', async () => {
    transport(); const store = createDashboardStore(); store.sql = source; await store.run();
    const changedFirst = "SELECT 'xyz;b'";
    const changed = `${changedFirst};\n${second}`;
    const event = { before: source, after: changed, changes: [{ rangeOffset: first.indexOf('a'), rangeLength: 1, text: 'xyz' }], isFlush: false };
    expect(store.applySqlEditorChange(event)).toBe(true);
    // The bind:value setter receives the same value after the precise event.
    store.sql = changed;
    vi.mocked(apiPost).mockResolvedValueOnce({ ...parsed, statements: [
        { sql: changedFirst, start_offset: 0, end_offset: changedFirst.length },
        { sql: second, start_offset: changedFirst.length + 2, end_offset: changed.length },
    ] });
    vi.mocked(apiPatch).mockClear();
    await store.handleEditSQL('p1');
    expect(store.sqlIdentity?.statements.map(item => item.panel_id)).toEqual(['p1', 'p2']);
    expect(apiPatch).not.toHaveBeenCalled();
});

it('a plain source setter loses evidence even when reordering equal known SQL', async () => {
    transport(); const store = createDashboardStore(); store.sql = source; await store.run();
    const reversed = `${second}\n;\n\n${first}`;
    store.sql = reversed;
    vi.mocked(apiPost).mockResolvedValueOnce({ ...parsed, statements: [
        { sql: second, start_offset: 0, end_offset: second.length },
        { sql: first, start_offset: second.length + 4, end_offset: reversed.length },
    ] });
    await store.handleEditSQL('p1');
    expect(store.sqlIdentity?.statements.map(item => item.panel_id)).toEqual([null, null]);
    expect(store.sqlIdentity?.unresolved_panel_ids).toEqual(['p1', 'p2']);
});

it('an obsolete Monaco model cannot write into a newly selected dashboard', async () => {
    transport(); const store = createDashboardStore(); store.sql = source; await store.run();
    await store.createDashboard('Other');
    expect(store.applySqlEditorChange({ before: source, after: 'SELECT 100', changes: [], isFlush: false })).toBe(false);
    expect(store.sql).toBe(''); expect(store.panelIds).toEqual([]);
});

it('a late parse of a replaced draft cannot attach old bindings to a restored text', async () => {
    transport(); const store = createDashboardStore(); store.sql = source; await store.run();
    const response = deferred();
    store.sql = 'SELECT 5';
    vi.mocked(apiPost).mockReturnValueOnce(response.promise);
    const operation = store.handleEditSQL('p1');
    store.sql = source; // Opaque replacement; equality is not identity evidence.
    response.resolve({ ...parsed, statements: [{ sql: 'SELECT 5', start_offset: 0, end_offset: 8 }] });
    await operation;
    vi.mocked(apiPost).mockResolvedValueOnce(parsed);
    await store.handleEditSQL('p1');
    expect(store.sqlIdentity?.statements.map(item => item.panel_id)).toEqual([null, null]);
});

it.each([true, false])('load distinguishes saved arbitrary SQL from directly constructed panel source (saved=%s)', async saved => {
    const reconstructed = `${first}\n;\n\n${second}`;
    vi.mocked(apiGet).mockResolvedValue({ id: 'loaded', sql_content: saved ? reconstructed : '', last_run_at: null });
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ json: async () => [
        { id: 'p1', sql_content: first, sort_order: 0 }, { id: 'p2', sql_content: second, sort_order: 1 },
    ] }));
    vi.mocked(apiPost).mockResolvedValueOnce({ ...parsed, statements: [
        { sql: first, start_offset: 0, end_offset: first.length },
        { sql: second, start_offset: first.length + 4, end_offset: reconstructed.length },
    ] });
    const store = createDashboardStore(); await store.loadDashboard('loaded'); await store.handleEditSQL('p1');
    expect(store.sqlIdentity?.statements.map(item => item.panel_id)).toEqual(saved ? [null, null] : ['p1', 'p2']);
});
