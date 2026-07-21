import { cleanup, fireEvent, render, waitFor } from '@testing-library/svelte';
import { afterEach, describe, expect, it, vi } from 'vitest';

import DashboardExplorer from './DashboardExplorer.svelte';
import { dashboardStore } from '$lib/stores/dashboardStore.svelte';
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

    // Empty fetch → bootstrap resolves with no dashboards and, crucially, flips
    // dashboardsLoading to false so the tree (and its inline inputs) render
    // instead of loading skeletons.
    function stubEmptyFetch() {
        vi.stubGlobal('fetch', vi.fn(() => Promise.resolve({
            ok: true, status: 200, json: () => Promise.resolve([]),
        } as Response)));
    }

    it('creates a group inline (no modal) and commits on Enter', async () => {
        stubEmptyFetch();
        await dashboardStore.bootstrap();
        const createFolder = vi.spyOn(dashboardStore, 'createFolder').mockResolvedValue(undefined);
        editMode.set(true);
        const screen = render(DashboardExplorer);

        // Clicking "New group" opens an inline input in the tree — never a modal.
        await fireEvent.click(screen.getByLabelText('New group'));
        const input = await screen.findByPlaceholderText('Nombre de la carpeta');
        await fireEvent.input(input, { target: { value: 'Sales' } });
        await fireEvent.keyDown(input, { key: 'Enter' });

        expect(createFolder).toHaveBeenCalledWith('Sales');
        // The inline input is gone once committed.
        await waitFor(() => {
            expect(screen.queryByPlaceholderText('Nombre de la carpeta')).toBeNull();
        });
        createFolder.mockRestore();
    });

    it('creates a new dashboard inside the folder the user selected', async () => {
        // Bootstrap with one (empty) folder so it renders a selectable header.
        vi.stubGlobal('fetch', vi.fn((url: string) => Promise.resolve({
            ok: true, status: 200,
            json: () => Promise.resolve(
                String(url).includes('/folders')
                    ? [{ id: 'f1', name: 'Sales', sort_order: 0, parent_id: null }]
                    : [],
            ),
        } as Response)));
        await dashboardStore.bootstrap();
        const createDashboard = vi.spyOn(dashboardStore, 'createDashboard').mockResolvedValue(undefined);
        editMode.set(true);
        const screen = render(DashboardExplorer);

        // Select the folder, then create a dashboard — it must land inside it,
        // even though the folder has no dashboards yet.
        await fireEvent.click(screen.getByText('Sales'));
        await fireEvent.click(screen.getByLabelText('New dashboard'));
        const input = await screen.findByPlaceholderText('Nombre del dashboard');
        await fireEvent.input(input, { target: { value: 'Q3 report' } });
        await fireEvent.keyDown(input, { key: 'Enter' });

        expect(createDashboard).toHaveBeenCalledWith('Q3 report', 'f1');
        createDashboard.mockRestore();
    });

    it('shows a subtle validation message when the name is empty on Enter', async () => {
        stubEmptyFetch();
        await dashboardStore.bootstrap();
        const createFolder = vi.spyOn(dashboardStore, 'createFolder').mockResolvedValue(undefined);
        editMode.set(true);
        const screen = render(DashboardExplorer);

        await fireEvent.click(screen.getByLabelText('New group'));
        const input = await screen.findByPlaceholderText('Nombre de la carpeta');
        await fireEvent.keyDown(input, { key: 'Enter' });

        // Message shown, input still present, nothing created.
        expect(await screen.findByText('Debes especificar un nombre para la carpeta')).toBeTruthy();
        expect(screen.queryByPlaceholderText('Nombre de la carpeta')).not.toBeNull();
        expect(createFolder).not.toHaveBeenCalled();
        createFolder.mockRestore();
    });

    it('cancels inline creation on Escape without creating anything', async () => {
        stubEmptyFetch();
        await dashboardStore.bootstrap();
        const createDashboard = vi.spyOn(dashboardStore, 'createDashboard').mockResolvedValue(undefined);
        editMode.set(true);
        const screen = render(DashboardExplorer);

        await fireEvent.click(screen.getByLabelText('New dashboard'));
        const input = await screen.findByPlaceholderText('Nombre del dashboard');
        await fireEvent.input(input, { target: { value: 'Draft' } });
        await fireEvent.keyDown(input, { key: 'Escape' });

        await waitFor(() => {
            expect(screen.queryByPlaceholderText('Nombre del dashboard')).toBeNull();
        });
        expect(createDashboard).not.toHaveBeenCalled();
        createDashboard.mockRestore();
    });
});
