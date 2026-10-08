import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/svelte';
import { afterEach, describe, expect, it, vi } from 'vitest';
import WorkspacePage from './workspace/[token]/+page.svelte';
import DashboardPage from './[token]/+page.svelte';

afterEach(async () => {
    cleanup();
    // Bits UI releases its shared body scroll lock on a 24 ms timeout.
    // Finish that cleanup while jsdom still owns document, even after revocation
    // unmounts an open dialog. Otherwise the callback can outlive this fixture.
    await new Promise(resolve => setTimeout(resolve, 40));
    vi.unstubAllGlobals();
});

describe.each([['workspace', WorkspacePage], ['dashboard', DashboardPage]] as const)('%s reader filter contract', (_, Page) => {
    function serve(failSecond = false, failureStatus = 500) {
        const request = vi.fn(async (url: string, init?: RequestInit) => {
            const body = init?.body ? JSON.parse(String(init.body)) : null;
            const panels = [{ id: 'first' }, { id: 'second' }];
            let data: unknown = [];
            if (url.startsWith('/view/')) data = {
                dashboard: { id: 'd1', name: 'Revenue' }, panels,
                dashboards: [{ id: 'd1', name: 'Revenue', folder_id: null, sort_order: 0 }], folders: [],
            };
            else if (url.includes('/panels?')) data = panels;
            else if (url.includes('/compose')) data = { rows: [] };
            else if (url.includes('/execute')) {
                const first = url.includes('/first/');
                const label = first ? 'Amount' : 'Limit';
                const variable = label.toLowerCase();
                data = { inference_result: { filter_controls: [{ variable, label, control_type: 'numeric',
                    column_name: variable, column_type: 'INTEGER', scope: 'global' }] }, data: [body?.variables ?? {}] };
            }
            const denied = failSecond && url.includes('/second/execute') && body;
            return { ok: !denied, status: denied ? failureStatus : 200, json: async () => denied ? { detail: 'Source unavailable' } : data } as Response;
        });
        vi.stubGlobal('fetch', request); return request;
    }

    it('runs a multi-filter draft once per affected panel only after Apply', async () => {
        const request = serve(); render(Page);
        const trigger = await screen.findByRole('button', { name: /^Dashboard filters:/ });
        await waitFor(() => expect((trigger as HTMLButtonElement).disabled).toBe(false));
        await fireEvent.click(trigger);
        await fireEvent.input(await screen.findByLabelText('Amount'), { target: { value: '12' } });
        await fireEvent.input(screen.getByLabelText('Limit'), { target: { value: '0' } });
        const filtered = () => request.mock.calls.filter(([, init]) => init?.body && JSON.parse(String(init.body)).variables);
        expect(filtered()).toHaveLength(0);
        await fireEvent.click(screen.getByRole('button', { name: 'Apply filters' }));
        await waitFor(() => expect(trigger.getAttribute('aria-label')).toContain('Limit: 0'));
        expect(filtered().map(([, init]) => JSON.parse(String(init!.body)).variables)).toEqual([{ amount: 12 }, { limit: 0 }]);
        expect(request.mock.calls.filter(([url]) => url.includes('/compose'))).toHaveLength(1);
    });
    it('keeps the applied summary unchanged after a partial source failure', async () => {
        serve(true); render(Page);
        const trigger = await screen.findByRole('button', { name: /^Dashboard filters:/ });
        await waitFor(() => expect((trigger as HTMLButtonElement).disabled).toBe(false));
        await fireEvent.click(trigger);
        await fireEvent.input(await screen.findByLabelText('Amount'), { target: { value: '12' } });
        await fireEvent.input(screen.getByLabelText('Limit'), { target: { value: '20' } });
        await fireEvent.click(screen.getByRole('button', { name: 'Apply filters' }));
        await screen.findByRole('alert');
        expect(trigger.getAttribute('aria-label')).toContain('All values');
        expect(trigger.getAttribute('aria-label')).not.toContain('Amount: 12');
        expect((screen.getByLabelText('Amount') as HTMLInputElement).value).toBe('12');
    });
    it.each([401, 403, 404])('removes protected context after access denial %s while applying', async status => {
        serve(true, status); render(Page);
        const trigger = await screen.findByRole('button', { name: /^Dashboard filters:/ });
        await waitFor(() => expect((trigger as HTMLButtonElement).disabled).toBe(false));
        await fireEvent.click(trigger);
        await fireEvent.input(await screen.findByLabelText('Amount'), { target: { value: '12' } });
        await fireEvent.input(screen.getByLabelText('Limit'), { target: { value: '20' } });
        await fireEvent.click(screen.getByRole('button', { name: 'Apply filters' }));
        await screen.findByText(/access has expired or was revoked/);
        expect(screen.queryByRole('button', { name: /^Dashboard filters:/ })).toBeNull();
        expect(screen.queryByRole('dialog', { name: 'Filters' })).toBeNull();
    });
});
