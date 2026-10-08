import { flushSync } from 'svelte';
import { expect, it } from 'vitest';
import { dashboardCache, type CachedDashboard } from './dashboardCache.svelte';

it('caching a reactive view does not subscribe the writer to its own writes', () => {
    dashboardCache.clear();
    const entry: CachedDashboard = {
        sql: '', panelIds: [], panelSQLs: [], executedResults: [], layout: null,
        filterDomains: {}, filterValues: {},
    };
    const dispose = $effect.root(() => {
        let revision = $state(0);
        let writes = 0;
        $effect(() => {
            const sql = String(revision);
            writes += 1;
            dashboardCache.set('d', { ...entry, sql });
        });
        flushSync();
        expect(writes).toBe(1);
        revision += 1;
        flushSync();
        expect(writes).toBe(2);
        expect(dashboardCache.get('d')?.sql).toBe('1');
    });
    dispose();
    dashboardCache.clear();
});
