import { beforeEach, expect, it, vi } from 'vitest';
import { apiPost } from '$lib/api';
import { createSqlScriptAnalysis, joinSqlStatements, parseSqlScript, type SqlStatement } from './sqlScript.svelte';

vi.mock('$lib/api', () => ({ apiPost: vi.fn() }));
beforeEach(() => vi.clearAllMocks());

const statements: SqlStatement[] = [{ sql: "SELECT 'a;b'", start_offset: 0, end_offset: 12 }];
function deferred() {
    let resolve!: (value: SqlStatement[]) => void;
    let reject!: (error: Error) => void;
    const promise = new Promise<SqlStatement[]>((r, j) => { resolve = r; reject = j; });
    return { promise, resolve, reject };
}

it('sends original SQL to the backend without splitting, regenerating or escaping it', async () => {
    vi.mocked(apiPost).mockResolvedValue({ version: 1, dialect: 'duckdb', statements });
    const source = "-- comment;\nSELECT $$😀;a$$; SELECT 'it''s;b'";
    expect(await parseSqlScript(source)).toEqual(statements);
    expect(apiPost).toHaveBeenCalledWith('/api/v1/sql/parse', { sql: source });
});

it('deduplicates a pending check and reuses only the exact confirmed source', async () => {
    const response = deferred(); const parse = vi.fn().mockReturnValue(response.promise);
    const analysis = createSqlScriptAnalysis(parse);
    const first = analysis.analyze('a'); const second = analysis.analyze('a');
    expect(analysis.get('a')).toBeNull(); expect(parse).toHaveBeenCalledOnce();
    response.resolve(statements); await Promise.all([first, second]);
    expect(analysis.get('a')).toEqual(statements); expect(analysis.get('a ')).toBeNull();
    expect(await analysis.analyze('a')).toEqual(statements); expect(parse).toHaveBeenCalledOnce();
});

it('an older response cannot replace the newer draft analysis', async () => {
    const old = deferred(); const fresh = deferred();
    const analysis = createSqlScriptAnalysis(vi.fn().mockReturnValueOnce(old.promise).mockReturnValueOnce(fresh.promise));
    const oldCheck = analysis.analyze('old'); const newCheck = analysis.analyze('fresh');
    fresh.resolve(statements); await newCheck; old.resolve([]); await oldCheck;
    expect(analysis.get('fresh')).toEqual(statements); expect(analysis.get('old')).toBeNull();
});

it('a late failure does not replace a newer successful check or its status', async () => {
    const old = deferred();
    const analysis = createSqlScriptAnalysis(vi.fn().mockReturnValueOnce(old.promise).mockResolvedValueOnce(statements));
    const check = analysis.analyze('old').catch(() => {});
    await analysis.analyze('fresh'); old.reject(new Error('offline')); await check;
    expect(analysis.error('fresh')).toBeNull(); expect(analysis.error('old')).toBeNull();
    expect(analysis.get('fresh')).toEqual(statements);
});

it('shows failure only for that source, publishes no count and permits retry', async () => {
    const parse = vi.fn().mockRejectedValueOnce(new Error('Invalid SQL')).mockResolvedValueOnce(statements);
    const analysis = createSqlScriptAnalysis(parse);
    await expect(analysis.analyze('bad')).rejects.toThrow('Invalid SQL');
    expect(analysis.get('bad')).toBeNull(); expect(analysis.error('bad')).toBe('Invalid SQL');
    expect(analysis.error('changed')).toBeNull();
    await analysis.analyze('bad'); expect(analysis.error('bad')).toBeNull();
    expect(analysis.get('bad')).toEqual(statements);
});

it('does not keep an unbounded cache of SQL drafts', async () => {
    const parse = vi.fn().mockResolvedValue(statements); const analysis = createSqlScriptAnalysis(parse);
    await analysis.analyze('a'); await analysis.analyze('b');
    expect(analysis.get('a')).toBeNull(); await analysis.analyze('a');
    expect(parse).toHaveBeenCalledTimes(3);
});

it('an empty editor confirms zero statements without sending SQL to the server', async () => {
    const parse = vi.fn(); const analysis = createSqlScriptAnalysis(parse);
    expect(await analysis.analyze('')).toEqual([]); expect(analysis.get('')).toEqual([]);
    expect(parse).not.toHaveBeenCalled();
});

it('reconstructs panels with a separator outside trailing line comments', () => {
    expect(joinSqlStatements(['SELECT 1 -- trailing;', 'SELECT 2'])).toBe('SELECT 1 -- trailing;\n;\n\nSELECT 2');
    expect(joinSqlStatements([])).toBe('');
});
