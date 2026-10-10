import { expect, it, vi } from 'vitest';
import type { DashboardLayout, InferenceResult } from '$lib/types';
import { requireSqlExecution, recomposeSqlRun, completeSqlRun, type BoundExecResult } from './sqlExecution';

const definition = { version: 1 as const, dashboard_id: 'd', revision: `sql-definition-v1:${'a'.repeat(64)}` };
const proof = `fixture.${'a'.repeat(64)}`;
function result(id = 'a'): BoundExecResult {
    return { panel_id: id, inference_result: { fallback_applied: false } as InferenceResult,
        data: [{ value: 42 }], execution_reference: { version: 1, panel_id: id, definition: { ...definition } },
        execution_receipt: proof, query_executed: true };
}
function layout(): DashboardLayout {
    return { rows: [{ panels: [{ panel_id: 'a', inference_result: result().inference_result,
        data: [], final_col_span: 12, col_offset: 0, row_index: 0 }] }] };
}

it('accepts a compatible execution and retains data without matching by SQL or order', () => {
    expect(requireSqlExecution(result(), definition, 'a')).toEqual(result());
});

it.each(['missing', 'version', 'panel', 'owner', 'revision', 'data', 'proof', 'outcome'])('rejects %s execution provenance', field => {
    const value = result();
    if (field === 'missing') delete (value as Partial<BoundExecResult>).execution_reference;
    if (field === 'version') value.execution_reference.version = 2 as 1;
    if (field === 'panel') value.execution_reference.panel_id = 'b';
    if (field === 'owner') value.execution_reference.definition.dashboard_id = 'other';
    if (field === 'revision') value.execution_reference.definition.revision = `sql-definition-v1:${'b'.repeat(64)}`;
    if (field === 'data') value.data = null as unknown as [];
    if (field === 'proof') value.execution_receipt = 'bad';
    if (field === 'outcome') value.query_executed = null as unknown as boolean;
    expect(() => requireSqlExecution(value, definition, 'a')).toThrow('Reload');
});

it('composes the exact definition and restores data only by validated panel ID', async () => {
    const post = vi.fn().mockResolvedValue({ ...layout(), definition, completion_receipt: proof });
    const response = await recomposeSqlRun([result()], definition, post);
    expect(post).toHaveBeenCalledWith('/api/v1/dashboards/d/sql-script/compose', {
        definition, panels: [{ panel_id: 'a', inference_result: result().inference_result,
            execution_reference: result().execution_reference, execution_receipt: proof }],
    });
    expect(response.layout.rows[0].panels[0].data).toEqual([{ value: 42 }]);
    expect(response.completionReceipt).toBe(proof);
});

it.each(['definition', 'missing', 'extra', 'duplicate', 'malformed'])('rejects a %s composition receipt', async field => {
    const response = { ...layout(), definition: { ...definition }, completion_receipt: proof };
    if (field === 'definition') response.definition.revision = `sql-definition-v1:${'b'.repeat(64)}`;
    if (field === 'missing') response.rows = [];
    if (field === 'extra') response.rows[0].panels[0].panel_id = 'unknown';
    if (field === 'duplicate') response.rows[0].panels.push(response.rows[0].panels[0]);
    if (field === 'malformed') response.rows = null as unknown as [];
    await expect(recomposeSqlRun([result()], definition, vi.fn().mockResolvedValue(response))).rejects.toThrow('Reload');
});

it('verifies empty dashboard composition instead of skipping its definition check', async () => {
    const post = vi.fn().mockResolvedValue({ rows: [], definition, completion_receipt: null });
    expect(await recomposeSqlRun([], definition, post)).toEqual({ layout: { rows: [] }, completionReceipt: null });
    expect(post).toHaveBeenCalledTimes(1);
});

it('rejects mixed results before contacting composition', async () => {
    const post = vi.fn(); const stale = result('b');
    stale.execution_reference.definition.revision = `sql-definition-v1:${'b'.repeat(64)}`;
    await expect(recomposeSqlRun([result(), stale], definition, post)).rejects.toThrow('Reload');
    expect(post).not.toHaveBeenCalled();
});

it('keeps fallback controls visible without claiming an executed Run', async () => {
    const fallback = { ...result(), query_executed: false };
    const response = await recomposeSqlRun([fallback], definition,
        vi.fn().mockResolvedValue({ ...layout(), definition, completion_receipt: null }));
    expect(response.completionReceipt).toBeNull(); expect(response.layout.rows).toHaveLength(1);
    await expect(recomposeSqlRun([fallback], definition,
        vi.fn().mockResolvedValue({ ...layout(), definition, completion_receipt: proof }))).rejects.toThrow('completion');
});

it('records only the server timestamp and exact source after verifying the acknowledgement', async () => {
    const post = vi.fn().mockResolvedValue({ definition, last_run_at: '2026-10-09T12:00:00.123456Z', last_run_sql: 'SELECT 1' });
    expect(await completeSqlRun(proof, definition, 'SELECT 1', post)).toEqual({
        lastRunAt: '2026-10-09T12:00:00.123456Z', lastRunSql: 'SELECT 1' });
    expect(post).toHaveBeenCalledWith('/api/v1/dashboards/d/sql-script/complete', {
        definition, completion_receipt: proof });
});

it.each(['definition', 'source', 'timestamp'])('rejects an incompatible %s success acknowledgement', async field => {
    const response = { definition, last_run_at: '2026-10-09T12:00:00Z', last_run_sql: 'SELECT 1' };
    if (field === 'definition') response.definition = { ...definition, dashboard_id: 'other' };
    if (field === 'source') response.last_run_sql = 'SELECT 2';
    if (field === 'timestamp') response.last_run_at = '2026-10-09T12:00:00';
    await expect(completeSqlRun(proof, definition, 'SELECT 1', vi.fn().mockResolvedValue(response))).rejects.toThrow('acknowledgement');
});
