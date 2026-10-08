import { cleanup, fireEvent, render } from '@testing-library/svelte';
import { afterEach, expect, it, vi } from 'vitest';
import type { InferenceResult } from '$lib/types';
import ChartSelectorPanel from './ChartSelectorPanel.svelte';

afterEach(cleanup);

function result(winner: string, engine: string): InferenceResult {
    return {
        chart_winner: winner, chart_engine_winner: engine,
        chart_alternatives: [
            { chart: 'bar', raw_score: 1, pct: engine === 'bar' ? 0.8 : 0.2 },
            { chart: 'line', raw_score: 1, pct: engine === 'line' ? 0.8 : 0.2 },
        ],
    } as InferenceResult;
}

it('uses the new panel result for selection, recommendation and scores', async () => {
    const props = { result: result('bar', 'bar'), onSelect: vi.fn(), onClose: vi.fn() };
    const screen = render(ChartSelectorPanel, props);
    expect((screen.getByRole('radio', { name: /Bar/ }) as HTMLInputElement).checked).toBe(true);
    await screen.rerender({ ...props, result: result('line', 'line') });
    expect((screen.getByRole('radio', { name: /Line/ }) as HTMLInputElement).checked).toBe(true);
    expect(screen.getByRole('radio', { name: /Line/ }).closest('label')?.textContent).toContain('80%');
    expect(screen.queryByRole('button', { name: 'Reset to auto' })).toBeNull();
});

it('shows a manual selection immediately and accepts the next persisted result', async () => {
    const props = { result: result('bar', 'bar'), onSelect: vi.fn(), onClose: vi.fn() };
    const screen = render(ChartSelectorPanel, props);
    await fireEvent.click(screen.getByRole('radio', { name: /Line/ }));
    expect(props.onSelect).toHaveBeenCalledWith('line');
    expect((screen.getByRole('radio', { name: /Line/ }) as HTMLInputElement).checked).toBe(true);
    await screen.rerender({ ...props, result: result('bar', 'line') });
    expect((screen.getByRole('radio', { name: /Bar/ }) as HTMLInputElement).checked).toBe(true);
    await fireEvent.click(screen.getByRole('button', { name: 'Reset to auto' }));
    expect(props.onSelect).toHaveBeenLastCalledWith('line');
});
