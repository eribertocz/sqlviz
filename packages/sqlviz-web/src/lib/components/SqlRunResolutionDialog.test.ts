import { cleanup, fireEvent, render, waitFor } from '@testing-library/svelte';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import SqlRunResolutionDialog from './SqlRunResolutionDialog.svelte';
import { selectRunPanel, type SqlRunResolution } from '$lib/sql/sqlRunResolution';

beforeEach(() => vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] }));
afterEach(async () => {
    cleanup();
    // Bits UI restores body scrolling after releasing the last modal lock.
    await vi.runAllTimersAsync();
    vi.useRealTimers();
});
function draft(): SqlRunResolution {
    return { source: 'SELECT 2; SELECT 1', statements: [
        { sql: 'SELECT 2', start_offset: 0, end_offset: 8 }, { sql: 'SELECT 1', start_offset: 10, end_offset: 18 },
    ], panels: [{ id: 'a', label: 'Margin', sql: 'SELECT 1' }, { id: 'b', label: 'Revenue', sql: 'SELECT 2' }], choices: [] };
}

it('keeps unresolved associations explicit, focuses the first query and supports keyboard cancellation', async () => {
    const onCancel = vi.fn(); const onChoose = vi.fn(); const onConfirm = vi.fn();
    const screen = render(SqlRunResolutionDialog, { resolution: draft(), onCancel, onChoose, onConfirm });
    const first = await screen.findByLabelText('Query 1');
    await waitFor(() => expect(document.activeElement).toBe(first));
    expect(screen.getByRole('button', { name: 'Run dashboard' }).hasAttribute('disabled')).toBe(true);
    await fireEvent.change(first, { target: { value: 'keep:b' } });
    expect(onChoose).toHaveBeenCalledWith(0, 'b'); expect(onConfirm).not.toHaveBeenCalled();
    await fireEvent.keyDown(first, { key: 'Escape' });
    expect(onCancel).toHaveBeenCalled();
});

it('shows previous SQL, prevents duplicate targets and allows confirmation only with full coverage', async () => {
    const onConfirm = vi.fn();
    const partial = selectRunPanel(draft(), 0, 'b', () => 'new');
    const screen = render(SqlRunResolutionDialog, { resolution: partial, onChoose: vi.fn(), onCancel: vi.fn(), onConfirm });
    await screen.findByRole('dialog');
    const second = screen.getByLabelText('Query 2') as HTMLSelectElement;
    expect(second.querySelector<HTMLOptionElement>('option[value="keep:b"]')?.disabled).toBe(true);
    expect(screen.getByText('Previous SQL · Revenue')).toBeTruthy();
    await screen.rerender({ resolution: selectRunPanel(partial, 1, 'a', () => 'new') });
    const confirm = screen.getByRole('button', { name: 'Run dashboard' });
    expect(confirm.hasAttribute('disabled')).toBe(false);
    await fireEvent.click(confirm); expect(onConfirm).toHaveBeenCalledOnce();
});

it('returns focus after confirmation finishes and the Run trigger becomes enabled', async () => {
    const trigger = document.createElement('button');
    trigger.setAttribute('data-sql-run-trigger', ''); trigger.disabled = true;
    document.body.append(trigger);
    try {
        const complete = selectRunPanel(selectRunPanel(draft(), 0, 'b', () => 'new'), 1, 'a', () => 'new');
        const screen = render(SqlRunResolutionDialog, { resolution: complete, onChoose: vi.fn(), onCancel: vi.fn(),
            onConfirm: async () => { await screen.rerender({ resolution: null }); trigger.disabled = false; } });
        await screen.findByRole('dialog');
        await fireEvent.click(screen.getByRole('button', { name: 'Run dashboard' }));
        await waitFor(() => expect(document.activeElement).toBe(trigger));
    } finally { trigger.remove(); }
});
