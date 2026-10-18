import { expect, it, vi } from 'vitest';
import type { ExecResult } from '$lib/api';
import { fetchFilterDomains } from './filterDomains';

function results(): ExecResult[] {
    return ['first', 'second'].map(panel_id => ({ panel_id, data: [], inference_result: {
        filter_controls: [
            { variable: 'region', column_name: 'region', control_type: 'dropdown' },
            { variable: panel_id, column_name: 'amount', control_type: 'range_slider' },
        ],
    } } as unknown as ExecResult));
}

it('serializes domain requests, deduplicates bindings and preserves actual panel IDs', async () => {
    let active = 0, peak = 0;
    const fetch = vi.fn(async () => {
        active++; peak = Math.max(peak, active);
        await new Promise(resolve => setTimeout(resolve, 1));
        active--; return { values: ['North'] };
    });
    const domains = await fetchFilterDomains({ results: results(), isCurrent: () => true, fetch });
    expect(peak).toBe(1);
    expect(fetch.mock.calls).toEqual([
        ['first', 'region', 'distinct'], ['first', 'amount', 'range'], ['second', 'amount', 'range'],
    ]);
    expect(Object.keys(domains)).toEqual(['region', 'first', 'second']);
});

it('stops issuing queries and excludes the late domain when its view is abandoned', async () => {
    let current = true;
    const fetch = vi.fn(async () => { current = false; return { values: ['North'] }; });
    expect(await fetchFilterDomains({ results: results(), isCurrent: () => current, fetch })).toEqual({});
    expect(fetch).toHaveBeenCalledTimes(1);
});

it('keeps the manual fallback for an ordinary failure and loads remaining domains', async () => {
    const fetch = vi.fn().mockRejectedValueOnce(new Error('Source unavailable')).mockResolvedValue({ min: 0, max: 10 });
    const domains = await fetchFilterDomains({ results: results(), isCurrent: () => true, fetch });
    expect(domains).toEqual({ first: { min: 0, max: 10 }, second: { min: 0, max: 10 } });
    expect(fetch).toHaveBeenCalledTimes(3);
});

it('propagates an access failure even when the view was abandoned during its request', async () => {
    const denial = new Error('Access revoked');
    let current = true;
    const fetch = vi.fn(async () => { current = false; throw denial; });
    const onAccessFailure = vi.fn(() => true);
    await expect(fetchFilterDomains({ results: results(), isCurrent: () => current, fetch, onAccessFailure })).rejects.toBe(denial);
    expect(onAccessFailure).toHaveBeenCalledWith(denial);
    expect(fetch).toHaveBeenCalledTimes(1);
});
