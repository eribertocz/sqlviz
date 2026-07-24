/**
 * Saved filter "views" per dashboard (Linear/Notion-style segments).
 *
 * A view is a named snapshot of the current filter values. Persisted in
 * localStorage, keyed by dashboard id, so combinations survive reloads without
 * a backend. Backed by `$state` so the header UI updates as views change.
 */
export type FilterView = {
    id: string;
    name: string;
    values: Record<string, unknown>;
};

const keyFor = (dashboardId: string) => `sqlviz-filter-views:${dashboardId}`;

let cache = $state<Record<string, FilterView[]>>({});

function load(dashboardId: string): void {
    if (cache[dashboardId]) return;
    let arr: FilterView[] = [];
    try {
        const raw = localStorage.getItem(keyFor(dashboardId));
        if (raw) arr = JSON.parse(raw) as FilterView[];
    } catch {
        arr = [];
    }
    cache = { ...cache, [dashboardId]: arr };
}

function persist(dashboardId: string, views: FilterView[]): void {
    cache = { ...cache, [dashboardId]: views };
    try {
        localStorage.setItem(keyFor(dashboardId), JSON.stringify(views));
    } catch {
        // Ignore quota / privacy-mode failures — views are a convenience.
    }
}

export const filterViews = {
    /** Reactive list of saved views for a dashboard. */
    list(dashboardId: string): FilterView[] {
        load(dashboardId);
        return cache[dashboardId] ?? [];
    },

    /** Save the given values as a new named view; returns it. */
    save(dashboardId: string, name: string, values: Record<string, unknown>): FilterView {
        load(dashboardId);
        const view: FilterView = {
            id: crypto.randomUUID(),
            name: name.trim(),
            values: { ...values },
        };
        persist(dashboardId, [...(cache[dashboardId] ?? []), view]);
        return view;
    },

    /** Remove a saved view by id. */
    remove(dashboardId: string, id: string): void {
        load(dashboardId);
        persist(dashboardId, (cache[dashboardId] ?? []).filter(v => v.id !== id));
    },
};
