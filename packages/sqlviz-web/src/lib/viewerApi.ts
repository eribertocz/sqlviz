/** Credentials belong to one mounted viewer and are never persisted to browser storage. */
import { recompose, type ExecResult } from '$lib/api';

export class ViewerAccessError extends Error {
    constructor(public status: number, message: string) {
        super(message);
    }
}

export function createViewerClient(shareToken: () => string) {
    let session: string | null = null;

    async function request<T>(method: 'GET' | 'POST', path: string, body?: unknown): Promise<T> {
        const headers: Record<string, string> = {
            Accept: 'application/json',
            'X-SQLviz-Share': shareToken(),
        };
        if (session) headers['X-SQLviz-Viewer-Session'] = session;
        if (body !== undefined) headers['Content-Type'] = 'application/json';
        const response = await fetch(path, {
            method,
            headers, cache: 'no-store', credentials: 'same-origin',
            body: body !== undefined ? JSON.stringify(body) : undefined,
        });
        if (!response.ok) {
            const error = await response.json().catch(() => null) as { detail?: string } | null;
            if ([401, 403, 404].includes(response.status)) {
                session = null;
                throw new ViewerAccessError(response.status, error?.detail ?? 'Access is no longer available.');
            }
            throw new Error(error?.detail ?? `${response.status} ${response.statusText}`);
        }
        return response.json() as Promise<T>;
    }

    async function post<T>(path: string, body?: unknown): Promise<T> {
        return request<T>('POST', path, body);
    }

    return {
        get: <T>(path: string) => request<T>('GET', path),
        post,
        recompose: (results: ExecResult[]) => recompose(results, post),
        setSession(value: string) {
            if (!value) throw new Error('The server did not provide a viewer session.');
            session = value;
        },
    };
}
