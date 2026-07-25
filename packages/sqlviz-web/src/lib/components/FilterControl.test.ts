import { cleanup, fireEvent, render, waitFor } from '@testing-library/svelte';
import { afterEach, describe, expect, it, vi } from 'vitest';

import FilterControl from './FilterControl.svelte';
import type { FilterControl as FC } from '$lib/types';

afterEach(cleanup);

function base(partial: Partial<FC>): FC {
    return {
        variable: 'v',
        label: 'L',
        control_type: 'dropdown',
        column_name: 'c',
        column_type: 'VARCHAR',
        scope: 'global',
        ...partial,
    };
}

// Fallback controls (no domain) use shadcn's <Input>, which renders a real
// native <input> — so we can assert the emit contract precisely here.
describe('FilterControl — fallback shadcn Input controls emit correct values', () => {
    it('dropdown (no domain): text Input emits string', async () => {
        const onChange = vi.fn();
        const { container } = render(FilterControl, {
            control: base({ variable: 'region', control_type: 'dropdown' }),
            filterVals: {}, onChange,
        });
        const input = container.querySelector('input[type="text"]')!;
        await fireEvent.input(input, { target: { value: 'North' } });
        expect(onChange).toHaveBeenCalledWith('region', 'North');
    });

    it('multiselect (no domain): comma Input emits string[]', async () => {
        const onChange = vi.fn();
        const { container } = render(FilterControl, {
            control: base({ variable: 'region', control_type: 'multiselect' }),
            filterVals: {}, onChange,
        });
        const input = container.querySelector('input[type="text"]')!;
        await fireEvent.input(input, { target: { value: 'A, B' } });
        expect(onChange).toHaveBeenCalledWith('region', ['A', 'B']);
    });

    it('search: text Input emits string', async () => {
        const onChange = vi.fn();
        const { container } = render(FilterControl, {
            control: base({ variable: 'q', control_type: 'search' }),
            filterVals: {}, onChange,
        });
        const input = container.querySelector('input[type="text"]')!;
        await fireEvent.input(input, { target: { value: '%foo%' } });
        expect(onChange).toHaveBeenCalledWith('q', '%foo%');
    });

    it('numeric: number Input emits number', async () => {
        const onChange = vi.fn();
        const { container } = render(FilterControl, {
            control: base({ variable: 'price', control_type: 'numeric', column_type: 'DOUBLE' }),
            filterVals: {}, onChange,
        });
        const input = container.querySelector('input[type="number"]')!;
        await fireEvent.input(input, { target: { value: '42' } });
        expect(onChange).toHaveBeenCalledWith('price', 42);
    });

    it('range_slider (no domain): two number Inputs emit numbers to both vars', async () => {
        const onChange = vi.fn();
        const { container } = render(FilterControl, {
            control: base({ variable: 'min,max', control_type: 'range_slider', column_type: 'DOUBLE' }),
            filterVals: {}, onChange,
        });
        const inputs = container.querySelectorAll('input[type="number"]');
        expect(inputs.length).toBe(2);
        await fireEvent.input(inputs[0], { target: { value: '10' } });
        await fireEvent.input(inputs[1], { target: { value: '90' } });
        expect(onChange).toHaveBeenCalledWith('min', 10);
        expect(onChange).toHaveBeenCalledWith('max', 90);
    });
});

// The shadcn Switch (bits-ui) renders a real button[role="switch"].
describe('FilterControl — toggle uses shadcn Switch', () => {
    it('renders a switch and emits boolean on toggle', async () => {
        const onChange = vi.fn();
        const { container } = render(FilterControl, {
            control: base({ variable: 'active', control_type: 'toggle', column_type: 'BOOLEAN' }),
            filterVals: {}, onChange,
        });
        const sw = container.querySelector('[role="switch"]')!;
        expect(sw).toBeTruthy();
        await fireEvent.click(sw);
        expect(onChange).toHaveBeenCalledWith('active', true);
    });
});

// Rich controls (Select/Combobox/Calendar/Slider) are bits-ui components whose
// menus/portals aren't fully exercisable in jsdom; assert they mount and expose
// the expected trigger/role without throwing.
describe('FilterControl — rich shadcn controls mount with a domain', () => {
    it('dropdown with options renders a select trigger (combobox role)', () => {
        const { container } = render(FilterControl, {
            control: base({ variable: 'region', control_type: 'dropdown' }),
            filterVals: {}, domain: { values: ['A', 'B', 'C'] }, onChange: vi.fn(),
        });
        expect(container.querySelector('[data-slot="select-trigger"], [role="combobox"]')).toBeTruthy();
    });

    it('range_slider with bounds renders slider thumbs', () => {
        const { container } = render(FilterControl, {
            control: base({ variable: 'min,max', control_type: 'range_slider', column_type: 'INTEGER' }),
            filterVals: {}, domain: { min: 0, max: 100 }, onChange: vi.fn(),
        });
        expect(container.querySelectorAll('[role="slider"]').length).toBeGreaterThanOrEqual(1);
    });

    it('date_picker mounts without throwing', () => {
        expect(() => render(FilterControl, {
            control: base({ variable: 'fecha', control_type: 'date_picker', column_type: 'DATE' }),
            filterVals: { fecha: '2024-01-01' }, onChange: vi.fn(),
        })).not.toThrow();
    });

    it('date_range_picker mounts without throwing', () => {
        expect(() => render(FilterControl, {
            control: base({ variable: 'desde,hasta', control_type: 'date_range_picker', column_type: 'DATE' }),
            filterVals: {}, onChange: vi.fn(),
        })).not.toThrow();
    });

    it('multiselect combobox mounts without throwing', () => {
        expect(() => render(FilterControl, {
            control: base({ variable: 'region', control_type: 'multiselect' }),
            filterVals: { region: ['A'] }, domain: { values: ['A', 'B', 'C'] }, onChange: vi.fn(),
        })).not.toThrow();
    });
});

// A long option list used to run off the bottom of the screen: the select
// content had `overflow-y-auto` but nothing bounding its height, and an
// unbounded box never scrolls. jsdom does no layout, so this asserts the height
// bound is present rather than measuring it — enough to catch the regression if
// `ui/select/select-content.svelte` is ever regenerated by the shadcn CLI.
describe('FilterControl — dropdown height is bounded so long lists scroll', () => {
    const manyOptions = Array.from({ length: 80 }, (_, i) => `Option ${i + 1}`);

    async function openDropdown(container: HTMLElement) {
        const trigger = container.querySelector('[data-slot="select-trigger"]')!;
        // bits-ui opens on a left-button pointerdown, not on click.
        await fireEvent.pointerDown(trigger, { pointerType: 'mouse', button: 0, pointerId: 1 });
        return waitFor(() => {
            const content = document.querySelector('[data-slot="select-content"]');
            if (!content) throw new Error('select content did not open');
            return content as HTMLElement;
        });
    }

    it('caps the open dropdown and lets the viewport own the scrolling', async () => {
        const { container } = render(FilterControl, {
            control: base({ variable: 'region', control_type: 'dropdown' }),
            filterVals: {}, domain: { values: manyOptions }, onChange: vi.fn(),
        });

        const content = await openDropdown(container);
        // Bounded by bits-ui's measured available height, capped at 18rem.
        expect(content.className).toContain('max-h-[min(18rem,var(--bits-select-content-available-height))]');
        // bits-ui scrolls the viewport (`flex:1; overflow:auto`), which only
        // works if the content is a flex column that clips.
        expect(content.className).toContain('flex-col');
        expect(content.className).toContain('overflow-hidden');
    });

    it('leaves the viewport free to fill the bounded content', async () => {
        const { container } = render(FilterControl, {
            control: base({ variable: 'region', control_type: 'dropdown' }),
            filterVals: {}, domain: { values: manyOptions }, onChange: vi.fn(),
        });

        await openDropdown(container);
        const viewport = document.querySelector('[data-select-viewport]') as HTMLElement | null;
        expect(viewport).toBeTruthy();
        // Pinning the viewport to the trigger's height fights bits-ui's `flex:1`.
        expect(viewport!.className).not.toContain('anchor-height');
    });
});
