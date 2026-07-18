import { cleanup, fireEvent, render } from '@testing-library/svelte';
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
