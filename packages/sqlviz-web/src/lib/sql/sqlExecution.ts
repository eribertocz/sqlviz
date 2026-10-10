import { apiPost, type ExecResult } from '$lib/api';
import type { DashboardLayout } from '$lib/types';

export type SqlDefinitionReference = { version: 1; dashboard_id: string; revision: string };
export type SqlExecutionReference = { version: 1; panel_id: string; definition: SqlDefinitionReference };
export type BoundExecResult = ExecResult & { execution_reference: SqlExecutionReference };

function sameDefinition(value: unknown, definition: SqlDefinitionReference): boolean {
    if (!value || typeof value !== 'object') return false;
    const candidate = value as SqlDefinitionReference;
    return candidate.version === 1 && candidate.dashboard_id === definition.dashboard_id &&
        typeof candidate.revision === 'string' &&
        /^sql-definition-v1:[0-9a-f]{64}$/.test(candidate.revision) && candidate.revision === definition.revision;
}

/** Provenance is verified before results can enter the Run view or composition. */
export function requireSqlExecution(value: unknown, definition: SqlDefinitionReference, panelId: string): BoundExecResult {
    const fail = () => { throw new Error('Could not verify the executed definition. Reload before running again.'); };
    if (!value || typeof value !== 'object') return fail();
    const result = value as BoundExecResult;
    const reference = result.execution_reference;
    if (reference?.version !== 1 || reference.panel_id !== panelId || !sameDefinition(reference.definition, definition) ||
        !result.inference_result || typeof result.inference_result !== 'object' || !Array.isArray(result.data)) return fail();
    return { panel_id: panelId, inference_result: result.inference_result, data: result.data, execution_reference: reference };
}

/** Author Run composes against its confirmed definition; legacy readers stay separate. */
export async function recomposeSqlRun(results: BoundExecResult[], definition: SqlDefinitionReference,
    post: <T>(path: string, body?: unknown) => Promise<T> = apiPost): Promise<DashboardLayout> {
    results.forEach(result => requireSqlExecution(result, definition, result.panel_id));
    const ids = new Set(results.map(result => result.panel_id));
    if (ids.size !== results.length) throw new Error('Execution contains duplicate panels.');
    const response = await post<DashboardLayout & { definition: SqlDefinitionReference }>(
        `/api/v1/dashboards/${encodeURIComponent(definition.dashboard_id)}/sql-script/compose`, {
            definition, panels: results.map(result => ({ panel_id: result.panel_id,
                inference_result: result.inference_result, execution_reference: result.execution_reference })),
        });
    if (!sameDefinition(response?.definition, definition) || !Array.isArray(response.rows) ||
        response.rows.some(row => !Array.isArray(row?.panels) || row.panels.some(panel => typeof panel?.panel_id !== 'string'))) {
        throw new Error('Could not verify the composed definition. Reload before running again.');
    }
    const composedIds = response.rows.flatMap(row => row.panels.map(panel => panel.panel_id));
    if (
        composedIds.length !== ids.size || new Set(composedIds).size !== ids.size || composedIds.some(id => !ids.has(id))) {
        throw new Error('Could not verify the composed definition. Reload before running again.');
    }
    const data = new Map(results.map(result => [result.panel_id, result.data]));
    return { rows: response.rows.map(row => ({ ...row, panels: row.panels.map(panel => ({
        ...panel, data: data.get(panel.panel_id)!,
    })) })) };
}
