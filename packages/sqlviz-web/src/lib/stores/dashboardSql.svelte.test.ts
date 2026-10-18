import { legacySqlSnapshot } from '$lib/sql/sqlSnapshot.testFixtures';
import type { SqlScriptSnapshot } from '$lib/sql/sqlScriptCommit';
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

const proof = `fixture.${'a'.repeat(64)}`;
const serverRunAt = '2026-10-09T17:00:00.123456+00:00';
const result = { inference_result: { filter_controls: [] } as unknown as InferenceResult, data: [{ total: 1 }],
    execution_receipt: proof, query_executed: true };
const first = "SELECT 'a;b'"; const second = 'SELECT 2 -- tail;';
const source = `${first};\n${second}`;
const parsed = { version: 1, dialect: 'duckdb', statements: [
    { sql: first, start_offset: 0, end_offset: first.length },
    { sql: second, start_offset: first.length + 2, end_offset: source.length },
] };
let proposedStatements = parsed.statements;

beforeEach(() => {
    vi.clearAllMocks(); vi.useFakeTimers(); dashboardCache.clear(); filterValues.reset();
    executionStore.executing = false; executionStore.errorMsg = null; executionStore.statusMsg = null;
    executionStore.saveStatus = 'idle'; proposedStatements = parsed.statements;
    editorRef.set({});
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ json: async () => [] }));
    vi.mocked(apiPatch).mockResolvedValue({});
    vi.mocked(apiGet).mockImplementation(async path =>
        path === '/api/v1/dashboards' || path === '/api/v1/folders' ? [] : legacySqlSnapshot(path.split('/').at(-2)!));
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
    let revision = 0;
    const token = () => `sql-script-v1:${revision.toString(16).padStart(64, '0')}`;
    let saved = { version: 1, dashboard_id: 'd', revision: token(), draft_source: '', definition_revision: null as string | null,
        publication_status: 'absent', last_run_at: null as string | null, last_run_sql: null as string | null,
        panels: [] as { id: string; name: string; sql_content: string; sort_order: number }[],
        publication: null as unknown };
    vi.mocked(apiGet).mockImplementation(async path => path.endsWith('/sql-script') ? saved : []);
    vi.mocked(apiPost).mockImplementation(async (path, body) => {
        if (path === '/api/v1/sql/parse') return parsed;
        if (path === '/api/v1/sql/reconcile') return fakePreflight(body);
        if (path === '/api/v1/dashboards') return { id: 'd' };
        if (path.endsWith('/sql-script/commit')) {
            const input = body as { sql: string; expected_revision: string; decisions: {
                kind: string; statement_index?: number; panel_id?: string; creation_key?: string;
            }[] };
            if (input.expected_revision !== saved.revision) throw new Error('Stale expected revision');
            const created_panels: { creation_key: string; panel_id: string }[] = [];
            const bindings = proposedStatements.map((statement, index) => {
                const choice = input.decisions.find(item => item.statement_index === index)!;
                const id = choice.kind === 'keep' ? choice.panel_id! : `p${++panels}`;
                if (choice.kind === 'create') created_panels.push({ creation_key: choice.creation_key!, panel_id: id });
                return { statement_index: index, panel_id: id, start_offset: statement.start_offset, end_offset: statement.end_offset };
            });
            revision++;
            saved = { ...saved, publication_status: 'confirmed', revision: token(), definition_revision: `sql-definition-v1:${revision.toString(16).padStart(64, '0')}`,
                draft_source: input.sql, panels: bindings.map((binding, i) => ({
                id: binding.panel_id, name: `Panel ${i + 1}`, sql_content: proposedStatements[i].sql, sort_order: i,
            })), publication: { version: 1, revision, source: input.sql, bindings } };
            return { version: 1, snapshot: saved, created_panels };
        }
        if (path.endsWith('/execute')) return { ...result, execution_reference: { version: 1,
            panel_id: path.split('/').at(-2), definition: (body as { definition: unknown }).definition } };
        if (path.endsWith('/sql-script/compose')) {
            const input = body as { definition: unknown; panels: { panel_id: string; inference_result: InferenceResult }[] };
            const template = await recompose([]);
            return { ...template, definition: input.definition, completion_receipt: input.panels.length ? proof : null,
                rows: template.rows.length ? template.rows : input.panels.length
                ? [{ panels: input.panels.map((panel, index) => ({ ...panel, final_col_span: 6, col_offset: index * 6, row_index: 0, data: [] })) }] : [] };
        }
        if (path.endsWith('/sql-script/complete')) {
            saved = { ...saved, last_run_at: serverRunAt, last_run_sql: saved.draft_source };
            return { definition: (body as { definition: unknown }).definition,
                last_run_at: serverRunAt, last_run_sql: saved.draft_source };
        }
        throw new Error(`Unexpected request: ${path}`);
    });
}

function fakePreflight(body: unknown, statements = parsed.statements) {
    const input = body as { sql: string; decisions: { kind: string; statement_index: number; panel_id?: string; creation_key?: string }[] };
    proposedStatements = statements;
    return { version: 1, source: input.sql, complete: true,
        removed_panel_ids: input.decisions.filter(item => item.kind === 'remove').map(item => item.panel_id), unresolved_panel_ids: [], unresolved_statement_indexes: [],
        statements: input.decisions.filter(item => item.kind !== 'remove').sort((a, b) => a.statement_index - b.statement_index).map(choice => ({
            ...statements[choice.statement_index], ...choice, panel_id: choice.panel_id ?? null, creation_key: choice.creation_key ?? null,
        })) };
}

it('uses native slices for panel SQL, count and exact last-run source', async () => {
    transport(); const store = createDashboardStore(); store.sql = source;
    expect(store.statementCount).toBe(0); expect(store.sqlCheckReady).toBe(false);
    await store.run();
    expect(apiPost).toHaveBeenNthCalledWith(1, '/api/v1/sql/parse', { sql: source });
    expect(apiPost).toHaveBeenCalledWith('/api/v1/dashboards/d/sql-script/commit', expect.objectContaining({ sql: source }));
    expect(vi.mocked(apiPost).mock.calls.filter(([path]) => path.endsWith('/sql-script/commit'))).toHaveLength(1);
    expect(vi.mocked(apiPost).mock.calls.some(([path]) => path === '/api/v1/panels')).toBe(false);
    expect(store.statementCount).toBe(2); expect(store.panelSQLs).toEqual([first, second]);
    expect(apiPost).toHaveBeenCalledWith('/api/v1/dashboards/d/sql-script/complete', expect.objectContaining({ completion_receipt: proof }));
    expect(store.lastRunAt).toBe(serverRunAt);
    expect(apiPatch).not.toHaveBeenCalled();
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
        final_col_span: 6, col_offset: 0, row_index: 0 }, { panel_id: 'p2', ...result,
        final_col_span: 6, col_offset: 6, row_index: 0 }] }] });
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
    await vi.waitFor(() => expect(apiPost).toHaveBeenCalledWith('/api/v1/panels/p1/execute', expect.any(Object)));
    store.sql = 'SELECT 3'; response.resolve({ ...result, execution_reference: { version: 1, panel_id: 'p1',
        definition: { version: 1, dashboard_id: 'd', revision: `sql-definition-v1:${'1'.padStart(64, '0')}` } } }); await operation;
    expect(store.lastRunAt).toBe(serverRunAt);
    expect(apiPatch).not.toHaveBeenCalled();
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
    vi.mocked(apiGet).mockResolvedValue(legacySqlSnapshot('loaded', [
        { id: 'p1', sql_content: first }, { id: 'p2', sql_content: second },
    ], saved ? reconstructed : ''));
    vi.mocked(apiPost).mockResolvedValueOnce({ ...parsed, statements: [
        { sql: first, start_offset: 0, end_offset: first.length },
        { sql: second, start_offset: first.length + 4, end_offset: reconstructed.length },
    ] });
    const store = createDashboardStore(); await store.loadDashboard('loaded'); await store.handleEditSQL('p1');
    expect(store.sqlIdentity?.statements.map(item => item.panel_id)).toEqual(saved ? [null, null] : ['p1', 'p2']);
});

it('reloads persisted associations and reruns with the same IDs without a resolution dialog', async () => {
    transport(); const firstStore = createDashboardStore(); firstStore.sql = source; await firstStore.run();
    vi.mocked(apiPost).mockClear(); vi.mocked(apiPatch).mockClear();
    const reloaded = createDashboardStore(); await reloaded.loadDashboard('d');
    expect(reloaded.panelIds).toEqual(['p1', 'p2']); expect(reloaded.lastRunAt).toBe(serverRunAt);
    expect(reloaded.executedResults).toEqual([]); expect(reloaded.layout).toBeNull();
    expect(vi.mocked(apiPost).mock.calls.every(([path]) => path === '/api/v1/sql/parse')).toBe(true);
    expect(apiPatch).not.toHaveBeenCalled();
    await reloaded.run();
    expect(reloaded.sqlRunResolution).toBeNull(); expect(reloaded.panelIds).toEqual(['p1', 'p2']);
    expect(apiPost).toHaveBeenCalledWith('/api/v1/dashboards/d/sql-script/commit', expect.objectContaining({
        decisions: [{ kind: 'keep', statement_index: 0, panel_id: 'p1' }, { kind: 'keep', statement_index: 1, panel_id: 'p2' }],
    }));
});

it('reloads a newer draft and restores the verified last-run identity only for its exact publication', async () => {
    transport(); const original = createDashboardStore(); original.sql = source; await original.run();
    const snapshot = await apiGet<SqlScriptSnapshot>('/api/v1/dashboards/d/sql-script');
    snapshot.draft_source = "SELECT 'unfinished";
    const reloaded = createDashboardStore(); await reloaded.loadDashboard('d');
    expect(reloaded.sql).toBe(snapshot.draft_source); expect(reloaded.sqlIdentity).toBeNull();
    expect(reloaded.canRestoreLastRun).toBe(true);
    reloaded.restoreLastRun(); await reloaded.handleEditSQL('p1');
    expect(reloaded.sql).toBe(source);
    expect(reloaded.sqlIdentity?.statements.map(item => item.panel_id)).toEqual(['p1', 'p2']);
});

it('saved definitions survive a failed execution and reload independently of last successful Run', async () => {
    transport(); const regular = vi.mocked(apiPost).getMockImplementation()!;
    vi.mocked(apiPost).mockImplementation((path, body) => path === '/api/v1/panels/p1/execute'
        ? Promise.reject(new Error('Query failed')) : regular(path, body));
    const original = createDashboardStore(); original.sql = source; await original.run();
    const reloaded = createDashboardStore(); await reloaded.loadDashboard('d');
    expect(reloaded.panelIds).toEqual(['p1', 'p2']); expect(reloaded.lastRunAt).toBeNull();
    await reloaded.handleEditSQL('p1');
    expect(reloaded.sqlIdentity?.statements.map(item => item.panel_id)).toEqual(['p1', 'p2']);
});

it('opaque reordering requires explicit IDs, then commits and focuses the selected panels', async () => {
    transport(); const store = createDashboardStore(); store.sql = source; await store.run();
    const reversed = `${second}\n;\n\n${first}`;
    const reordered = [
        { sql: second, start_offset: 0, end_offset: second.length },
        { sql: first, start_offset: second.length + 4, end_offset: reversed.length },
    ];
    const regular = vi.mocked(apiPost).getMockImplementation()!;
    vi.mocked(apiPost).mockImplementation((path, body) => path === '/api/v1/sql/parse'
        ? Promise.resolve({ ...parsed, statements: reordered }) : path === '/api/v1/sql/reconcile'
            ? Promise.resolve(fakePreflight(body, reordered)) : regular(path, body));
    vi.mocked(apiPost).mockClear(); vi.mocked(apiPatch).mockClear();
    store.sql = reversed; await store.run();
    expect(store.sqlRunResolution?.choices).toEqual([]);
    expect(apiPost).toHaveBeenCalledTimes(1); expect(apiPatch).not.toHaveBeenCalled();
    store.chooseSqlRunPanel(0, 'p2'); store.chooseSqlRunPanel(1, 'p1');
    await store.confirmSqlRunResolution();
    expect(apiPost).toHaveBeenCalledWith('/api/v1/dashboards/d/sql-script/commit', expect.objectContaining({
        sql: reversed, decisions: [{ kind: 'keep', statement_index: 0, panel_id: 'p2' }, { kind: 'keep', statement_index: 1, panel_id: 'p1' }],
    }));
    expect(vi.mocked(apiPatch).mock.calls.some(([path]) => path.startsWith('/api/v1/panels/'))).toBe(false);
    expect(vi.mocked(apiPost).mock.calls.some(([path]) => path === '/api/v1/panels')).toBe(false);
    expect(store.panelIds).toEqual(['p2', 'p1']); expect(store.sqlRunResolution).toBeNull();
    const focusOffset = vi.fn(); editorRef.set({ focusOffset }); await store.handleEditSQL('p1');
    expect(focusOffset).toHaveBeenCalledWith(second.length + 4);
});

it('removing a query cannot silently discard an existing panel; cancel performs no writes', async () => {
    transport(); const store = createDashboardStore(); store.sql = source; await store.run();
    store.sql = first;
    vi.mocked(apiPost).mockResolvedValueOnce({ ...parsed, statements: [parsed.statements[0]] });
    vi.mocked(apiPost).mockClear(); vi.mocked(apiPatch).mockClear();
    await store.run(); store.chooseSqlRunPanel(0, 'p1'); await store.confirmSqlRunResolution();
    expect(store.sqlRunResolution).not.toBeNull(); expect(apiPost).toHaveBeenCalledTimes(1);
    expect(apiPatch).not.toHaveBeenCalled(); expect(store.panelIds).toEqual(['p1', 'p2']);
    store.cancelSqlRunResolution(); expect(store.sqlRunResolution).toBeNull();
    expect(store.panelIds).toEqual(['p1', 'p2']);
});

it('a tracked insertion creates a new panel without transferring existing settings to it', async () => {
    transport(); const store = createDashboardStore(); store.sql = source; await store.run();
    const prefix = 'SELECT 3;\n'; const changed = prefix + source;
    store.applySqlEditorChange({ before: source, after: changed, changes: [{ rangeOffset: 0, rangeLength: 0, text: prefix }], isFlush: false });
    const statements = [{ sql: 'SELECT 3', start_offset: 0, end_offset: 8 },
        ...parsed.statements.map(item => ({ ...item, start_offset: item.start_offset + prefix.length, end_offset: item.end_offset + prefix.length }))];
    const regular = vi.mocked(apiPost).getMockImplementation()!;
    vi.mocked(apiPost).mockImplementation((path, body) => path === '/api/v1/sql/parse'
        ? Promise.resolve({ ...parsed, statements }) : path === '/api/v1/sql/reconcile'
            ? Promise.resolve(fakePreflight(body, statements)) : regular(path, body));
    vi.mocked(apiPost).mockClear(); vi.mocked(apiPatch).mockClear(); await store.run();
    expect(store.sqlRunResolution).toBeNull(); expect(store.panelIds).toEqual(['p3', 'p1', 'p2']);
    expect(apiPost).toHaveBeenCalledWith('/api/v1/dashboards/d/sql-script/commit', expect.objectContaining({
        decisions: expect.arrayContaining([{ kind: 'keep', statement_index: 1, panel_id: 'p1' }, { kind: 'keep', statement_index: 2, panel_id: 'p2' }]),
    }));
});

it('a failed preflight writes nothing and keeps explicit choices for retry', async () => {
    transport(); const store = createDashboardStore(); store.sql = source;
    const regular = vi.mocked(apiPost).getMockImplementation()!;
    vi.mocked(apiPost).mockImplementation((path, body) => path === '/api/v1/sql/reconcile'
        ? Promise.reject(new Error('Panel snapshot changed')) : regular(path, body));
    await store.run();
    expect(apiPatch).not.toHaveBeenCalled(); expect(store.dashboardId).toBeNull();
    expect(vi.mocked(apiPost).mock.calls.map(([path]) => path)).toEqual(['/api/v1/sql/parse', '/api/v1/sql/reconcile']);
    const choices = store.sqlRunResolution?.choices; expect(choices).toHaveLength(2);
    vi.mocked(apiPost).mockImplementation(regular); await store.confirmSqlRunResolution();
    expect(vi.mocked(apiPost).mock.calls.filter(([path]) => path === '/api/v1/sql/reconcile')[1][1]).toEqual(
        expect.objectContaining({ decisions: choices }));
    expect(store.panelIds).toEqual(['p1', 'p2']);
});

it.each([false, true])('a changed draft invalidates an in-flight preflight even if its text is restored (restore=%s)', async restore => {
    transport(); const response = deferred(); const regular = vi.mocked(apiPost).getMockImplementation()!;
    vi.mocked(apiPost).mockImplementation((path, body) => path === '/api/v1/sql/reconcile' ? response.promise : regular(path, body));
    const store = createDashboardStore(); store.sql = source; const operation = store.run();
    await vi.waitFor(() => expect(apiPost).toHaveBeenCalledWith('/api/v1/sql/reconcile', expect.anything()));
    const body = vi.mocked(apiPost).mock.calls.find(([path]) => path === '/api/v1/sql/reconcile')![1];
    store.sql = 'SELECT 99'; if (restore) store.sql = source;
    response.resolve(fakePreflight(body)); await operation;
    expect(apiPatch).not.toHaveBeenCalled(); expect(store.dashboardId).toBeNull();
    expect(store.sqlRunResolution).toBeNull(); expect(store.sql).toBe(restore ? source : 'SELECT 99');
});

it('editing an unresolved draft cancels old choices without changing confirmed IDs', async () => {
    transport(); const store = createDashboardStore(); store.sql = source; await store.run();
    store.sql = source + ' '; await store.run(); expect(store.sqlRunResolution).not.toBeNull();
    store.chooseSqlRunPanel(0, 'p1'); store.sql = source;
    expect(store.sqlRunResolution).toBeNull(); expect(store.panelIds).toEqual(['p1', 'p2']);
});

it('a rejected commit preserves the previous view and does not start execution', async () => {
    transport(); const store = createDashboardStore(); store.sql = source; await store.run();
    const before = { ids: store.panelIds, results: store.executedResults, layout: store.layout };
    filterValues.replace({ period: '2026' });
    const regular = vi.mocked(apiPost).getMockImplementation()!;
    vi.mocked(apiPost).mockImplementation((path, body) => path.endsWith('/sql-script/commit')
        ? Promise.reject(new Error('Dashboard changed')) : regular(path, body));
    vi.mocked(apiPost).mockClear(); vi.mocked(apiPatch).mockClear();
    await store.run();
    expect(store.panelIds).toEqual(before.ids); expect(store.executedResults).toEqual(before.results);
    expect(store.layout).toEqual(before.layout); expect(filterValues.current).toEqual({ period: '2026' });
    expect(store.sqlRunResolution?.choices.every(item => item.kind === 'keep')).toBe(true);
    expect(vi.mocked(apiPost).mock.calls.some(([path]) => path.endsWith('/execute'))).toBe(false);
    expect(executionStore.errorMsg).toContain('Could not confirm saving');
});

it.each(['execution', 'composition'])('a post-commit %s failure keeps IDs saved and retries without new creations', async stage => {
    transport(); const regular = vi.mocked(apiPost).getMockImplementation()!;
    if (stage === 'execution') vi.mocked(apiPost).mockImplementation((path, body) => path === '/api/v1/panels/p2/execute'
        ? Promise.reject(new Error('Query failed')) : regular(path, body));
    else vi.mocked(recompose).mockRejectedValueOnce(new Error('Layout failed'));
    const store = createDashboardStore(); store.sql = source; await store.run();
    expect(store.panelIds).toEqual(['p1', 'p2']); expect(store.panelSQLs).toEqual([first, second]);
    expect(store.executedResults).toEqual([]); expect(store.layout).toBeNull();
    expect(store.sqlIdentity?.statements.map(item => item.panel_id)).toEqual(['p1', 'p2']);
    expect(store.sqlRunResolution).toBeNull(); expect(executionStore.errorMsg).toContain('Definitions saved.');
    expect(store.lastRunAt).toBeNull(); expect(apiPatch).not.toHaveBeenCalled();
    vi.mocked(apiPost).mockImplementation(regular); vi.mocked(apiPost).mockClear();
    await store.run();
    const body = vi.mocked(apiPost).mock.calls.find(([path]) => path.endsWith('/sql-script/commit'))![1];
    expect(body).toEqual(expect.objectContaining({ decisions: [
        { kind: 'keep', statement_index: 0, panel_id: 'p1' }, { kind: 'keep', statement_index: 1, panel_id: 'p2' },
    ] }));
    expect(store.panelIds).toEqual(['p1', 'p2']); expect(store.executedResults).toHaveLength(2);
});

it('a failed execution acknowledgement does not claim that the definitions were not saved', async () => {
    transport(); const regular = vi.mocked(apiPost).getMockImplementation()!;
    vi.mocked(apiPost).mockImplementation((path, body) => path.endsWith('/sql-script/complete')
        ? Promise.reject(new Error('Offline')) : regular(path, body));
    const store = createDashboardStore(); store.sql = source; await store.run();
    expect(store.panelIds).toEqual(['p1', 'p2']); expect(store.executedResults).toHaveLength(2);
    expect(store.sqlRunResolution).toBeNull(); expect(store.lastRunAt).toBeNull();
    expect(executionStore.errorMsg).toContain('Definitions saved and queries executed');
});

it('a mixed fallback Run preserves controls and never records successful execution', async () => {
    transport(); const regular = vi.mocked(apiPost).getMockImplementation()!;
    vi.mocked(apiPost).mockImplementation(async (path, body) => {
        const response = await regular(path, body) as Record<string, unknown>;
        if (path === '/api/v1/panels/p2/execute') return { ...response, query_executed: false };
        if (path.endsWith('/sql-script/compose')) return { ...response, completion_receipt: null };
        return response;
    });
    const store = createDashboardStore(); store.sql = source; await store.run();
    expect(store.executedResults).toHaveLength(2); expect(store.layout).not.toBeNull();
    expect(store.panelIds).toEqual(['p1', 'p2']); expect(store.lastRunAt).toBeNull();
    expect(executionStore.errorMsg).toContain('not recorded as successful');
    expect(vi.mocked(apiPost).mock.calls.some(([path]) => path.endsWith('/sql-script/complete'))).toBe(false);
    expect(apiPatch).not.toHaveBeenCalled();
});

it('explicit removal is submitted in the same commit as kept SQL; cancellation performs no writes', async () => {
    transport(); const store = createDashboardStore(); store.sql = source; await store.run();
    const regular = vi.mocked(apiPost).getMockImplementation()!;
    vi.mocked(apiPost).mockImplementation((path, body) => path === '/api/v1/sql/parse'
        ? Promise.resolve({ ...parsed, statements: [parsed.statements[0]] }) : path === '/api/v1/sql/reconcile'
            ? Promise.resolve(fakePreflight(body, [parsed.statements[0]])) : regular(path, body));
    store.sql = first; vi.mocked(apiPost).mockClear(); vi.mocked(apiPatch).mockClear(); await store.run();
    store.chooseSqlRunPanel(0, 'p1'); store.chooseSqlRunRemoval('p2', true);
    expect(store.panelIds).toEqual(['p1', 'p2']);
    store.cancelSqlRunResolution();
    expect(vi.mocked(apiPost).mock.calls.some(([path]) => path.endsWith('/sql-script/commit'))).toBe(false);
    await store.run(); store.chooseSqlRunPanel(0, 'p1'); store.chooseSqlRunRemoval('p2', true);
    await store.confirmSqlRunResolution();
    expect(apiPost).toHaveBeenCalledWith('/api/v1/dashboards/d/sql-script/commit', expect.objectContaining({
        sql: first, decisions: [{ kind: 'keep', statement_index: 0, panel_id: 'p1' }, { kind: 'remove', panel_id: 'p2' }],
    }));
    expect(store.panelIds).toEqual(['p1']); expect(store.executedResults).toHaveLength(1);
});

it('a comment-only script can remove all panels explicitly without marking queries as executed', async () => {
    transport(); const store = createDashboardStore(); store.sql = source; await store.run();
    const previousRun = store.lastRunAt;
    const regular = vi.mocked(apiPost).getMockImplementation()!;
    vi.mocked(apiPost).mockImplementation((path, body) => path === '/api/v1/sql/parse'
        ? Promise.resolve({ ...parsed, statements: [] }) : path === '/api/v1/sql/reconcile'
            ? Promise.resolve(fakePreflight(body, [])) : regular(path, body));
    store.sql = '-- cleared'; vi.mocked(apiPost).mockClear(); vi.mocked(apiPatch).mockClear(); await store.run();
    expect(store.sqlRunResolution?.statements).toEqual([]);
    store.chooseSqlRunRemoval('p1', true); store.chooseSqlRunRemoval('p2', true);
    await store.confirmSqlRunResolution();
    expect(store.panelIds).toEqual([]); expect(store.executedResults).toEqual([]);
    expect(store.lastRunAt).toBe(previousRun); expect(apiPatch).not.toHaveBeenCalled();
    expect(vi.mocked(apiPost).mock.calls.some(([path]) => path.endsWith('/execute'))).toBe(false);
});

it('a commit acknowledgement does not overwrite text edited while that commit was in flight', async () => {
    transport(); const response = deferred(); const regular = vi.mocked(apiPost).getMockImplementation()!;
    let receipt: unknown;
    vi.mocked(apiPost).mockImplementation(async (path, body) => {
        if (!path.endsWith('/sql-script/commit')) return regular(path, body);
        receipt = await regular(path, body); return response.promise;
    });
    const store = createDashboardStore(); store.sql = source; const operation = store.run();
    await vi.waitFor(() => expect(receipt).toBeDefined());
    store.sql = 'SELECT 99'; response.resolve(receipt); await operation;
    expect(store.sql).toBe('SELECT 99'); expect(store.panelIds).toEqual(['p1', 'p2']);
    expect(executionStore.saveStatus).toBe('draft');
    expect(store.lastRunAt).toBe(serverRunAt); expect(apiPatch).not.toHaveBeenCalled();
    expect(vi.mocked(apiPatch).mock.calls.every(([, body]) => !('sql_content' in (body as object)))).toBe(true);
});

it('Run waits for an in-flight draft write and suspends additional auto-save during preparation', async () => {
    transport(); const store = createDashboardStore(); store.sql = source; await store.run();
    const response = deferred(); vi.mocked(apiPatch).mockReturnValueOnce(response.promise);
    store.sql = source + ' '; store.saveDraft();
    await vi.waitFor(() => expect(apiPatch).toHaveBeenCalledWith('/api/v1/dashboards/d', { sql_content: source + ' ' }));
    vi.mocked(apiGet).mockClear(); const operation = store.run();
    await Promise.resolve(); await Promise.resolve();
    expect(apiGet).not.toHaveBeenCalled();
    store.saveDraft(true); expect(fetch).not.toHaveBeenCalledWith('/api/v1/dashboards/d', expect.objectContaining({ method: 'PATCH' }));
    response.resolve({}); await operation;
    expect(apiGet).toHaveBeenCalledWith('/api/v1/dashboards/d/sql-script');
});

it('confirmation retains the reviewed revision instead of fetching a new token silently', async () => {
    transport(); const store = createDashboardStore(); store.sql = source; await store.run();
    vi.mocked(apiGet).mockClear(); vi.mocked(apiPost).mockClear(); store.sql = source + ' '; await store.run();
    const revision = store.sqlRunResolution?.expectedRevision;
    store.chooseSqlRunPanel(0, 'p1'); store.chooseSqlRunPanel(1, 'p2');
    await store.confirmSqlRunResolution();
    expect(vi.mocked(apiGet).mock.calls.filter(([path]) => path.endsWith('/sql-script'))).toHaveLength(1);
    expect(apiPost).toHaveBeenCalledWith('/api/v1/dashboards/d/sql-script/commit', expect.objectContaining({ expected_revision: revision }));
});

it('Run sends one confirmed definition to every execution and to composition', async () => {
    transport(); const store = createDashboardStore(); store.sql = source; await store.run();
    const expected = { version: 1, dashboard_id: 'd', revision: `sql-definition-v1:${'1'.padStart(64, '0')}` };
    const executions = vi.mocked(apiPost).mock.calls.filter(([path]) => path.endsWith('/execute'));
    expect(executions).toHaveLength(2);
    executions.forEach(([, body]) => expect(body).toEqual({ definition: expected }));
    const composition = vi.mocked(apiPost).mock.calls.find(([path]) => path.endsWith('/sql-script/compose'))!;
    expect(composition[1]).toEqual(expect.objectContaining({ definition: expected }));
    expect(vi.mocked(apiPost).mock.calls.some(([path]) => path === '/api/v1/compose')).toBe(false);
});

it.each(['execution', 'composition'])('a mismatched %s reference cannot enter the view or record success', async stage => {
    transport(); const regular = vi.mocked(apiPost).getMockImplementation()!;
    vi.mocked(apiPost).mockImplementation(async (path, body) => {
        const response = await regular(path, body) as Record<string, unknown>;
        if (stage === 'execution' && path === '/api/v1/panels/p1/execute') return { ...response,
            execution_reference: { version: 1, panel_id: 'p1', definition: {
                version: 1, dashboard_id: 'd', revision: `sql-definition-v1:${'b'.repeat(64)}` } } };
        if (stage === 'composition' && path.endsWith('/sql-script/compose')) return { ...response,
            definition: { version: 1, dashboard_id: 'other', revision: `sql-definition-v1:${'b'.repeat(64)}` } };
        return response;
    });
    const store = createDashboardStore(); store.sql = source; await store.run();
    expect(store.panelIds).toEqual(['p1', 'p2']); expect(store.layout).toBeNull();
    expect(store.executedResults).toEqual([]); expect(store.lastRunAt).toBeNull();
    expect(apiPatch).not.toHaveBeenCalled(); expect(executionStore.errorMsg).toContain('Definitions saved.');
    if (stage === 'execution') expect(vi.mocked(apiPost).mock.calls.some(([path]) => path.endsWith('/sql-script/compose'))).toBe(false);
});
