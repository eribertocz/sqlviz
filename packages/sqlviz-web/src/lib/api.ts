/** Shared JSON fetch helpers used by the dashboard domain store. */
import type { DashboardLayout, InferenceResult } from '$lib/types';

export type ExecResult = {
    panel_id: string;
    inference_result: InferenceResult;
    data: Record<string, unknown>[];
};

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
    const r = await fetch(path, {
        method: 'POST',
        headers: body !== undefined ? { 'Content-Type': 'application/json' } : {},
        body:    body !== undefined ? JSON.stringify(body) : undefined,
    });
    if (!r.ok) {
        const err = await r.json().catch(() => null) as { detail?: string } | null;
        throw new Error(err?.detail ?? `${r.status} ${r.statusText}`);
    }
    return r.json() as Promise<T>;
}

/** Sends executed panel results to /compose and merges the row data back into the response. */
export async function recompose(results: ExecResult[]): Promise<DashboardLayout> {
    const composeBody = results.map(r => ({
        panel_id: r.panel_id,
        inference_result: r.inference_result,
    }));
    const layoutResponse = await apiPost<DashboardLayout>('/api/v1/compose', composeBody);
    const dataMap = new Map(results.map(r => [r.panel_id, r.data]));
    return {
        ...layoutResponse,
        rows: layoutResponse.rows.map(row => ({
            panels: row.panels.map(p => ({
                ...p,
                data: dataMap.get(p.panel_id) ?? [],
            })),
        })),
    };
}

export async function apiPatch<T>(path: string, body: unknown): Promise<T> {
    const r = await fetch(path, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(body),
    });
    if (!r.ok) {
        const err = await r.json().catch(() => null) as { detail?: string } | null;
        throw new Error(err?.detail ?? `${r.status} ${r.statusText}`);
    }
    return r.json() as Promise<T>;
}
