import type { ExecResult } from '$lib/api';
import type { FilterControl, FilterDomain } from '$lib/types';

/** Domain queries share the analytical budget with charts. Issue one at a time
 * per loader and stop work when its view is replaced. Credentials stay in the
 * caller's transport; ordinary failures retain the existing manual fallback. */
export async function fetchFilterDomains(options: {
    results: ExecResult[];
    isCurrent: () => boolean;
    fetch: (panelId: string, column: string, kind: 'distinct' | 'range') => Promise<FilterDomain>;
    onAccessFailure?: (error: unknown) => boolean;
}): Promise<Record<string, FilterDomain>> {
    const domains: Record<string, FilterDomain> = {};
    const seen = new Set<string>();
    for (const result of options.results) {
        for (const control of result.inference_result.filter_controls) {
            if (!options.isCurrent()) return domains;
            const kind = domainKind(control);
            if (!kind || seen.has(control.variable)) continue;
            seen.add(control.variable);
            try {
                const domain = await options.fetch(result.panel_id, control.column_name, kind);
                if (!options.isCurrent()) return domains;
                domains[control.variable] = domain;
            } catch (error) {
                if (options.onAccessFailure?.(error)) throw error;
            }
        }
    }
    return domains;
}

function domainKind(control: FilterControl): 'distinct' | 'range' | null {
    if (control.control_type === 'dropdown' || control.control_type === 'multiselect') return 'distinct';
    return control.control_type === 'range_slider' ? 'range' : null;
}
