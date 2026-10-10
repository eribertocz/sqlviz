import { apiPost, type ExecResult } from '$lib/api';
import type { DashboardLayout } from '$lib/types';

export type SqlDefinitionReference = { version: 1; dashboard_id: string; revision: string };
export type SqlExecutionReference = { version: 1; panel_id: string; definition: SqlDefinitionReference };
export type BoundExecResult = ExecResult & { execution_reference: SqlExecutionReference;
    execution_receipt: string; query_executed: boolean };
export type SqlRunComposition = { layout: DashboardLayout; completionReceipt: string | null };

function validReceipt(value: unknown): value is string {
    return typeof value === 'string' && value.length <= 2048 && /^[A-Za-z0-9_-]+\.[0-9a-f]{64}$/.test(value);
}

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
        !result.inference_result || typeof result.inference_result !== 'object' || !Array.isArray(result.data) ||
        !validReceipt(result.execution_receipt) || typeof result.query_executed !== 'boolean') return fail();
    return { panel_id: panelId, inference_result: result.inference_result, data: result.data, execution_reference: reference,
        execution_receipt: result.execution_receipt, query_executed: result.query_executed };
}

/** Author Run composes against its confirmed definition; legacy readers stay separate. */
export async function recomposeSqlRun(results: BoundExecResult[], definition: SqlDefinitionReference,
    post: <T>(path: string, body?: unknown) => Promise<T> = apiPost): Promise<SqlRunComposition> {
    results.forEach(result => requireSqlExecution(result, definition, result.panel_id));
    const ids = new Set(results.map(result => result.panel_id));
    if (ids.size !== results.length) throw new Error('Execution contains duplicate panels.');
    const response = await post<DashboardLayout & { definition: SqlDefinitionReference; completion_receipt: string | null }>(
        `/api/v1/dashboards/${encodeURIComponent(definition.dashboard_id)}/sql-script/compose`, {
            definition, panels: results.map(result => ({ panel_id: result.panel_id,
                inference_result: result.inference_result, execution_reference: result.execution_reference,
                execution_receipt: result.execution_receipt })),
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
    const complete = results.length > 0 && results.every(result => result.query_executed);
    if (complete ? !validReceipt(response.completion_receipt) : response.completion_receipt !== null) {
        throw new Error('Could not verify Run completion. Reload before running again.');
    }
    return { completionReceipt: response.completion_receipt, layout: { rows: response.rows.map(row => ({ ...row, panels: row.panels.map(panel => ({
        ...panel, data: data.get(panel.panel_id)!,
    })) })) } };
}

export async function completeSqlRun(receipt: string, definition: SqlDefinitionReference, source: string,
    post: <T>(path: string, body?: unknown) => Promise<T> = apiPost): Promise<{ lastRunAt: string; lastRunSql: string }> {
    if (!validReceipt(receipt)) throw new Error('Could not verify Run completion. Run again.');
    const response = await post<{ definition: SqlDefinitionReference; last_run_at: string; last_run_sql: string }>(
        `/api/v1/dashboards/${encodeURIComponent(definition.dashboard_id)}/sql-script/complete`,
        { definition, completion_receipt: receipt });
    if (!sameDefinition(response?.definition, definition) || response.last_run_sql !== source ||
        typeof response.last_run_at !== 'string' || !/(Z|[+-]\d{2}:\d{2})$/.test(response.last_run_at) ||
        !Number.isFinite(Date.parse(response.last_run_at))) {
        throw new Error('Could not verify the last Run acknowledgement. Reload before running again.');
    }
    return { lastRunAt: response.last_run_at, lastRunSql: response.last_run_sql };
}
