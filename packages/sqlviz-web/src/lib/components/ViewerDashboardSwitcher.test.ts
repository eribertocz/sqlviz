import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/svelte';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import ViewerDashboardSwitcher from './ViewerDashboardSwitcher.svelte';

afterEach(() => { cleanup(); vi.restoreAllMocks(); });
beforeEach(() => {
    // Floating UI needs a nonzero viewport; jsdom provides no layout geometry.
    vi.spyOn(Element.prototype, 'clientWidth', 'get').mockReturnValue(1024);
    vi.spyOn(Element.prototype, 'clientHeight', 'get').mockReturnValue(768);
    vi.spyOn(Element.prototype, 'getBoundingClientRect').mockReturnValue({
        x: 20, y: 20, width: 400, height: 40, top: 20, left: 20, right: 420, bottom: 60,
        toJSON: () => ({}),
    });
});
const dashboards = [
    { id: 'one', name: 'Revenue', folderName: 'Finance' },
    { id: 'two', name: 'Revenue', folderName: 'Operations' },
];

it('searches by group and selects by ID even with duplicate names', async () => {
    const onSelect = vi.fn();
    render(ViewerDashboardSwitcher, { dashboards, activeId: 'one', onSelect });
    await fireEvent.click(screen.getByRole('button', { name: 'Switch dashboard: Revenue' }));
    const search = await screen.findByLabelText('Search shared dashboards');
    expect(screen.getByRole('combobox', { name: 'Search shared dashboards', hidden: true })).toBe(search);
    await waitFor(() => expect(document.activeElement).toBe(search));
    await fireEvent.input(search, { target: { value: 'Operations' } });
    await fireEvent.click(screen.getByText('Operations').closest('[role="option"]')!);
    expect(onSelect).toHaveBeenCalledWith('two');
    await waitFor(() => expect(screen.queryByRole('combobox', { hidden: true })).toBeNull());
});

it('Escape dismisses the search and returns focus without changing dashboard', async () => {
    const onSelect = vi.fn();
    render(ViewerDashboardSwitcher, { dashboards, activeId: 'one', onSelect });
    const trigger = screen.getByRole('button', { name: 'Switch dashboard: Revenue' });
    await fireEvent.click(trigger);
    const search = await screen.findByLabelText('Search shared dashboards');
    await fireEvent.keyDown(search, { key: 'Escape' });
    await waitFor(() => expect(document.activeElement).toBe(trigger));
    expect(onSelect).not.toHaveBeenCalled();
});

it('allows searching while loading but prevents another dashboard change', async () => {
    const onSelect = vi.fn();
    render(ViewerDashboardSwitcher, { dashboards, activeId: 'one', loading: true, onSelect });
    const next = screen.getByRole('button', { name: 'Next dashboard' }) as HTMLButtonElement;
    expect(next.disabled).toBe(true);
    await fireEvent.click(screen.getByRole('button', { name: 'Switch dashboard: Revenue' }));
    await screen.findByLabelText('Search shared dashboards');
    expect(screen.getAllByRole('option', { hidden: true }).every(option => option.getAttribute('aria-disabled') === 'true')).toBe(true);
    await fireEvent.click(next);
    expect(onSelect).not.toHaveBeenCalled();
});

it('shows the current title with no switching controls for a single dashboard', () => {
    render(ViewerDashboardSwitcher, { dashboards: dashboards.slice(0, 1), activeId: 'one', onSelect: vi.fn() });
    expect(screen.getByText('Revenue')).toBeTruthy();
    expect(screen.queryByRole('button')).toBeNull();
});
