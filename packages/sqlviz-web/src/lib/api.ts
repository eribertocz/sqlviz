/** Shared JSON fetch helpers used by the dashboard domain store. */
import type { DashboardLayout, InferenceResult } from '$lib/types';

export type ExecResult = {
    panel_id: string;
    inference_result: InferenceResult;
    data: Record<string, unknown>[];
};

/** Keep server validation messages readable without rendering raw JSON values. */
async function responseError(response: Response): Promise<Error> {
    const body: unknown = await response.json().catch(() => null);
    const detail = body && typeof body === 'object' && 'detail' in body ? body.detail : null;
    if (typeof detail === 'string') return new Error(detail);
    if (Array.isArray(detail)) {
        const messages = detail.flatMap(item =>
            item && typeof item === 'object' && 'msg' in item && typeof item.msg === 'string'
                ? [item.msg] : [],
        );
        if (messages.length) return new Error(messages.slice(0, 3).join('; '));
    }
    return new Error(`${response.status} ${response.statusText}`.trim());
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
    const r = await fetch(path, {
        method: 'POST',
        headers: body !== undefined ? { 'Content-Type': 'application/json' } : {},
        body:    body !== undefined ? JSON.stringify(body) : undefined,
    });
    if (!r.ok) {
        throw await responseError(r);
    }
    return r.json() as Promise<T>;
}

/** Sends executed panel results to /compose and merges the row data back into the response. */
export async function recompose(
    results: ExecResult[],
    post: <T>(path: string, body?: unknown) => Promise<T> = apiPost,
): Promise<DashboardLayout> {
    if (results.length === 0) return { rows: [] };
    const composeBody = results.map(r => ({
        panel_id: r.panel_id,
        inference_result: r.inference_result,
    }));
    const layoutResponse = await post<DashboardLayout>('/api/v1/compose', composeBody);
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

export async function apiGet<T>(path: string): Promise<T> {
    const r = await fetch(path);
    if (!r.ok) {
        throw await responseError(r);
    }
    return r.json() as Promise<T>;
}

export async function apiDelete(path: string): Promise<void> {
    const r = await fetch(path, { method: 'DELETE' });
    if (!r.ok && r.status !== 204) {
        throw await responseError(r);
    }
}

export async function apiPatch<T>(path: string, body: unknown): Promise<T> {
    const r = await fetch(path, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(body),
    });
    if (!r.ok) {
        throw await responseError(r);
    }
    return r.json() as Promise<T>;
}
