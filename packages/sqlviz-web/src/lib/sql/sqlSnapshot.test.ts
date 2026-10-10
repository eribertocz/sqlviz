import { expect, it, vi } from 'vitest';
import { loadSqlSnapshot, sqlSnapshotMatchesCache } from './sqlSnapshot';
import { projectSqlIdentity } from './sqlIdentityDraft';
import { legacySqlSnapshot } from './sqlSnapshot.testFixtures';
import type { CachedDashboard } from '$lib/stores/dashboardCache.svelte';
import type { SqlScriptSnapshot } from './sqlScriptCommit';
import type { InferenceResult } from '$lib/types';

const first = "SELECT '🧠;text' AS label";
const second = 'SELECT 2 -- tail;';
const source = `${first};\n${second}`;
const statements = [{ sql: first, start_offset: 0, end_offset: first.length },
    { sql: second, start_offset: first.length + 2, end_offset: source.length }];

function published(): SqlScriptSnapshot {
    return { ...legacySqlSnapshot('d', [{ id: 'a', sql_content: first }, { id: 'b', sql_content: second }], source),
        publication_status: 'confirmed', definition_revision: `sql-definition-v1:${'a'.repeat(64)}`,
        last_run_at: '2026-10-09T12:00:00Z', last_run_sql: source,
        publication: { version: 1, revision: 3, source, bindings: statements.map((statement, index) => ({
            statement_index: index, panel_id: index ? 'b' : 'a',
            start_offset: statement.start_offset, end_offset: statement.end_offset,
        })) } };
}

it('restores explicit bindings from a native-verified source, including UTF-16 and quoted semicolons', async () => {
    const parse = vi.fn().mockResolvedValue(statements);
    const loaded = await loadSqlSnapshot(published(), 'd', parse);
    expect(parse).toHaveBeenCalledWith(source);
    expect(projectSqlIdentity(loaded.identity, statements).statements.map(item => item.panel_id)).toEqual(['a', 'b']);
    expect(loaded.lastRunIdentity).toBe(loaded.identity);
    expect(loaded.lastRunAt).toBe('2026-10-09T12:00:00Z');
});

it('keeps a newer invalid draft unbound while retaining verified identity for restoring the last run', async () => {
    const snapshot = published(); snapshot.draft_source = "SELECT 'unfinished";
    const loaded = await loadSqlSnapshot(snapshot, 'd', vi.fn().mockResolvedValue(statements));
    expect(loaded.source).toBe(snapshot.draft_source); expect(loaded.identity.bindings).toEqual([]);
    expect(loaded.lastRunIdentity?.source).toBe(source);
});

it('preserves an intentionally empty draft even when confirmed queries still exist', async () => {
    const snapshot = published(); snapshot.draft_source = '';
    const loaded = await loadSqlSnapshot(snapshot, 'd', vi.fn().mockResolvedValue(statements));
    expect(loaded.source).toBe(''); expect(loaded.identity.bindings).toEqual([]);
});

it('identical query text retains the persisted IDs rather than matching by text or panel order', async () => {
    const query = 'SELECT 1'; const duplicateSource = `${query};\n${query}`;
    const native = [{ sql: query, start_offset: 0, end_offset: 8 }, { sql: query, start_offset: 10, end_offset: 18 }];
    const snapshot = published();
    snapshot.draft_source = duplicateSource; snapshot.publication!.source = duplicateSource;
    snapshot.panels.forEach(panel => panel.sql_content = query);
    snapshot.publication!.bindings = native.map((statement, index) => ({
        statement_index: index, panel_id: index ? 'a' : 'b', start_offset: statement.start_offset, end_offset: statement.end_offset,
    }));
    const loaded = await loadSqlSnapshot(snapshot, 'd', vi.fn().mockResolvedValue(native));
    expect(projectSqlIdentity(loaded.identity, native).statements.map(item => item.panel_id)).toEqual(['b', 'a']);
    expect(loaded.lastRunIdentity).toBeNull();
});

it.each(['owner', 'token', 'status', 'duplicate', 'definition', 'publication', 'binding', 'offset', 'sql', 'last-run', 'missing'])
('rejects an inconsistent %s snapshot before adopting identity', async field => {
    const snapshot = published();
    if (field === 'owner') snapshot.dashboard_id = 'other';
    if (field === 'token') snapshot.revision = 'bad';
    if (field === 'status') snapshot.publication_status = 'absent';
    if (field === 'duplicate') snapshot.panels[1].id = 'a';
    if (field === 'definition') snapshot.definition_revision = null;
    if (field === 'publication') snapshot.publication!.version = 2 as 1;
    if (field === 'binding') snapshot.publication!.bindings[1].panel_id = 'a';
    if (field === 'offset') snapshot.publication!.bindings[1].end_offset--;
    if (field === 'sql') snapshot.panels[1].sql_content = 'SELECT 3';
    if (field === 'last-run') snapshot.last_run_at = '2026-10-09T12:00:00';
    if (field === 'missing') delete (snapshot as Partial<SqlScriptSnapshot>).last_run_sql;
    await expect(loadSqlSnapshot(snapshot, 'd', vi.fn().mockResolvedValue(statements))).rejects.toThrow('snapshot');
});

it('rejects stored ranges that omit a native statement and propagates parser failures', async () => {
    await expect(loadSqlSnapshot(published(), 'd', vi.fn().mockResolvedValue(statements.slice(0, 1)))).rejects.toThrow('snapshot');
    await expect(loadSqlSnapshot(published(), 'd', vi.fn().mockRejectedValue(new Error('Native parser busy')))).rejects.toThrow('busy');
});

it('reconstructs only an uninitialized legacy source directly from paired panels', async () => {
    const parse = vi.fn(); const snapshot = legacySqlSnapshot('d', [{ id: 'a', sql_content: first }, { id: 'b', sql_content: second }]);
    const loaded = await loadSqlSnapshot(snapshot, 'd', parse);
    expect(loaded.source).toBe(`${first}\n;\n\n${second}`);
    expect(loaded.identity.bindings.map(item => item.panel_id)).toEqual(['a', 'b']);
    expect(loaded.lastRunIdentity).toBeNull(); expect(parse).not.toHaveBeenCalled();
    snapshot.draft_source = loaded.source;
    expect((await loadSqlSnapshot(snapshot, 'd', parse)).identity.bindings).toEqual([]);
});

it('an incompatible publication preserves even an empty draft and never guesses correspondence', async () => {
    const snapshot = legacySqlSnapshot('d', [{ id: 'a', sql_content: first }]);
    snapshot.publication_status = 'incompatible';
    const loaded = await loadSqlSnapshot(snapshot, 'd', vi.fn());
    expect(loaded.source).toBe(''); expect(loaded.identity.panel_ids).toEqual(['a']);
    expect(loaded.identity.bindings).toEqual([]);
});

it('accepts a confirmed empty publication without converting comments into panels', async () => {
    const snapshot = published(); snapshot.panels = []; snapshot.last_run_sql = null;
    snapshot.draft_source = '-- empty'; snapshot.publication!.source = '-- empty'; snapshot.publication!.bindings = [];
    const loaded = await loadSqlSnapshot(snapshot, 'd', vi.fn().mockResolvedValue([]));
    expect(loaded.source).toBe('-- empty'); expect(loaded.identity.panel_ids).toEqual([]);
});

it.each(['source', 'generation', 'ids', 'sql', 'missing-revision', 'missing-result', 'extra-result', 'duplicate-result', 'layout'])
('does not revive a cache with stale %s', async field => {
    const loaded = await loadSqlSnapshot(published(), 'd', vi.fn().mockResolvedValue(statements));
    const cached: CachedDashboard = { sql: source, definitionRevision: loaded.definitionRevision,
        panelIds: ['b', 'a'], panelSQLs: [second, first],
        executedResults: ['b', 'a'].map(panel_id => ({ panel_id, data: [], inference_result: {} as InferenceResult })),
        layout: null, filterDomains: {}, filterValues: {} };
    expect(sqlSnapshotMatchesCache(loaded, cached)).toBe(true);
    if (field === 'source') cached.sql += ' ';
    if (field === 'generation') cached.definitionRevision = `sql-definition-v1:${'b'.repeat(64)}`;
    if (field === 'ids') cached.panelIds[0] = 'deleted';
    if (field === 'sql') cached.panelSQLs[0] = 'SELECT 3';
    if (field === 'missing-revision') delete cached.definitionRevision;
    if (field === 'missing-result') cached.executedResults.pop();
    if (field === 'extra-result') cached.executedResults.push({ ...cached.executedResults[0], panel_id: 'deleted' });
    if (field === 'duplicate-result') cached.executedResults[1] = cached.executedResults[0];
    if (field === 'layout') cached.layout = { rows: [{ panels: [{ ...cached.executedResults[0], panel_id: 'deleted',
        final_col_span: 12, col_offset: 0, row_index: 0 }] }] };
    expect(sqlSnapshotMatchesCache(loaded, cached)).toBe(false);
});
