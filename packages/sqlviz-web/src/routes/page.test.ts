import { cleanup, render, screen } from '@testing-library/svelte';
import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('$app/navigation', () => ({ goto: vi.fn() }));

import Page from './+page.svelte';

afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
});

describe('/ (dashboard)', () => {
    it('renders the empty Preview-mode dashboard without crashing', async () => {
        vi.stubGlobal('fetch', vi.fn((url: string) => {
            if (url === '/api/v1/auth/me') {
                return Promise.resolve({
                    status: 200,
                    json: () => Promise.resolve({ status: 'ok', demo: false }),
                } as Response);
            }
            if (url === '/api/v1/dashboards') {
                return Promise.resolve({
                    ok: true,
                    status: 200,
                    json: () => Promise.resolve([]),
                } as Response);
            }
            return Promise.reject(new Error(`Unexpected fetch in test: ${url}`));
        }));

        render(Page);

        // Sidebar is a rail by default, so the app shell is proven by its
        // expand toggle rather than the (now collapsed) wordmark.
        expect(await screen.findByLabelText('Expand sidebar')).toBeTruthy();
        expect(await screen.findByText(/Switch to Edit mode to write SQL/i)).toBeTruthy();
    });
});
