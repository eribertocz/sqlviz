import type { ExecResult } from '$lib/api';
import type { DashboardLayout, FilterDomain } from '$lib/types';

/**
 * A single dashboard's last-executed view, kept in memory so navigating back
 * to it restores the charts instantly instead of showing an empty editor.
 *
 * `sql` is the exact editor text that produced these results — it is the
 * invalidation key: the moment the draft diverges from it, the entry is stale
 * and must be dropped (the charts no longer match the query).
 */
export interface CachedDashboard {
    sql: string;
    panelIds: string[];
    panelSQLs: string[];
    executedResults: ExecResult[];
    layout: DashboardLayout | null;
    filterDomains: Record<string, FilterDomain>;
    filterValues: Record<string, unknown>;
}

/**
 * In-memory results cache for dashboard navigation (Svelte 5 class + `$state`
 * pattern — the modern idiom for complex reactive stores).
 *
 * The backing store is a reactive Map keyed by `dashboard_id`. It lives for the
 * lifetime of the running SQLviz session: results persist across sidebar
 * navigation but are intentionally NOT written to disk (a page reload starts
 * fresh, falling back to the "Last run X ago" hint + a manual re-run).
 *
 * `$state.raw` gives reference-level reactivity without deep-proxying the
 * (potentially large) result rows: every mutation replaces the Map wholesale,
 * so readers in reactive contexts still update while row data stays untouched.
 */
class DashboardCache {
    #entries = $state.raw(new Map<string, CachedDashboard>());

    /** The cached view for a dashboard, or undefined if none / invalidated. */
    get(id: string): CachedDashboard | undefined {
        return this.#entries.get(id);
    }

    /** Whether a (still-valid) cached view exists for this dashboard. */
    has(id: string): boolean {
        return this.#entries.has(id);
    }

    /** Store (or replace) the cached view for a dashboard. */
    set(id: string, entry: CachedDashboard): void {
        const next = new Map(this.#entries);
        next.set(id, entry);
        this.#entries = next;
    }

    /** Drop a dashboard's cached view (e.g. its SQL changed, or it was deleted). */
    invalidate(id: string): void {
        if (!this.#entries.has(id)) return;
        const next = new Map(this.#entries);
        next.delete(id);
        this.#entries = next;
    }

    /** Drop every cached view (e.g. on logout). */
    clear(): void {
        this.#entries = new Map();
    }

    get size(): number {
        return this.#entries.size;
    }
}

export const dashboardCache = new DashboardCache();
