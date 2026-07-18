import { cleanup, render, screen } from '@testing-library/svelte';
import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('$app/navigation', () => ({ goto: vi.fn() }));

import Page from './+page.svelte';

afterEach(() => cleanup());

describe('/login', () => {
    it('renders the sign-in form', () => {
        render(Page);

        expect(screen.getByPlaceholderText('Admin password')).toBeTruthy();
        expect(screen.getByRole('button', { name: /sign in/i })).toBeTruthy();
    });
});
