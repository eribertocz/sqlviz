import type { ExecResult } from '$lib/api';
import type { DashboardLayout } from '$lib/types';
import { copyFilterValues, filterVariables, sameFilterValue, validateFilterValues, type FilterValues } from './filterContext';

export function patchFilterResults(layout: DashboardLayout, results: ExecResult[]): DashboardLayout {
    const byId = new Map(results.map(result => [result.panel_id, result]));
    return { ...layout, rows: layout.rows.map(row => ({ ...row, panels: row.panels.map(panel => {
        const result = byId.get(panel.panel_id);
        return result ? { ...panel, inference_result: { ...result.inference_result,
            col_span: panel.inference_result.col_span, row_span: panel.inference_result.row_span,
            panel_height_px: panel.inference_result.panel_height_px }, data: result.data } : panel;
    }) })) };
}

/** One runtime per mounted reader/store. No credentials, globals or author stores. */
export function createFilterRuntime(options: {
    getScope: () => unknown;
    getResults: () => ExecResult[];
    getValues: () => FilterValues;
    execute: (panelId: string, variables: FilterValues) => Promise<Omit<ExecResult, 'panel_id'>>;
    commit: (results: ExecResult[], values: FilterValues) => void;
    onAccessFailure?: (error: unknown) => boolean;
}) {
    let revision = 0;
    let busy = $state(false);
    let error = $state<string | null>(null);
    let pending = $state<FilterValues | null>(null);

    function reset() { revision++; busy = false; error = null; pending = null; }

    async function apply(values: FilterValues): Promise<boolean> {
        const request = ++revision;
        const scope = options.getScope();
        const original = options.getResults();
        const current = () => request === revision && scope === options.getScope() && original === options.getResults();
        busy = true; error = null; pending = null;
        try {
            const controls = original.flatMap(result => result.inference_result.filter_controls);
            const target = validateFilterValues(controls, values);
            pending = target;
            const applied = copyFilterValues(options.getValues());
            const changed = new Set([...Object.keys(target), ...Object.keys(applied)]
                .filter(key => !sameFilterValue(target[key], applied[key])));
            const updated = [...original];
            for (let i = 0; i < original.length; i++) {
                const keys = original[i].inference_result.filter_controls.flatMap(filterVariables);
                if (!keys.some(key => changed.has(key))) continue;
                const variables = Object.fromEntries(keys.map(key => [key, target[key] ?? '']));
                const result = await options.execute(original[i].panel_id, variables);
                if (!current()) return false;
                if (result.inference_result.execution_state === 'failed') throw new Error('A chart could not be updated.');
                updated[i] = { ...result, panel_id: original[i].panel_id };
            }
            if (!current()) return false;
            options.commit(updated, target);
            pending = null;
            return true;
        } catch (cause) {
            // Revocation is session-wide, including a denial from an older request.
            if (options.onAccessFailure?.(cause)) return false;
            if (current()) error = cause instanceof Error ? cause.message : 'The filters could not be applied. Try again.';
            return false;
        } finally {
            if (request === revision) busy = false;
        }
    }

    return { apply, reset, get busy() { return busy; }, get error() { return error; }, get pending() { return pending; } };
}
