import { cleanup, render, screen } from '@testing-library/svelte';
import { afterEach, describe, expect, it, vi } from 'vitest';

import Page from './+page.svelte';

afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
});

describe('/view/[token]', () => {
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
