import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/svelte';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import Page from './+page.svelte';

const workspace = {
    folders: [{ id: 'f1', name: 'Finance', parent_id: null, sort_order: 0 }],
    dashboards: [
        { id: 'd1', name: 'Revenue', folder_id: 'f1', sort_order: 0 },
        { id: 'd2', name: 'Operations', folder_id: null, sort_order: 1 },
    ],
};

beforeEach(() => {
    localStorage.clear();
    vi.spyOn(Element.prototype, 'clientWidth', 'get').mockReturnValue(1024);
    vi.spyOn(Element.prototype, 'clientHeight', 'get').mockReturnValue(768);
    vi.spyOn(Element.prototype, 'getBoundingClientRect').mockReturnValue({
        x: 20, y: 20, width: 400, height: 40, top: 20, left: 20, right: 420, bottom: 60,
        toJSON: () => ({}),
    });
    vi.stubGlobal('fetch', vi.fn((url: string) => Promise.resolve({
        ok: true, status: 200, json: () => Promise.resolve(String(url).startsWith('/view/') ? workspace
            : String(url).includes('/compose') ? { rows: [], score: 0 } : []),
    } as Response)));
});
afterEach(async () => {
    cleanup(); vi.restoreAllMocks(); vi.unstubAllGlobals();
    await new Promise(resolve => setTimeout(resolve, 30));
});

async function openLibrary() {
    await fireEvent.click(await screen.findByRole('button', { name: 'Show navigation' }));
}

describe('shared workspace navigation', () => {
    it('keeps one brand control in the header for opening and closing the library', async () => {
        render(Page);
        const trigger = await screen.findByRole('button', { name: 'Show navigation' });
        const header = trigger.closest('header')!;
        expect(trigger.getAttribute('aria-controls')).toBe('workspace-navigation');
        await fireEvent.click(trigger);
        await screen.findByRole('navigation', { name: 'Dashboard navigation' });
        expect(trigger.getAttribute('aria-expanded')).toBe('true');
        expect(screen.getAllByRole('button', { name: 'Hide navigation' })).toHaveLength(1);
        expect(header.querySelector('[data-navigation-trigger]')).toBe(trigger);
        expect(header.parentElement?.classList.contains('ws-shell')).toBe(true);
        await fireEvent.click(trigger);
        await waitFor(() => {
            expect(screen.queryByRole('navigation')).toBeNull();
            expect(document.activeElement).toBe(trigger);
        });
        expect(trigger.getAttribute('aria-expanded')).toBe('false');
    });

    it('focuses mobile library search and restores the brand control after Escape', async () => {
        vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: true, addEventListener: vi.fn(), removeEventListener: vi.fn() })));
        render(Page);
        const trigger = await screen.findByRole('button', { name: 'Show navigation' });
        await fireEvent.click(trigger);
        await screen.findByRole('dialog', { name: 'Dashboard navigation' });
        await waitFor(() => expect(document.activeElement).toBe(screen.getByRole('searchbox', { name: 'Find a dashboard' })));
        await fireEvent.keyDown(document.activeElement!, { key: 'Escape' });
        await waitFor(() => {
            expect(screen.queryByRole('dialog')).toBeNull();
            expect(document.activeElement).toBe(trigger);
        });
    });
    it('unlocks a workspace and keeps its session on panel requests', async () => {
        const fetch = vi.fn(async (url: string) => ({ ok: true, status: 200,
            json: async () => url.endsWith('/unlock') ? { ...workspace, viewer_session: 'session-W' }
                : url.startsWith('/view/') ? { requires_password: true } : [],
        } as Response));
        vi.stubGlobal('fetch', fetch);
        render(Page);
        await fireEvent.input(await screen.findByLabelText('Password'), { target: { value: 'reader-password' } });
        await fireEvent.click(screen.getByRole('button', { name: 'Unlock' }));
        await screen.findByRole('button', { name: 'Switch dashboard: Revenue' });
        await waitFor(() => expect(fetch.mock.calls.some(([url]) => url.includes('/panels?'))).toBe(true));
        const call = fetch.mock.calls.find(([url]) => url.includes('/panels?'))!;
        const init = (call as unknown as [string, RequestInit])[1];
        expect(init.headers).toMatchObject({ 'X-SQLviz-Viewer-Session': 'session-W' });
        expect(init.headers).toHaveProperty('X-SQLviz-Share');
    });

    it('removes navigation and the previous dashboard when the next request is revoked', async () => {
        let panelRequests = 0;
        vi.stubGlobal('fetch', vi.fn(async (url: string) => {
            if (url.includes('/panels?')) panelRequests += 1;
            const denied = url.includes('/panels?') && panelRequests > 1;
            return { ok: !denied, status: denied ? 404 : 200,
                json: async () => url.startsWith('/view/') ? workspace : denied ? { detail: 'Share not found' } : [],
            } as Response;
        }));
        render(Page);
        await openLibrary();
        await fireEvent.click(screen.getByRole('button', { name: 'Operations' }));
        await screen.findByText(/Workspace access has expired or was revoked/i);
        expect(screen.queryByRole('navigation')).toBeNull();
        expect(screen.queryByRole('button', { name: 'Show navigation' })).toBeNull();
        expect(screen.queryByText('Operations')).toBeNull();
    });
    it('reclaims the entire sidebar and offers dashboard search without authoring actions', async () => {
        render(Page);
        const trigger = await screen.findByRole('button', { name: 'Switch dashboard: Revenue' });
        expect(screen.queryByRole('navigation')).toBeNull();
        const find = trigger as HTMLButtonElement;
        await waitFor(() => expect(find.disabled).toBe(false));
        await fireEvent.click(find);
        const search = await screen.findByLabelText('Search shared dashboards');
        await waitFor(() => expect(document.activeElement).toBe(search));
        await fireEvent.input(search, { target: { value: 'finance' } });
        expect(screen.getByRole('option', { hidden: true })).toBeTruthy();
        expect(screen.queryByText('Operations')).toBeNull();
        expect(screen.queryByRole('navigation')).toBeNull();
        expect(screen.queryByRole('button', { name: 'New dashboard' })).toBeNull();
        await fireEvent.keyDown(search, { key: 'Escape' });
        await waitFor(() => expect(screen.queryByRole('combobox', { hidden: true })).toBeNull());
        expect(trigger.getAttribute('aria-expanded')).toBe('false');
    });

    it('dismisses mobile navigation after switching dashboards', async () => {
        vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: true, addEventListener: vi.fn(), removeEventListener: vi.fn() })));
        render(Page);
        await openLibrary();
        await screen.findByRole('dialog', { name: 'Dashboard navigation' });
        await fireEvent.click(screen.getByRole('button', { name: 'Operations' }));
        await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
        expect(await screen.findByText('Operations')).toBeTruthy();
    });

    it('keeps navigation unavailable until a protected workspace is unlocked', async () => {
        vi.stubGlobal('fetch', vi.fn(() => Promise.resolve({ ok: true, status: 200,
            json: () => Promise.resolve({ requires_password: true }),
        } as Response)));
        render(Page);
        expect(await screen.findByLabelText('Password')).toBeTruthy();
        expect(screen.queryByRole('button', { name: 'Show navigation' })).toBeNull();
        expect(screen.queryByRole('navigation')).toBeNull();
        expect(screen.queryByRole('group', { name: 'Dashboard switcher' })).toBeNull();
    });

    it('keeps the header compact and switches without opening the library', async () => {
        render(Page);
        const trigger = await screen.findByRole('button', { name: 'Switch dashboard: Revenue' });
        expect(screen.queryByRole('button', { name: 'Next dashboard' })).toBeNull();
        expect(screen.queryByRole('button', { name: 'Find a dashboard' })).toBeNull();
        await fireEvent.click(trigger);
        const search = await screen.findByLabelText('Search shared dashboards');
        await fireEvent.input(search, { target: { value: 'Operations' } });
        await waitFor(() => expect(screen.getByRole('option', { hidden: true }).getAttribute('aria-disabled')).not.toBe('true'));
        await fireEvent.keyDown(search, { key: 'ArrowDown' });
        await fireEvent.keyDown(search, { key: 'Enter' });
        await screen.findByRole('button', { name: 'Switch dashboard: Operations' });
        expect(screen.queryByRole('navigation')).toBeNull();
        expect(localStorage.getItem('sqlviz-viewer-navigation-hidden')).toBeNull();
    });

    it('opens keyboard search without changing the sidebar preference', async () => {
        render(Page);
        const trigger = await screen.findByRole('button', { name: 'Switch dashboard: Revenue' }) as HTMLButtonElement;
        await waitFor(() => expect(trigger.disabled).toBe(false));
        await fireEvent.keyDown(window, { key: 'k', ctrlKey: true });
        const search = await screen.findByLabelText('Search shared dashboards');
        await fireEvent.input(search, { target: { value: 'Operations' } });
        await fireEvent.keyDown(search, { key: 'ArrowDown' });
        await fireEvent.keyDown(search, { key: 'Enter' });
        await screen.findByRole('button', { name: 'Switch dashboard: Operations' });
        expect(screen.queryByRole('combobox', { hidden: true })).toBeNull();
        expect(screen.queryByRole('navigation')).toBeNull();
    });

    it('does not publish results from a dashboard left while it was loading', async () => {
        let resolvePanels!: (response: Response) => void;
        const fetch = vi.fn(async (url: string) => {
            if (url.includes('dashboard_id=d1')) return new Promise<Response>(resolve => { resolvePanels = resolve; });
            return { ok: true, status: 200, json: async () => url.startsWith('/view/') ? workspace
                : url.includes('/compose') ? { rows: [] } : [] } as Response;
        });
        vi.stubGlobal('fetch', fetch);
        render(Page);
        await openLibrary();
        await fireEvent.click(screen.getByRole('button', { name: 'Operations' }));
        const trigger = await screen.findByRole('button', { name: 'Switch dashboard: Operations' }) as HTMLButtonElement;
        await waitFor(() => expect(trigger.disabled).toBe(false));
        resolvePanels({ ok: true, status: 200, json: async () => [{ id: 'obsolete-panel' }] } as Response);
        await new Promise(resolve => setTimeout(resolve, 30));
        expect(fetch.mock.calls.some(([url]) => url.includes('obsolete-panel'))).toBe(false);
        expect(trigger.disabled).toBe(false);
    });

    it('offers no pointless switcher for an empty workspace', async () => {
        vi.stubGlobal('fetch', vi.fn(async (url: string) => ({ ok: true, status: 200,
            json: async () => url.startsWith('/view/') ? { folders: [], dashboards: [] } : [],
        } as Response)));
        render(Page);
        await screen.findByText('No dashboards have been shared.');
        expect(screen.queryByRole('button', { name: 'Next dashboard' })).toBeNull();
        expect(screen.queryByRole('button', { name: 'Find a dashboard' })).toBeNull();
    });
});
