import type { FilterControl } from '$lib/types';

export type FilterValues = Record<string, unknown>;
export const filterVariables = (control: FilterControl) => control.variable.split(',').map(v => v.trim());
export const hasFilterValue = (value: unknown) => value !== '' && value !== undefined && value !== null
    && (!Array.isArray(value) || value.length > 0);

export function copyFilterValues(values: FilterValues): FilterValues {
    return Object.fromEntries(Object.entries(values).map(([key, value]) => [key, Array.isArray(value) ? [...value] : value]));
}

export function sameFilterValue(a: unknown, b: unknown): boolean {
    if (!hasFilterValue(a) && !hasFilterValue(b)) return true;
    return Array.isArray(a) && Array.isArray(b)
        ? a.length === b.length && a.every((value, i) => value === b[i]) : a === b;
}

export function filterSummary(controls: FilterControl[], values: FilterValues) {
    return controls.filter(control => filterVariables(control).some(key => hasFilterValue(values[key])))
        .map(control => {
            const parts = filterVariables(control).map(key => values[key]);
            const text = parts.map(value => !hasFilterValue(value) ? 'Any'
                : Array.isArray(value) ? `${value.length} selected` : String(value)).join(' – ');
            return { label: control.label, value: text };
        });
}

/** Keep the current contract: absent/empty means All. Published defaults are not available yet. */
export function validateFilterValues(controls: FilterControl[], values: FilterValues): FilterValues {
    const allowed = new Set(controls.flatMap(filterVariables));
    if (Object.keys(values).some(key => !allowed.has(key))) throw new Error('These saved filters no longer match this dashboard.');
    for (const value of Object.values(values)) {
        const scalar = (v: unknown) => v == null || typeof v === 'boolean' || typeof v === 'string'
            || (typeof v === 'number' && Number.isFinite(v));
        if (Array.isArray(value) ? !value.every(scalar) : !scalar(value)) throw new Error('Choose a valid filter value.');
    }
    for (const control of controls) {
        const keys = filterVariables(control);
        const [from, to] = keys.map(key => values[key]);
        if (keys.length === 2 && hasFilterValue(from) && hasFilterValue(to)) {
            if (control.control_type === 'range_slider' && Number(from) > Number(to)) throw new Error(`${control.label}: minimum must not exceed maximum.`);
            if (control.control_type === 'date_range_picker' && String(from) > String(to)) throw new Error(`${control.label}: start must not follow end.`);
        }
    }
    return copyFilterValues(values);
}
