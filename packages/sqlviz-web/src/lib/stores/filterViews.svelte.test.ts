import { flushSync } from 'svelte';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { filterViews } from './filterViews.svelte';

beforeEach(() => localStorage.clear());
afterEach(() => localStorage.clear());

// Dashboard ids are unique per test so the store's in-memory cache (which
// deliberately outlives a single component) can't leak between them.
let n = 0;
const freshId = () => `dash-${++n}`;

describe('filterViews — persistence', () => {
    it('saves a named snapshot and reads it back', () => {
        const id = freshId();
        filterViews.save(id, 'Q1 North', { region: 'North', quarter: 'Q1' });

        const [view] = filterViews.list(id);
        expect(view.name).toBe('Q1 North');
        expect(view.values).toEqual({ region: 'North', quarter: 'Q1' });
        expect(view.id).toBeTruthy();
    });

    it('writes through to localStorage under a per-dashboard key', () => {
        const id = freshId();
        filterViews.save(id, 'Saved', { region: 'South' });

        const raw = localStorage.getItem(`sqlviz-filter-views:${id}`);
        expect(raw).toBeTruthy();
        expect(JSON.parse(raw!)[0].values).toEqual({ region: 'South' });
    });

    it('snapshots the values, so later filter edits do not mutate the view', () => {
        const id = freshId();
        const live: Record<string, unknown> = { region: 'North' };
        filterViews.save(id, 'Snapshot', live);

        live.region = 'South';
        expect(filterViews.list(id)[0].values).toEqual({ region: 'North' });
    });

    it('keeps views of different dashboards apart', () => {
        const a = freshId();
        const b = freshId();
        filterViews.save(a, 'A view', { region: 'North' });

        expect(filterViews.list(b)).toHaveLength(0);
        expect(filterViews.list(a)).toHaveLength(1);
    });

    it('gives every view a distinct id and removes only the requested one', () => {
        const id = freshId();
        const first = filterViews.save(id, 'First', { a: 1 });
        const second = filterViews.save(id, 'Second', { a: 2 });
        expect(first.id).not.toBe(second.id);

        filterViews.remove(id, first.id);
        expect(filterViews.list(id).map(v => v.name)).toEqual(['Second']);
    });

    it('survives a corrupt localStorage entry instead of throwing', () => {
        const id = freshId();
        localStorage.setItem(`sqlviz-filter-views:${id}`, '{not json');
        expect(filterViews.list(id)).toEqual([]);
    });
});

// The pill and its list are driven by a `$derived` over `list()`. The store
// keeps parsed data in a plain object and bumps a `$state` counter on write, so
// this asserts that counter really is what re-renders the UI.
describe('filterViews — reactivity', () => {
    it('re-runs a $derived over list() after save and remove', () => {
        const id = freshId();
        const cleanup = $effect.root(() => {
            const names = $derived(filterViews.list(id).map(v => v.name));
            // Read through a closure, the way a template would — reading the
            // derived directly here would capture only its initial value.
            const read = () => names;
            expect(read()).toEqual([]);

            filterViews.save(id, 'Q1', {});
            flushSync();
            expect(read()).toEqual(['Q1']);

            const extra = filterViews.save(id, 'Q2', {});
            flushSync();
            expect(read()).toEqual(['Q1', 'Q2']);

            filterViews.remove(id, extra.id);
            flushSync();
            expect(read()).toEqual(['Q1']);
        });
        cleanup();
    });
});

// `crypto.randomUUID` is exposed only in secure contexts. Dashboards are shared
// over http://<LAN-IP>, where it is undefined — saving a view must still work.
describe('filterViews — insecure context (LAN viewer)', () => {
    it('saves a view when crypto.randomUUID is unavailable', () => {
        const original = crypto.randomUUID;
        // `randomUUID` lives on Crypto.prototype, so it has to be shadowed by an
        // own property — deleting it would leave the inherited one in place.
        Object.defineProperty(crypto, 'randomUUID', { value: undefined, configurable: true });
        expect(crypto.randomUUID).toBeUndefined();
        try {
            const id = freshId();
            const view = filterViews.save(id, 'From a phone', { region: 'North' });
            expect(view.id).toBeTruthy();
            expect(filterViews.list(id)).toHaveLength(1);

            const other = filterViews.save(id, 'Second', {});
            expect(other.id).not.toBe(view.id);
        } finally {
            Object.defineProperty(crypto, 'randomUUID', { value: original, configurable: true });
        }
    });
});
