import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/svelte';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { uiStore } from '$lib/stores/uiStore.svelte';
import { editMode } from '$lib/stores/editMode';
import { legacySqlSnapshot } from '$lib/sql/sqlSnapshot.testFixtures';
import { dashboardStore } from '$lib/stores/dashboardStore.svelte';

vi.mock('$app/navigation', () => ({ goto: vi.fn() }));

import Page from './+page.svelte';

const dashboards = [
    { id: 'd1', name: 'Revenue', folder_id: 'f1', sort_order: 0, sql_content: '', last_run_at: null },
    { id: 'd2', name: 'Operations', folder_id: null, sort_order: 1, sql_content: '', last_run_at: null },
];

beforeEach(() => {
    localStorage.clear();
    uiStore.setSidebarCollapsed(true);
    uiStore.focusMode = false;
    editMode.set(true);
    vi.stubGlobal('fetch', vi.fn((url: string) => {
        const path = String(url);
        const snapshotDashboard = dashboards.find(d => path.endsWith(`/${d.id}/sql-script`));
        const body = path.endsWith('/auth/me') ? { status: 'ok', demo: false }
            : path.endsWith('/folders') ? [{ id: 'f1', name: 'Finance', sort_order: 0 }]
            : path.includes('/panels') ? []
            : path.endsWith('/dashboards') ? dashboards
            : snapshotDashboard ? legacySqlSnapshot(snapshotDashboard.id)
            : dashboards.find(d => path.endsWith(`/${d.id}`));
        if (!body) throw new Error(`Unexpected fetch in test: ${path}`);
        return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(body) } as Response);
    }));
});

afterEach(async () => {
    cleanup();
    uiStore.focusMode = false;
    uiStore.setSidebarCollapsed(true);
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
    // bits-ui defers body scroll restoration by 24 ms after dialog destruction.
    await new Promise(resolve => setTimeout(resolve, 30));
});

describe('/ workspace navigation', () => {
    it('hides navigation entirely, reopens it, then restores keyboard focus when closed', async () => {
        render(Page);
        await screen.findByRole('button', { name: 'Revenue' });
        const trigger = await screen.findByRole('button', { name: 'Show navigation' });
        expect(screen.queryByRole('navigation')).toBeNull();
        await fireEvent.click(trigger);
        expect(await screen.findByRole('navigation', { name: 'Dashboard explorer' })).toBeTruthy();
        await fireEvent.click(screen.getByRole('button', { name: 'Hide navigation' }));
        await waitFor(() => {
            expect(screen.queryByRole('navigation')).toBeNull();
            expect(document.activeElement).toBe(trigger);
        });
        expect(trigger.getAttribute('aria-expanded')).toBe('false');
        expect(localStorage.getItem('sqlviz-sidebar-collapsed')).toBe('1');
    });

    it('opens visible search and switches dashboards using keyboard selection', async () => {
        render(Page);
        await screen.findByRole('button', { name: 'Revenue' });
        await fireEvent.click(screen.getByRole('button', { name: 'Search dashboards and commands' }));
        const search = await screen.findByPlaceholderText(/Jump to a dashboard/);
        await fireEvent.input(search, { target: { value: 'Operations' } });
        await fireEvent.keyDown(search, { key: 'ArrowDown' });
        await fireEvent.keyDown(search, { key: 'Enter' });
        await waitFor(() => {
            expect(screen.queryByRole('dialog')).toBeNull();
            expect(screen.getByRole('button', { name: 'Operations' })).toBeTruthy();
        });
    });

    it('restores focus when a keyboard shortcut hides the docked explorer', async () => {
        render(Page);
        const trigger = await screen.findByRole('button', { name: 'Show navigation' });
        await fireEvent.keyDown(trigger, { key: 'b', ctrlKey: true });
        const dashboard = await screen.findByRole('button', { name: 'Operations' });
        dashboard.focus();
        await fireEvent.keyDown(dashboard, { key: 'b', ctrlKey: true });
        await waitFor(() => {
            expect(screen.queryByRole('navigation')).toBeNull();
            expect(document.activeElement).toBe(trigger);
        });
    });

    it('does not capture typing shortcuts and keeps navigation preferences through focus mode', async () => {
        render(Page);
        await fireEvent.click(await screen.findByRole('button', { name: 'Show navigation' }));
        const search = screen.getByRole('searchbox', { name: 'Find a dashboard' });
        await fireEvent.keyDown(search, { key: 'b', ctrlKey: true });
        await fireEvent.keyDown(search, { key: 'k', ctrlKey: true });
        expect(screen.queryByRole('dialog')).toBeNull();
        expect(uiStore.sidebarCollapsed).toBe(false);
        await fireEvent.click(screen.getByRole('button', { name: 'Enter focus mode' }));
        const exit = await screen.findByRole('button', { name: /Exit focus/ });
        await waitFor(() => expect(document.activeElement).toBe(exit));
        expect(screen.queryByRole('navigation')).toBeNull();
        await fireEvent.keyDown(exit, { key: 'Escape' });
        expect(await screen.findByRole('navigation')).toBeTruthy();
        await waitFor(() => expect(document.activeElement).toBe(screen.getByRole('button', { name: 'Enter focus mode' })));
    });

    it('restores the saved visibility and still closes when storage is unavailable', async () => {
        localStorage.setItem('sqlviz-sidebar-collapsed', '0');
        render(Page);
        expect(await screen.findByRole('navigation')).toBeTruthy();
        vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('Storage blocked'); });
        await fireEvent.click(screen.getByRole('button', { name: 'Hide navigation' }));
        await waitFor(() => expect(screen.queryByRole('navigation')).toBeNull());
    });

    it('uses a modal on narrow screens and dismisses it after selecting a dashboard', async () => {
        vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: true, addEventListener: vi.fn(), removeEventListener: vi.fn() })));
        render(Page);
        await fireEvent.click(await screen.findByRole('button', { name: 'Show navigation' }));
        const modal = await screen.findByRole('dialog', { name: 'Dashboard navigation' });
        expect(modal.getAttribute('aria-modal')).toBe('true');
        await fireEvent.click(await screen.findByRole('button', { name: 'Operations' }));
        await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
        expect(await screen.findByRole('button', { name: 'Show navigation' })).toBeTruthy();
    });

    it('closes mobile navigation with Escape and returns focus to the toggle', async () => {
        vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: true, addEventListener: vi.fn(), removeEventListener: vi.fn() })));
        render(Page);
        const trigger = await screen.findByRole('button', { name: 'Show navigation' });
        await fireEvent.click(trigger);
        await screen.findByRole('dialog', { name: 'Dashboard navigation' });
        await fireEvent.keyDown(document.activeElement ?? document.body, { key: 'Escape' });
        await waitFor(() => {
            expect(screen.queryByRole('dialog')).toBeNull();
            expect(document.activeElement).toBe(trigger);
        });
    });
});


describe('minimal reader Preview', () => {
    beforeEach(() => {
        editMode.set(false);
        vi.spyOn(Element.prototype, 'clientWidth', 'get').mockReturnValue(1024);
        vi.spyOn(Element.prototype, 'clientHeight', 'get').mockReturnValue(768);
        vi.spyOn(Element.prototype, 'getBoundingClientRect').mockReturnValue({
            x: 20, y: 20, width: 400, height: 40, top: 20, left: 20, right: 420, bottom: 60, toJSON: () => ({}),
        });
    });
    it('opens dashboard search from the title and keyboard without author commands', async () => {
        render(Page);
        await waitFor(() => expect(vi.mocked(fetch).mock.calls.some(([url]) =>
            String(url).endsWith('/d1/sql-script'))).toBe(true));
        const trigger = await screen.findByRole('button', { name: 'Switch dashboard: Revenue' });
        await waitFor(() => expect(dashboardStore.viewLoading).toBe(false));
        expect(screen.queryByRole('button', { name: 'Search dashboards and commands' })).toBeNull();
        expect(screen.getByRole('button', { name: 'Show navigation' })).toBeTruthy();
        await fireEvent.keyDown(trigger, { key: 'k', ctrlKey: true });
        const search = await screen.findByLabelText('Search shared dashboards');
        await fireEvent.input(search, { target: { value: 'Operations' } });
        await waitFor(() => expect(screen.getByRole('option', { name: 'Operations' }).getAttribute('data-disabled')).not.toBe('true'));
        await fireEvent.keyDown(search, { key: 'ArrowDown' });
        await fireEvent.keyDown(search, { key: 'Enter' });
        await screen.findByRole('button', { name: 'Switch dashboard: Operations' });
        expect(screen.queryByRole('navigation')).toBeNull();
    });
    it('opens the library directly from the brand control and reserves options for secondary actions', async () => {
        render(Page);
        await screen.findByRole('button', { name: 'Switch dashboard: Revenue' });
        const navigation = screen.getByRole('button', { name: 'Show navigation' });
        await fireEvent.click(navigation);
        await screen.findByRole('navigation', { name: 'Dashboard navigation' });
        expect(navigation.getAttribute('aria-expanded')).toBe('true');
        expect(screen.getAllByRole('button', { name: 'Hide navigation' })).toHaveLength(1);
        await fireEvent.click(navigation);
        await waitFor(() => expect(screen.queryByRole('navigation')).toBeNull());
        await fireEvent.click(screen.getByRole('button', { name: 'View options' }));
        expect(screen.getByRole('button', { name: 'Edit', hidden: true })).toBeTruthy();
        const options = screen.getByRole('dialog', { name: 'View options', hidden: true });
        expect(within(options).queryByRole('button', { name: /navigation/, hidden: true })).toBeNull();
    });
    it('returns focus to view options when leaving reader concentration mode', async () => {
        render(Page);
        await screen.findByRole('button', { name: 'Switch dashboard: Revenue' });
        await fireEvent.click(screen.getByRole('button', { name: 'View options' }));
        await fireEvent.click(screen.getByRole('button', { name: 'Enter focus mode', hidden: true }));
        const exit = await screen.findByRole('button', { name: /Exit focus/ });
        await waitFor(() => expect(document.activeElement).toBe(exit));
        await fireEvent.keyDown(exit, { key: 'Escape' });
        await waitFor(() => expect(document.activeElement).toBe(screen.getByRole('button', { name: 'View options' })));
    });
});
