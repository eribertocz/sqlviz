import { describe, expect, it, vi } from 'vitest';
import type { ExecResult } from '$lib/api';
import type { FilterControl, DashboardLayout } from '$lib/types';
import { filterSummary } from './filterContext';
import { createFilterRuntime, patchFilterResults } from './filterRuntime.svelte';

const control = (variable: string, control_type: FilterControl['control_type'] = 'numeric'): FilterControl => ({
    variable, control_type, label: variable, column_name: variable, column_type: 'INTEGER', scope: 'global',
});
const panel = (id: string, variables: string[]): ExecResult => ({ panel_id: id, data: [{ amount: 100 }],
    inference_result: { filter_controls: variables.map(v => control(v)) } as ExecResult['inference_result'],
});
function setup() {
    let scope = 'dashboard-A';
    let results = [panel('p-A', ['a']), panel('p-B', ['b']), panel('p-C', [])];
    let values: Record<string, unknown> = {};
    const execute = vi.fn(async (id: string, variables: Record<string, unknown>) => ({
        ...results.find(p => p.panel_id === id)!, data: [variables],
    }));
    const commit = vi.fn((next: ExecResult[], applied: Record<string, unknown>) => { results = next; values = applied; });
    const runtime = createFilterRuntime({ getScope: () => scope, getResults: () => results, getValues: () => values, execute, commit });
    return { runtime, execute, commit, get results() { return results; }, get values() { return values; },
        navigate() { scope = 'dashboard-B'; runtime.reset(); } };
}

describe('confirmed filter updates', () => {
    it('applies every variable in a preset and preserves unaffected results', async () => {
        const s = setup(); const unaffected = s.results[2];
        expect(await s.runtime.apply({ a: 0, b: false })).toBe(true);
        expect(s.execute.mock.calls).toEqual([['p-A', { a: 0 }], ['p-B', { b: false }]]);
        expect(s.commit).toHaveBeenCalledTimes(1);
        expect(s.results[2]).toBe(unaffected);
        expect(s.values).toEqual({ a: 0, b: false });
    });
    it('keeps the entire confirmed set when a later panel fails', async () => {
        const s = setup(); const original = s.results;
        s.execute.mockRejectedValueOnce(new Error('Connection unavailable'));
        expect(await s.runtime.apply({ a: 1, b: 2 })).toBe(false);
        expect(s.commit).not.toHaveBeenCalled();
        expect(s.results).toBe(original); expect(s.values).toEqual({});
        expect(s.runtime.error).toBe('Connection unavailable');
        expect(s.runtime.busy).toBe(false);
    });
    it('does not publish a successful first panel if the second fails', async () => {
        const s = setup();
        s.execute.mockResolvedValueOnce({ ...s.results[0], data: [{ amount: 900 }] })
            .mockRejectedValueOnce(new Error('Second panel failed'));
        await s.runtime.apply({ a: 1, b: 2 });
        expect(s.commit).not.toHaveBeenCalled(); expect(s.results[0].data).toEqual([{ amount: 100 }]);
    });
    it('keeps applied criteria unchanged while a request is pending', async () => {
        const s = setup(); let finish!: (result: ExecResult) => void;
        s.execute.mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
        const operation = s.runtime.apply({ a: 12 });
        expect(s.runtime.busy).toBe(true); expect(s.values).toEqual({});
        expect(s.runtime.pending).toEqual({ a: 12 });
        finish({ ...s.results[0], data: [] }); await operation;
        expect(s.values).toEqual({ a: 12 }); expect(s.results[0].data).toEqual([]);
    });
    it('only publishes the latest request even when the older one finishes first', async () => {
        const s = setup(); let finish!: (result: ExecResult) => void;
        s.execute.mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
        const old = s.runtime.apply({ a: 1 });
        const recent = s.runtime.apply({ a: 2 });
        finish({ ...s.results[0], data: [{ a: 1 }] });
        await Promise.all([old, recent]);
        expect(s.commit).toHaveBeenCalledTimes(1); expect(s.values).toEqual({ a: 2 });
    });
    it('discards pending results when navigating or disposing', async () => {
        const s = setup(); let finish!: (result: ExecResult) => void;
        s.execute.mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
        const operation = s.runtime.apply({ a: 1 });
        s.navigate(); finish(s.results[0]);
        expect(await operation).toBe(false); expect(s.commit).not.toHaveBeenCalled();
        expect(s.runtime.busy).toBe(false);
    });
    it('handles an access denial from an older request after a newer update', async () => {
        const results = [panel('p-A', ['a'])];
        let failOld!: (error: Error) => void;
        const execute = vi.fn(async () => results[0]);
        execute.mockImplementationOnce(() => new Promise((_, reject) => { failOld = reject; }));
        const onAccessFailure = vi.fn(() => true);
        const runtime = createFilterRuntime({ getScope: () => 'same-session', getResults: () => results,
            getValues: () => ({}), execute, commit: vi.fn(), onAccessFailure });
        const old = runtime.apply({ a: 1 }); await runtime.apply({ a: 2 });
        const denial = new Error('Revoked'); failOld(denial); await old;
        expect(onAccessFailure).toHaveBeenCalledWith(denial);
    });
    it('clears omitted preset values and executes all changed bindings', async () => {
        const s = setup(); await s.runtime.apply({ a: 1, b: 2 }); s.execute.mockClear();
        await s.runtime.apply({ a: 3 });
        expect(s.execute.mock.calls).toEqual([['p-A', { a: 3 }], ['p-B', { b: '' }]]);
    });
    it('rejects obsolete preset keys and inverted ranges before execution', async () => {
        const s = setup();
        expect(await s.runtime.apply({ obsolete: 1 })).toBe(false);
        s.results[0].inference_result.filter_controls = [control('a,b', 'range_slider')];
        expect(await s.runtime.apply({ a: 9, b: 1 })).toBe(false);
        expect(s.execute).not.toHaveBeenCalled(); expect(s.commit).not.toHaveBeenCalled();
    });
    it('counts a range once and preserves false and zero as active criteria', () => {
        expect(filterSummary([control('a'), control('b'), control('start,end', 'range_slider')],
            { a: false, b: 0, start: 1, end: 2 })).toHaveLength(3);
    });
    it('updates data without changing the panel frame', () => {
        const result = panel('p-A', []);
        const ir = { ...result.inference_result, col_span: 6, row_span: 1, panel_height_px: 360 };
        const layout = { rows: [{ panels: [{ panel_id: 'p-A', inference_result: ir, final_col_span: 6 }] }] } as DashboardLayout;
        const patched = patchFilterResults(layout, [{ ...result, inference_result: { ...ir, col_span: 12, panel_height_px: 800 }, data: [] }]);
        expect(patched.rows[0].panels[0].inference_result.panel_height_px).toBe(360);
        expect(patched.rows[0].panels[0].final_col_span).toBe(6);
        expect(patched.rows[0].panels[0].data).toEqual([]);
    });
});
