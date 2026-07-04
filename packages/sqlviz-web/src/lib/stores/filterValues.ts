import { writable } from 'svelte/store';

/**
 * Current value of every active filter variable.
 * Key = variable name (e.g. "region", "start_date").
 * Value = the user-selected value; arrays for multiselect.
 */
export const filterValues = writable<Record<string, unknown>>({});
