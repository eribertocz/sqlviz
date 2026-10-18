import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/svelte';
import { afterEach, describe, expect, it, vi } from 'vitest';

import Page from './+page.svelte';

afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
});

describe('/view/[token]', () => {
    it('unlocks a password share and scopes every subsequent data request', async () => {
        const fetch = vi.fn(async (url: string) => ({ ok: true, status: 200,
            json: async () => url.endsWith('/unlock') ? {
                dashboard: { id: 'd1', name: 'Protected Revenue' },
                panels: [{ id: 'p1' }], viewer_session: 'session-A',
            } : url.startsWith('/view/') ? { requires_password: true }
                : url.includes('/execute') ? { inference_result: { filter_controls: [] }, data: [] }
                    : { rows: [] },
        } as Response));
        vi.stubGlobal('fetch', fetch);
        render(Page);
        await fireEvent.input(await screen.findByLabelText('Password'), { target: { value: 'reader-password' } });
        await fireEvent.click(screen.getByRole('button', { name: 'Unlock' }));
        await screen.findByText('Protected Revenue');
        const dataCalls = fetch.mock.calls.filter(([url]) => url.startsWith('/api/'));
        expect(dataCalls.length).toBe(2);
        for (const call of dataCalls) {
            const init = (call as unknown as [string, RequestInit])[1];
            expect(init.headers).toMatchObject({ 'X-SQLviz-Viewer-Session': 'session-A' });
            expect(init.headers).toHaveProperty('X-SQLviz-Share');
        }
    });

    it('does not present an unlocked dashboard when authorization fails during domain loading', async () => {
        vi.stubGlobal('fetch', vi.fn(async (url: string) => ({
            ok: !url.includes('/filter-domain'), status: url.includes('/filter-domain') ? 404 : 200,
            json: async () => url.startsWith('/view/') ? {
                dashboard: { id: 'd1', name: 'Revoked Revenue' }, panels: [{ id: 'p1' }],
            } : url.includes('/execute') ? { inference_result: { filter_controls: [{
                variable: 'region', column_name: 'region', control_type: 'dropdown',
            }] }, data: [{ secret: 'previous-data' }] }
                : url.includes('/compose') ? { rows: [] } : { detail: 'Share not found' },
        } as Response)));
        render(Page);
        await screen.findByText(/Failed to load the dashboard/i);
        await waitFor(() => expect(screen.queryByText('Revoked Revenue')).toBeNull());
    });
    it('renders an error state for a missing/expired share link', async () => {
        vi.stubGlobal('fetch', vi.fn((url: string) => {
            if (url.startsWith('/view/')) {
                return Promise.resolve({
                    ok: false,
                    status: 404,
                    json: () => Promise.resolve({}),
                } as Response);
            }
            return Promise.reject(new Error(`Unexpected fetch in test: ${url}`));
        }));

        render(Page);

        expect(await screen.findByText(/Dashboard not found or link has expired/i)).toBeTruthy();
    });
});
