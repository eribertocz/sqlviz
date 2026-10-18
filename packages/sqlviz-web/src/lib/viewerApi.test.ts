import { afterEach, describe, expect, it, vi } from 'vitest';
import { createViewerClient, ViewerAccessError } from './viewerApi';
import type { ExecResult } from './api';

afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks(); });

function response(body: unknown, status = 200): Response {
    return { ok: status === 200, status, json: async () => body } as Response;
}

describe('scoped viewer requests', () => {
    it('carries share and unlock credentials on listing, execution, domains and composition', async () => {
        const fetch = vi.fn(async () => response({ rows: [] }));
        vi.stubGlobal('fetch', fetch);
        const viewer = createViewerClient(() => 'share-A');
        viewer.setSession('session-A');
        await viewer.get('/api/v1/panels?dashboard_id=A');
        await viewer.post('/api/v1/panels/p1/execute');
        await viewer.post('/api/v1/panels/p1/filter-domain', { column: 'region', kind: 'distinct' });
        await viewer.recompose([{ panel_id: 'p1', inference_result: {}, data: [] } as unknown as ExecResult]);
        expect(fetch).toHaveBeenCalledTimes(4);
        for (const [, init] of fetch.mock.calls as unknown as [string, RequestInit][]) {
            expect(init.headers).toMatchObject({
                'X-SQLviz-Share': 'share-A', 'X-SQLviz-Viewer-Session': 'session-A',
            });
            expect(init.cache).toBe('no-store');
            expect(init.credentials).toBe('same-origin');
        }
        expect((fetch.mock.calls[1] as unknown as [string, RequestInit])[1].method).toBe('POST');
    });

    it('keeps sessions local to each viewer and out of localStorage', async () => {
        const fetch = vi.fn(async () => response({}));
        vi.stubGlobal('fetch', fetch);
        const stored = vi.spyOn(Storage.prototype, 'setItem');
        const first = createViewerClient(() => 'A');
        first.setSession('session-A');
        await first.get('/panels');
        await createViewerClient(() => 'B').get('/panels');
        const init = (fetch.mock.calls[1] as unknown as [string, RequestInit])[1];
        expect(init.headers).toMatchObject({ 'X-SQLviz-Share': 'B' });
        expect(init.headers).not.toHaveProperty('X-SQLviz-Viewer-Session');
        expect(stored).not.toHaveBeenCalled();
    });

    it.each([401, 403, 404])('exposes denial %s to the UI and drops the old session', async (status) => {
        const fetch = vi.fn().mockResolvedValueOnce(response({ detail: 'Denied' }, status))
            .mockResolvedValueOnce(response({}));
        vi.stubGlobal('fetch', fetch);
        const viewer = createViewerClient(() => 'A');
        viewer.setSession('old-session');
        await expect(viewer.post('/execute')).rejects.toBeInstanceOf(ViewerAccessError);
        await viewer.get('/panels');
        expect(fetch.mock.calls[1][1].headers).not.toHaveProperty('X-SQLviz-Viewer-Session');
    });

    it('does not turn a normal execution error into loss of credentials', async () => {
        const fetch = vi.fn().mockResolvedValueOnce(response({ detail: 'Bad query' }, 422))
            .mockResolvedValueOnce(response({}));
        vi.stubGlobal('fetch', fetch);
        const viewer = createViewerClient(() => 'A');
        viewer.setSession('valid-session');
        await expect(viewer.post('/execute')).rejects.toThrow('Bad query');
        await viewer.get('/panels');
        expect(fetch.mock.calls[1][1].headers['X-SQLviz-Viewer-Session']).toBe('valid-session');
    });

    it('composes an empty dashboard without issuing a request', async () => {
        const fetch = vi.fn();
        vi.stubGlobal('fetch', fetch);
        expect(await createViewerClient(() => 'A').recompose([])).toEqual({ rows: [] });
        expect(fetch).not.toHaveBeenCalled();
    });
});
