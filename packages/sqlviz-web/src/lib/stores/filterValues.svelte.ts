/**
 * Current value of every active filter variable (Svelte 5 runes).
 *
 * Key   = variable name (e.g. "region", "start_date").
 * Value = the user-selected value; arrays for multiselect. An empty value
 *         ("" / [] / undefined) means "no filter" — the API neutralizes empty
 *         variables so all rows are returned for that dimension.
 *
 * Backed by `$state` so any reactive reader (`filterValues.current` in a
 * template, a `$derived`, or the re-execution `$effect` in dashboardStore)
 * updates automatically when a value changes.
 */
let values = $state<Record<string, unknown>>({});

export const filterValues = {
    /** Reactive snapshot of every filter value. */
    get current(): Record<string, unknown> {
        return values;
    },

    /** Set a single variable. Reassigns the object so `$state` readers update. */
    set(name: string, value: unknown): void {
        values = { ...values, [name]: value };
    },

    /** Clear every filter (e.g. when switching dashboards). */
    reset(): void {
        values = {};
    },
};
