import { cleanup, render, waitFor } from '@testing-library/svelte';
import { afterEach, expect, it, vi } from 'vitest';

const deferred = vi.hoisted(() => {
    let finish: () => void = () => {};
    const ready = new Promise<void>(resolve => { finish = resolve; });
    return { ready, finish, create: vi.fn(), loaded: vi.fn() };
});

vi.mock('monaco-editor', async () => {
    await deferred.ready;
    deferred.loaded();
    return { editor: { create: deferred.create, defineTheme: vi.fn() } };
});

import SQLEditor from './SQLEditor.svelte';
afterEach(() => { cleanup(); vi.restoreAllMocks(); });

it('does not create an editor if navigation removes it before Monaco finishes loading', async () => {
    const screen = render(SQLEditor, { value: 'SELECT 1' });
    expect(screen.getByText('Loading editor…')).toBeTruthy();
    screen.unmount();
    deferred.finish();
    await waitFor(() => expect(deferred.loaded).toHaveBeenCalledOnce());
    expect(deferred.create).not.toHaveBeenCalled();
});
