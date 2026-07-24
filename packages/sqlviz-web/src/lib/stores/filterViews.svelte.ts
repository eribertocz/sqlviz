/**
 * Saved filter "views" per dashboard (Linear/Notion-style segments).
 *
 * A view is a named snapshot of the current filter values. Persisted in
 * localStorage, keyed by dashboard id, so combinations survive reloads without
 * a backend.
 *
 * Reactivity note: the parsed data lives in a plain (non-reactive) map so that
 * `list()` — which is called inside components' `$derived` — never writes
 * `$state` during a read (that would throw `state_unsafe_mutation`). A separate
 * `$state` version counter is read by `list()` and bumped by `save`/`remove`,
 * which is what drives the UI to re-render.
 */
export type FilterView = {
    id: string;
    name: string;
    values: Record<string, unknown>;
};

const keyFor = (dashboardId: string) => `sqlviz-filter-views:${dashboardId}`;

const mem: Record<string, FilterView[]> = {};
let version = $state(0);

function ensureLoaded(dashboardId: string): void {
    if (dashboardId in mem) return;
    let arr: FilterView[] = [];
    try {
        const raw = localStorage.getItem(keyFor(dashboardId));
        if (raw) arr = JSON.parse(raw) as FilterView[];
    } catch {
        arr = [];
    }
    mem[dashboardId] = arr;
}

function persist(dashboardId: string, views: FilterView[]): void {
    mem[dashboardId] = views;
    try {
        localStorage.setItem(keyFor(dashboardId), JSON.stringify(views));
    } catch {
        // Ignore quota / privacy-mode failures — views are a convenience.
    }
    version++;
}

export const filterViews = {
    /** Reactive list of saved views for a dashboard. */
    list(dashboardId: string): FilterView[] {
        void version; // subscribe to changes without mutating state here
        ensureLoaded(dashboardId);
        return mem[dashboardId] ?? [];
    },

    /** Save the given values as a new named view; returns it. */
    save(dashboardId: string, name: string, values: Record<string, unknown>): FilterView {
        ensureLoaded(dashboardId);
        const view: FilterView = {
            id: crypto.randomUUID(),
            name: name.trim(),
            values: { ...values },
        };
        persist(dashboardId, [...(mem[dashboardId] ?? []), view]);
        return view;
    },

    /** Remove a saved view by id. */
    remove(dashboardId: string, id: string): void {
        ensureLoaded(dashboardId);
        persist(dashboardId, (mem[dashboardId] ?? []).filter(v => v.id !== id));
    },
};
