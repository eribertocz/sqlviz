import { cleanup, fireEvent, render, waitFor } from '@testing-library/svelte';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import FilterViews from './FilterViews.svelte';
import { filterViews } from '$lib/stores/filterViews.svelte';

beforeEach(() => localStorage.clear());
afterEach(() => {
    cleanup();
    localStorage.clear();
});

let n = 0;
const freshId = () => `fv-dash-${++n}`;

/** bits-ui popovers open on pointerdown, which jsdom does not derive from click. */
async function openPopover(trigger: Element) {
    await fireEvent.pointerDown(trigger, { pointerType: 'mouse', button: 0 });
    await fireEvent.click(trigger);
}

function mount(dashboardId: string | null, currentValues: Record<string, unknown> = {}) {
    const onApply = vi.fn();
    const rendered = render(FilterViews, { dashboardId, currentValues, onApply });
    return { ...rendered, onApply };
}

describe('FilterViews — pill', () => {
    it('renders the trigger with no count when nothing is saved', () => {
        const { getByLabelText } = mount(freshId());
        const pill = getByLabelText('Saved views');
        expect(pill.textContent).toContain('Views');
        expect(pill.querySelector('.views-count')).toBeNull();
    });

    it('shows how many views the dashboard has', () => {
        const id = freshId();
        filterViews.save(id, 'Q1', { region: 'North' });
        filterViews.save(id, 'Q2', { region: 'South' });

        const { getByLabelText } = mount(id);
        expect(getByLabelText('Saved views').querySelector('.views-count')?.textContent).toBe('2');
    });

    it('renders without a dashboard id instead of throwing', () => {
        expect(() => mount(null)).not.toThrow();
    });
});

describe('FilterViews — saving and applying', () => {
    it('saves the current filter values under the typed name', async () => {
        const id = freshId();
        const { getByLabelText, getByPlaceholderText, getByText } = mount(id, {
            region: 'North',
            quarter: 'Q1',
        });

        await openPopover(getByLabelText('Saved views'));
        const input = await waitFor(() => getByPlaceholderText('Save current as…'));
        await fireEvent.input(input, { target: { value: 'North Q1' } });
        await fireEvent.click(getByText('Save'));

        const saved = filterViews.list(id);
        expect(saved).toHaveLength(1);
        expect(saved[0].name).toBe('North Q1');
        expect(saved[0].values).toEqual({ region: 'North', quarter: 'Q1' });
    });

    it('hands a saved view back to the caller when applied', async () => {
        const id = freshId();
        filterViews.save(id, 'North Q1', { region: 'North', quarter: 'Q1' });
        const { getByLabelText, getByText, onApply } = mount(id);

        await openPopover(getByLabelText('Saved views'));
        await fireEvent.click(await waitFor(() => getByText('North Q1')));

        expect(onApply).toHaveBeenCalledWith({ region: 'North', quarter: 'Q1' });
    });

    it('deletes a view without applying it', async () => {
        const id = freshId();
        filterViews.save(id, 'Doomed', { region: 'North' });
        const { getByLabelText, onApply } = mount(id);

        await openPopover(getByLabelText('Saved views'));
        await fireEvent.click(await waitFor(() => getByLabelText('Delete view')));

        expect(filterViews.list(id)).toHaveLength(0);
        expect(onApply).not.toHaveBeenCalled();
    });
});

// Viewers reach shared dashboards over http://<LAN-IP>, an insecure context.
describe('FilterViews — insecure context (LAN viewer)', () => {
    it('still saves when crypto.randomUUID is unavailable', async () => {
        const original = crypto.randomUUID;
        Object.defineProperty(crypto, 'randomUUID', { value: undefined, configurable: true });
        try {
            const id = freshId();
            const { getByLabelText, getByPlaceholderText, getByText } = mount(id, { region: 'North' });

            await openPopover(getByLabelText('Saved views'));
            const input = await waitFor(() => getByPlaceholderText('Save current as…'));
            await fireEvent.input(input, { target: { value: 'From a phone' } });
            await fireEvent.click(getByText('Save'));

            expect(filterViews.list(id).map(v => v.name)).toEqual(['From a phone']);
        } finally {
            Object.defineProperty(crypto, 'randomUUID', { value: original, configurable: true });
        }
    });
});
