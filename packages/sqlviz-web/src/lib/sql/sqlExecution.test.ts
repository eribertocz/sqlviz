import { expect, it, vi } from 'vitest';
import type { DashboardLayout, InferenceResult } from '$lib/types';
import { requireSqlExecution, recomposeSqlRun, type BoundExecResult } from './sqlExecution';

const definition = { version: 1 as const, dashboard_id: 'd', revision: `sql-definition-v1:${'a'.repeat(64)}` };
function result(id = 'a'): BoundExecResult {
    return { panel_id: id, inference_result: { fallback_applied: false } as InferenceResult,
        data: [{ value: 42 }], execution_reference: { version: 1, panel_id: id, definition: { ...definition } } };
}
function layout(): DashboardLayout {
    return { rows: [{ panels: [{ panel_id: 'a', inference_result: result().inference_result,
        data: [], final_col_span: 12, col_offset: 0, row_index: 0 }] }] };
}

it('accepts a compatible execution and retains data without matching by SQL or order', () => {
    expect(requireSqlExecution(result(), definition, 'a')).toEqual(result());
});

it.each(['missing', 'version', 'panel', 'owner', 'revision', 'data'])('rejects %s execution provenance', field => {
    const value = result();
    if (field === 'missing') delete (value as Partial<BoundExecResult>).execution_reference;
    if (field === 'version') value.execution_reference.version = 2 as 1;
    if (field === 'panel') value.execution_reference.panel_id = 'b';
    if (field === 'owner') value.execution_reference.definition.dashboard_id = 'other';
    if (field === 'revision') value.execution_reference.definition.revision = `sql-definition-v1:${'b'.repeat(64)}`;
    if (field === 'data') value.data = null as unknown as [];
    expect(() => requireSqlExecution(value, definition, 'a')).toThrow('Reload');
});

it('composes the exact definition and restores data only by validated panel ID', async () => {
    const post = vi.fn().mockResolvedValue({ ...layout(), definition });
    const response = await recomposeSqlRun([result()], definition, post);
    expect(post).toHaveBeenCalledWith('/api/v1/dashboards/d/sql-script/compose', {
        definition, panels: [{ panel_id: 'a', inference_result: result().inference_result,
            execution_reference: result().execution_reference }],
    });
    expect(response.rows[0].panels[0].data).toEqual([{ value: 42 }]);
});

it.each(['definition', 'missing', 'extra', 'duplicate', 'malformed'])('rejects a %s composition receipt', async field => {
    const response = { ...layout(), definition: { ...definition } };
    if (field === 'definition') response.definition.revision = `sql-definition-v1:${'b'.repeat(64)}`;
    if (field === 'missing') response.rows = [];
    if (field === 'extra') response.rows[0].panels[0].panel_id = 'unknown';
    if (field === 'duplicate') response.rows[0].panels.push(response.rows[0].panels[0]);
    if (field === 'malformed') response.rows = null as unknown as [];
    await expect(recomposeSqlRun([result()], definition, vi.fn().mockResolvedValue(response))).rejects.toThrow('Reload');
});

it('verifies empty dashboard composition instead of skipping its definition check', async () => {
    const post = vi.fn().mockResolvedValue({ rows: [], definition });
    expect(await recomposeSqlRun([], definition, post)).toEqual({ rows: [] });
    expect(post).toHaveBeenCalledTimes(1);
});

it('rejects mixed results before contacting composition', async () => {
    const post = vi.fn(); const stale = result('b');
    stale.execution_reference.definition.revision = `sql-definition-v1:${'b'.repeat(64)}`;
    await expect(recomposeSqlRun([result(), stale], definition, post)).rejects.toThrow('Reload');
    expect(post).not.toHaveBeenCalled();
});
