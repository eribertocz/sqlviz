import { afterEach, expect, it, vi } from 'vitest';
import { apiDelete, apiGet, apiPatch, apiPost } from './api';

afterEach(() => vi.unstubAllGlobals());

it.each([apiGet, apiPost, apiPatch, apiDelete])('keeps a server conflict readable', async (request) => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(
        JSON.stringify({ detail: 'Panel changed concurrently.', code: 'panel_write_conflict' }),
        { status: 409 },
    )));
    await expect(request('/api/v1/test', {})).rejects.toThrow('Panel changed concurrently.');
});

it('formats validation messages and falls back for a non-JSON response', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(new Response(JSON.stringify({ detail: [
        { type: 'string_too_long', loc: ['body', 'value'], msg: 'Use at most 512 characters.' },
    ] }), { status: 422 })).mockResolvedValueOnce(new Response('Unavailable', { status: 503 })));
    await expect(apiPatch('/api/v1/test', {})).rejects.toThrow('Use at most 512 characters.');
    await expect(apiPatch('/api/v1/test', {})).rejects.toThrow('503');
});
