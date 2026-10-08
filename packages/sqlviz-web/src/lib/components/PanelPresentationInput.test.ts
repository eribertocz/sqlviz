import { cleanup, fireEvent, render, waitFor } from '@testing-library/svelte';
import { afterEach, expect, it, vi } from 'vitest';
import { dashboardStore } from '$lib/stores/dashboardStore.svelte';
import PanelPresentationInput from './PanelPresentationInput.svelte';

vi.mock('$lib/stores/dashboardStore.svelte', () => ({ dashboardStore: { setViewOverride: vi.fn() } }));
afterEach(() => { cleanup(); vi.resetAllMocks(); });

const props = { panelId: 'p', field: 'title' as const, label: 'Panel title',
    value: 'Confirmed', placeholder: 'Panel title' };

it('keeps the failed draft, exposes an accessible error and retries the exact text', async () => {
    vi.mocked(dashboardStore.setViewOverride).mockResolvedValueOnce('Could not save.');
    vi.mocked(dashboardStore.setViewOverride).mockResolvedValueOnce(null);
    const screen = render(PanelPresentationInput, props);
    const input = screen.getByRole('textbox', { name: 'Panel title' }) as HTMLInputElement;
    await fireEvent.input(input, { target: { value: '  Nueva · ñ  ' } });
    await fireEvent.blur(input);
    await waitFor(() => expect(screen.getByRole('alert').textContent).toContain('Could not save'));
    expect(input.value).toBe('  Nueva · ñ  ');
    expect(input.getAttribute('aria-invalid')).toBe('true');
    await fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
    await waitFor(() => expect(dashboardStore.setViewOverride).toHaveBeenCalledTimes(2));
    expect(dashboardStore.setViewOverride).toHaveBeenLastCalledWith('p', 'title', '  Nueva · ñ  ');
    await waitFor(() => expect(screen.queryByRole('alert')).toBeNull());
    expect(document.activeElement).toBe(input);
});

it('disables the pending input and avoids duplicate Enter/blur saves', async () => {
    let finish!: (value: null) => void;
    vi.mocked(dashboardStore.setViewOverride).mockImplementationOnce(() => new Promise(r => { finish = r; }));
    const screen = render(PanelPresentationInput, props);
    const input = screen.getByRole('textbox') as HTMLInputElement;
    await fireEvent.input(input, { target: { value: 'New' } });
    await fireEvent.keyDown(input, { key: 'Enter' });
    await fireEvent.blur(input);
    expect(input.disabled).toBe(true);
    expect(screen.getByRole('status').textContent).toContain('Saving');
    expect(dashboardStore.setViewOverride).toHaveBeenCalledTimes(1);
    finish(null);
    await waitFor(() => expect(input.disabled).toBe(false));
});

it('keeps the inline editor open on rejection and closes it only after confirmation', async () => {
    const onSaved = vi.fn();
    vi.mocked(dashboardStore.setViewOverride).mockResolvedValueOnce('Synthetic conflict');
    vi.mocked(dashboardStore.setViewOverride).mockResolvedValueOnce(null);
    const screen = render(PanelPresentationInput, { ...props, compact: true, autofocus: true, onSaved });
    const input = screen.getByRole('textbox') as HTMLInputElement;
    await waitFor(() => expect(document.activeElement).toBe(input));
    await fireEvent.input(input, { target: { value: 'Draft' } });
    await fireEvent.keyDown(input, { key: 'Enter' });
    await waitFor(() => expect(screen.getByRole('alert').textContent).toContain('Synthetic conflict'));
    expect(onSaved).not.toHaveBeenCalled();
    expect(input.value).toBe('Draft');
    await fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
    await waitFor(() => expect(onSaved).toHaveBeenCalledTimes(1));
});

it('cancels an inline draft with Escape without persisting it', async () => {
    const onCancel = vi.fn();
    const screen = render(PanelPresentationInput, { ...props, compact: true, onCancel });
    const input = screen.getByRole('textbox');
    await fireEvent.input(input, { target: { value: 'Unsaved' } });
    await fireEvent.keyDown(input, { key: 'Escape' });
    await fireEvent.blur(input);
    expect(onCancel).toHaveBeenCalledTimes(1);
    expect(dashboardStore.setViewOverride).not.toHaveBeenCalled();
});
