import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/svelte';
import { afterEach, expect, it, vi } from 'vitest';
import FilterContext from './FilterContext.svelte';
import type { FilterControl } from '$lib/types';

afterEach(async () => {
    cleanup();
    // Finish Bits UI's deferred body scroll restoration before jsdom teardown.
    await new Promise(resolve => setTimeout(resolve, 40));
});
const controls: FilterControl[] = ['Amount', 'Limit'].map(label => ({ label, variable: label.toLowerCase(),
    control_type: 'numeric', column_name: label, column_type: 'INTEGER', scope: 'global' }));
const props = { dashboardId: 'filter-context-test', controls, values: { amount: 10 }, domains: {} };
const open = async () => fireEvent.click(screen.getByRole('button', { name: /^Dashboard filters:/ }));

it('edits a draft without requests and cancels back to the applied values', async () => {
    const onApply = vi.fn(async () => true); render(FilterContext, { ...props, onApply });
    await open();
    await fireEvent.input(await screen.findByLabelText('Amount'), { target: { value: '20' } });
    expect(onApply).not.toHaveBeenCalled();
    await fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    await waitFor(() => expect(screen.queryByLabelText('Amount')).toBeNull());
    await open(); expect((await screen.findByLabelText('Amount') as HTMLInputElement).value).toBe('10');
});
it('submits multiple edits together and returns focus to the context trigger', async () => {
    const onApply = vi.fn(async () => true); render(FilterContext, { ...props, onApply });
    const trigger = screen.getByRole('button', { name: /^Dashboard filters:/ });
    await open();
    await fireEvent.input(await screen.findByLabelText('Amount'), { target: { value: '0' } });
    await fireEvent.input(screen.getByLabelText('Limit'), { target: { value: '15' } });
    await fireEvent.click(screen.getByRole('button', { name: 'Apply filters' }));
    expect(onApply).toHaveBeenCalledWith({ amount: 0, limit: 15 });
    await waitFor(() => expect(document.activeElement).toBe(trigger));
});
it('keeps a failed draft open for retry', async () => {
    const onApply = vi.fn(async () => false); render(FilterContext, { ...props, onApply, error: 'Server unavailable' });
    await open(); await fireEvent.input(await screen.findByLabelText('Amount'), { target: { value: '20' } });
    await fireEvent.click(screen.getByRole('button', { name: 'Apply filters' }));
    expect(screen.getByRole('dialog', { name: 'Filters' })).toBeTruthy();
    expect((screen.getByLabelText('Amount') as HTMLInputElement).value).toBe('20');
    expect(screen.getByRole('alert').textContent).toContain('Previous charts and filters are unchanged');
});
it('Escape discards edits, restores focus and performs no queries', async () => {
    const onApply = vi.fn(async () => true); render(FilterContext, { ...props, onApply });
    const trigger = screen.getByRole('button', { name: /^Dashboard filters:/ }); await open();
    const input = await screen.findByLabelText('Amount');
    await fireEvent.input(input, { target: { value: '99' } }); await fireEvent.keyDown(input, { key: 'Escape' });
    await waitFor(() => expect(document.activeElement).toBe(trigger));
    expect(onApply).not.toHaveBeenCalled();
});
it('offers no inert context control for a dashboard without filters', () => {
    render(FilterContext, { ...props, controls: [], onApply: vi.fn() });
    expect(screen.queryByRole('button')).toBeNull();
});
