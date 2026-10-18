import { cleanup, fireEvent, render, waitFor } from '@testing-library/svelte';
import { afterEach, expect, it, vi } from 'vitest';
import type { DashboardPanel } from '$lib/types';
import { dashboardStore } from '$lib/stores/dashboardStore.svelte';
import PanelPropertiesPanel from './PanelPropertiesPanel.svelte';

vi.mock('$lib/stores/dashboardStore.svelte', () => ({ dashboardStore: {
    panelSQLs: ['SELECT 1'], panelIds: ['p'], handleWidthOverride: vi.fn(),
    handleHeightOverride: vi.fn(), closePanelProperties: vi.fn(),
} }));
afterEach(() => { cleanup(); vi.clearAllMocks(); });

it.each([
    ['Width (columns)', '6', '12', 'handleWidthOverride'],
    ['Height (px)', '480', '360', 'handleHeightOverride'],
] as const)('restores %s after an unconfirmed save and disables controls while pending',
async (label, attempted, confirmed, method) => {
    const panel = {
        panel_id: 'p', final_col_span: 12, data: [],
        inference_result: { chart_winner: 'bar', panel_height_px: 360 },
    } as unknown as DashboardPanel;
    let finish!: () => void;
    vi.mocked(dashboardStore[method]).mockImplementationOnce(() => new Promise<void>(r => { finish = r; }));
    const screen = render(PanelPropertiesPanel, { panel });
    const input = screen.getByLabelText(label) as HTMLInputElement;
    await fireEvent.input(input, { target: { value: attempted } });
    await fireEvent.change(input);
    expect(input.disabled).toBe(true);
    expect((screen.getByRole('button', { name: 'Reset to auto' }) as HTMLButtonElement).disabled).toBe(true);
    finish(); // The store handles rejection; its authoritative panel stays unchanged.
    await waitFor(() => {
        expect(input.disabled).toBe(false);
        expect(input.value).toBe(confirmed);
    });
});
