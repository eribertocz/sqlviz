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

describe('FilterControl — renders correct control + emits correct value for all 8 types', () => {
    it('dropdown: text input, emits string', async () => {
        const onChange = vi.fn();
        const { container } = render(FilterControl, {
            control: base({ variable: 'region', control_type: 'dropdown' }),
            filterVals: {}, onChange,
        });
        const input = container.querySelector('input[type="text"]')!;
        await fireEvent.input(input, { target: { value: 'North' } });
        expect(onChange).toHaveBeenCalledWith('region', 'North');
    });

    it('multiselect: comma text, emits string[]', async () => {
        const onChange = vi.fn();
        const { container } = render(FilterControl, {
            control: base({ variable: 'region', control_type: 'multiselect' }),
            filterVals: {}, onChange,
        });
        const input = container.querySelector('input[type="text"]')!;
        await fireEvent.input(input, { target: { value: 'A, B' } });
        expect(onChange).toHaveBeenCalledWith('region', ['A', 'B']);
    });

    it('date_picker: date input, emits string', async () => {
        const onChange = vi.fn();
        const { container } = render(FilterControl, {
            control: base({ variable: 'fecha', control_type: 'date_picker', column_type: 'DATE' }),
            filterVals: {}, onChange,
        });
        const input = container.querySelector('input[type="date"]')!;
        await fireEvent.change(input, { target: { value: '2024-01-01' } });
        expect(onChange).toHaveBeenCalledWith('fecha', '2024-01-01');
    });

    it('date_range_picker: two date inputs, emits to both vars', async () => {
        const onChange = vi.fn();
        const { container } = render(FilterControl, {
            control: base({ variable: 'desde,hasta', control_type: 'date_range_picker', column_type: 'DATE' }),
            filterVals: {}, onChange,
        });
        const inputs = container.querySelectorAll('input[type="date"]');
        expect(inputs.length).toBe(2);
        await fireEvent.change(inputs[0], { target: { value: '2024-01-01' } });
        await fireEvent.change(inputs[1], { target: { value: '2024-06-01' } });
        expect(onChange).toHaveBeenCalledWith('desde', '2024-01-01');
        expect(onChange).toHaveBeenCalledWith('hasta', '2024-06-01');
    });

    it('numeric: number input, emits number', async () => {
        const onChange = vi.fn();
        const { container } = render(FilterControl, {
            control: base({ variable: 'price', control_type: 'numeric', column_type: 'DOUBLE' }),
            filterVals: {}, onChange,
        });
        const input = container.querySelector('input[type="number"]')!;
        await fireEvent.input(input, { target: { value: '42' } });
        expect(onChange).toHaveBeenCalledWith('price', 42);
    });

    it('range_slider: two number inputs, emits numbers to both vars', async () => {
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

    it('search: text input, emits string', async () => {
        const onChange = vi.fn();
        const { container } = render(FilterControl, {
            control: base({ variable: 'q', control_type: 'search' }),
            filterVals: {}, onChange,
        });
        const input = container.querySelector('input[type="text"]')!;
        await fireEvent.input(input, { target: { value: '%foo%' } });
        expect(onChange).toHaveBeenCalledWith('q', '%foo%');
    });

    it('toggle: checkbox, emits boolean', async () => {
        const onChange = vi.fn();
        const { container } = render(FilterControl, {
            control: base({ variable: 'active', control_type: 'toggle', column_type: 'BOOLEAN' }),
            filterVals: {}, onChange,
        });
        const input = container.querySelector('input[type="checkbox"]')! as HTMLInputElement;
        await fireEvent.change(input, { target: { checked: true } });
        expect(onChange).toHaveBeenCalledWith('active', true);
    });
});

describe('FilterControl — rich controls when a column domain is provided', () => {
    it('dropdown: renders a <select> populated with the domain values', async () => {
        const onChange = vi.fn();
        const { container } = render(FilterControl, {
            control: base({ variable: 'region', control_type: 'dropdown' }),
            filterVals: {}, domain: { values: ['A', 'B', 'C'] }, onChange,
        });
        const select = container.querySelector('select')! as HTMLSelectElement;
        expect(select).toBeTruthy();
        // "All" + 3 domain options
        expect(select.querySelectorAll('option').length).toBe(4);
        await fireEvent.change(select, { target: { value: 'B' } });
        expect(onChange).toHaveBeenCalledWith('region', 'B');
    });

    it('multiselect: renders checkboxes; toggling emits the updated array', async () => {
        const onChange = vi.fn();
        const { container } = render(FilterControl, {
            control: base({ variable: 'region', control_type: 'multiselect' }),
            filterVals: { region: ['A'] }, domain: { values: ['A', 'B', 'C'] }, onChange,
        });
        const boxes = container.querySelectorAll('.multiselect-panel input[type="checkbox"]');
        expect(boxes.length).toBe(3);
        // check "B" (second option) → array becomes ['A','B']
        await fireEvent.change(boxes[1], { target: { checked: true } });
        expect(onChange).toHaveBeenCalledWith('region', ['A', 'B']);
    });

    it('range_slider: renders two range inputs bounded by the domain', async () => {
        const onChange = vi.fn();
        const { container } = render(FilterControl, {
            control: base({ variable: 'min,max', control_type: 'range_slider', column_type: 'INTEGER' }),
            filterVals: {}, domain: { min: 0, max: 100 }, onChange,
        });
        const sliders = container.querySelectorAll('input[type="range"]');
        expect(sliders.length).toBe(2);
        expect((sliders[0] as HTMLInputElement).min).toBe('0');
        expect((sliders[0] as HTMLInputElement).max).toBe('100');
        await fireEvent.input(sliders[0], { target: { value: '25' } });
        expect(onChange).toHaveBeenCalledWith('min', 25);
    });

    it('dropdown: falls back to a text input when the domain is empty', () => {
        const { container } = render(FilterControl, {
            control: base({ variable: 'region', control_type: 'dropdown' }),
            filterVals: {}, domain: { values: [] }, onChange: vi.fn(),
        });
        expect(container.querySelector('select')).toBeNull();
        expect(container.querySelector('input[type="text"]')).toBeTruthy();
    });
});
