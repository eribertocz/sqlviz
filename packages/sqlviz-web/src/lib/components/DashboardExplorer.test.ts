import { cleanup, render } from '@testing-library/svelte';
import { afterEach, describe, expect, it } from 'vitest';

import DashboardExplorer from './DashboardExplorer.svelte';
import { editMode } from '$lib/stores/editMode';
import { uiStore } from '$lib/stores/uiStore.svelte';

afterEach(() => {
    cleanup();
    editMode.set(false);
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
});
