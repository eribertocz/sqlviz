import { cleanup, fireEvent, render, waitFor } from '@testing-library/svelte';
import { afterEach, describe, expect, it, vi } from 'vitest';

import DashboardExplorer from './DashboardExplorer.svelte';
import { dashboardStore } from '$lib/stores/dashboardStore.svelte';
import { editMode } from '$lib/stores/editMode';
import { uiStore } from '$lib/stores/uiStore.svelte';

afterEach(() => {
    cleanup();
    editMode.set(false);
    uiStore.setSidebarCollapsed(true);
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
});

describe('DashboardExplorer', () => {
    it('shows its contents and asks the shell to close navigation', async () => {
        const onClose = vi.fn();
        const screen = render(DashboardExplorer, { onClose, showClose: true });
        await fireEvent.click(screen.getByLabelText('Hide navigation'));
        expect(onClose).toHaveBeenCalledOnce();
        expect(screen.queryByLabelText('Expand sidebar')).toBeNull();
    });

    it('keeps creation actions exclusive to Edit mode', () => {
        editMode.set(false);
        const screen = render(DashboardExplorer);
        expect(screen.queryByLabelText('New dashboard')).toBeNull();
        expect(screen.queryByLabelText('Hide navigation')).toBeNull();
        expect(screen.getByLabelText('Find a dashboard')).toBeTruthy();
    });

    it('finds dashboards by name or folder and announces an empty result', async () => {
        const dashboards = [
            { id: 'd1', name: 'Revenue', folder_id: 'f1', sort_order: 0 },
            { id: 'd2', name: 'Operations', folder_id: null, sort_order: 1 },
        ];
        vi.stubGlobal('fetch', vi.fn((url: string) => Promise.resolve({
            ok: true, status: 200,
            json: () => Promise.resolve(String(url).includes('/folders')
                ? [{ id: 'f1', name: 'Finance', sort_order: 0 }] : String(url).includes('/panels') ? [] : dashboards),
        } as Response)));
        await dashboardStore.bootstrap();
        const load = vi.spyOn(dashboardStore, 'loadDashboard').mockResolvedValue(undefined);
        const onNavigate = vi.fn();
        const screen = render(DashboardExplorer, { onNavigate });
        const search = screen.getByLabelText('Find a dashboard');
        await fireEvent.input(search, { target: { value: 'FINANCE' } });
        expect(screen.getByRole('button', { name: 'Revenue' })).toBeTruthy();
        expect(screen.queryByRole('button', { name: 'Operations' })).toBeNull();
        await fireEvent.click(screen.getByRole('button', { name: 'Revenue' }));
        expect(load).toHaveBeenCalledWith('d1');
        expect(onNavigate).toHaveBeenCalledOnce();
        await fireEvent.input(search, { target: { value: 'unknown' } });
        expect(screen.getByRole('status').textContent).toContain('No matching dashboards');
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
