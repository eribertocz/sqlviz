import { cleanup, fireEvent, render, waitFor } from '@testing-library/svelte';
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

it('keeps the confirmed selection while saving and accepts the next persisted result', async () => {
    let finish!: (value: { saved: boolean; error: string | null }) => void;
    const props = { result: result('bar', 'bar'), onSelect: vi.fn(() => new Promise<{ saved: boolean; error: string | null }>(r => { finish = r; })), onClose: vi.fn() };
    const screen = render(ChartSelectorPanel, props);
    await fireEvent.click(screen.getByRole('radio', { name: /Line/ }));
    expect(props.onSelect).toHaveBeenCalledWith('line', false);
    expect((screen.getByRole('radio', { name: /Line/ }) as HTMLInputElement).checked).toBe(false);
    expect((screen.getByRole('radio', { name: /Bar/ }) as HTMLInputElement).checked).toBe(true);
    expect((screen.getByRole('radio', { name: /Line/ }) as HTMLInputElement).disabled).toBe(true);
    expect(screen.getByRole('status').textContent).toContain('Saving');
    finish({ saved: true, error: null });
    await waitFor(() => expect(screen.queryByRole('status')).toBeNull());
    await screen.rerender({ ...props, result: { ...result('bar', 'line'), chart_user_override: 'bar' } });
    expect((screen.getByRole('radio', { name: /Bar/ }) as HTMLInputElement).checked).toBe(true);
    await fireEvent.click(screen.getByRole('button', { name: 'Reset to auto' }));
    expect(props.onSelect).toHaveBeenLastCalledWith(null, false);
});

it('keeps a rejected choice available for retry without marking it saved', async () => {
    const onSelect = vi.fn().mockResolvedValueOnce({ saved: false, error: 'Conflict; retry.' })
        .mockResolvedValueOnce({ saved: true, error: null });
    const screen = render(ChartSelectorPanel, { result: result('bar', 'bar'), onSelect, onClose: vi.fn() });
    await fireEvent.click(screen.getByRole('radio', { name: /Line/ }));
    await waitFor(() => expect(screen.getByRole('alert').textContent).toContain('Conflict'));
    expect((screen.getByRole('radio', { name: /Bar/ }) as HTMLInputElement).checked).toBe(true);
    await fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
    expect(onSelect).toHaveBeenLastCalledWith('line', false);
});

it('retries only refresh when the project choice was already saved', async () => {
    const onSelect = vi.fn().mockResolvedValueOnce({ saved: true, error: 'Saved; refresh failed.' })
        .mockResolvedValueOnce({ saved: true, error: null });
    const screen = render(ChartSelectorPanel, { result: result('bar', 'bar'), onSelect, onClose: vi.fn() });
    await fireEvent.click(screen.getByRole('radio', { name: /Line/ }));
    await waitFor(() => expect(screen.getByRole('button', { name: 'Retry refresh' })).toBeTruthy());
    await fireEvent.click(screen.getByRole('button', { name: 'Retry refresh' }));
    expect(onSelect).toHaveBeenLastCalledWith('line', true);
});

it('a manual choice matching the engine still offers a real reset', async () => {
    const onSelect = vi.fn().mockResolvedValue({ saved: true, error: null });
    const screen = render(ChartSelectorPanel, { result: { ...result('bar', 'bar'), chart_user_override: 'bar' }, onSelect, onClose: vi.fn() });
    expect(screen.getByRole('radio', { name: /Bar/ }).closest('label')?.textContent).toContain('Manual');
    await fireEvent.click(screen.getByRole('button', { name: 'Reset to auto' }));
    expect(onSelect).toHaveBeenCalledWith(null, false);
});

it('shows a persisted choice absent from the new alternatives without inventing its score', () => {
    const screen = render(ChartSelectorPanel, { result: { ...result('pie', 'bar'), chart_user_override: 'pie' }, onSelect: vi.fn(), onClose: vi.fn() });
    const choice = screen.getByRole('radio', { name: /Pie/ }) as HTMLInputElement;
    expect(choice.checked).toBe(true);
    expect(choice.closest('label')?.textContent).toContain('Manual');
    expect(choice.closest('label')?.textContent).not.toContain('%');
});
