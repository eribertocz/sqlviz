import { cleanup, fireEvent, render, waitFor } from '@testing-library/svelte';
import { afterEach, describe, expect, it, vi } from 'vitest';

import DashboardExplorer from './DashboardExplorer.svelte';
import { editMode } from '$lib/stores/editMode';
import { uiStore } from '$lib/stores/uiStore.svelte';

afterEach(() => {
    cleanup();
    editMode.set(false);
    vi.unstubAllGlobals();
});

describe('DashboardExplorer — dual mode + collapsible sidebar', () => {
    it('mounts in preview mode without throwing and shows a collapse toggle', () => {
        editMode.set(false);
        const { getByLabelText } = render(DashboardExplorer);
        expect(getByLabelText('Collapse sidebar')).toBeTruthy();
    });

    it('mounts in edit mode without throwing', () => {
        editMode.set(true);
        expect(() => render(DashboardExplorer)).not.toThrow();
    });

    it('exposes an expand toggle when the sidebar is collapsed', () => {
        // uiStore is a singleton; collapse it for this render.
        if (!uiStore.sidebarCollapsed) uiStore.toggleSidebar();
        try {
            const { getByLabelText } = render(DashboardExplorer);
            expect(getByLabelText('Expand sidebar')).toBeTruthy();
        } finally {
            if (uiStore.sidebarCollapsed) uiStore.toggleSidebar();
        }
    });

    it('closes the New group dialog after clicking Create', async () => {
        // Stub fetch so createFolder/refreshExplorer resolve quietly.
        vi.stubGlobal('fetch', vi.fn(() => Promise.resolve({
            ok: true, status: 200, json: () => Promise.resolve([]),
        } as Response)));
        editMode.set(true);
        const screen = render(DashboardExplorer);

        await fireEvent.click(screen.getByLabelText('New group'));
        const input = await screen.findByPlaceholderText('Group name');
        await fireEvent.input(input, { target: { value: 'Sales' } });
        await fireEvent.click(screen.getByText('Create'));

        // The dialog (its input) must be gone once confirmed.
        await waitFor(() => {
            expect(screen.queryByPlaceholderText('Group name')).toBeNull();
        });
    });
});
