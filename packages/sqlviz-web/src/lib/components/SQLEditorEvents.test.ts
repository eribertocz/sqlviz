import { cleanup, render, waitFor } from '@testing-library/svelte';
import { get } from 'svelte/store';
import { editorRef } from '$lib/stores/editorRef';
import { afterEach, expect, it, vi } from 'vitest';
import SQLEditor from './SQLEditor.svelte';

const mock = vi.hoisted(() => ({ create: vi.fn() }));
vi.mock('monaco-editor', () => ({ KeyMod: { CtrlCmd: 2048 }, KeyCode: { Enter: 3, KeyS: 49 },
    editor: { create: mock.create, defineTheme: vi.fn(), setTheme: vi.fn() } }));
afterEach(() => { cleanup(); vi.restoreAllMocks(); });

function mountedEditor() {
    let text = 'SELECT 1';
    let notify: (event: unknown) => void = () => {};
    const editor = { getValue: () => text, getPosition: () => null, setPosition: vi.fn(),
        setValue: vi.fn((next: string) => {
            const length = text.length; text = next;
            notify({ isFlush: true, changes: [{ rangeOffset: 0, rangeLength: length, text: next }] });
        }),
        onDidChangeModelContent: (listener: typeof notify) => { notify = listener; },
        addCommand: vi.fn(), layout: vi.fn(), focus: vi.fn(), dispose: vi.fn(), updateOptions: vi.fn(),
    };
    mock.create.mockReturnValue(editor);
    return { editor, edit(next: string, changes: unknown[]) { text = next; notify({ isFlush: false, changes }); } };
}

it('emits the precise edit once, while external and imperative source updates remain guarded', async () => {
    const model = mountedEditor(); const onEdit = vi.fn();
    const screen = render(SQLEditor, { value: 'SELECT 1', onEdit });
    await waitFor(() => expect(model.editor.updateOptions).toHaveBeenCalled());
    model.edit('SELECT 10', [{ rangeOffset: 8, rangeLength: 0, text: '0' }]);
    expect(onEdit).toHaveBeenCalledExactlyOnceWith({ before: 'SELECT 1', after: 'SELECT 10', isFlush: false,
        changes: [{ rangeOffset: 8, rangeLength: 0, text: '0' }] });
    await screen.rerender({ value: 'SELECT 2', disabled: true });
    await waitFor(() => expect(model.editor.getValue()).toBe('SELECT 2'));
    expect(onEdit).toHaveBeenCalledOnce();
    expect(model.editor.updateOptions).toHaveBeenLastCalledWith({ readOnly: true });
    get(editorRef).setContent?.('SELECT 3');
    expect(onEdit).toHaveBeenCalledOnce();
    model.edit('SELECT 30', [{ rangeOffset: 8, rangeLength: 0, text: '0' }]);
    expect(onEdit).toHaveBeenLastCalledWith(expect.objectContaining({ before: 'SELECT 3', after: 'SELECT 30' }));
});

it('rejecting an obsolete model event restores current props without sending a second edit', async () => {
    const model = mountedEditor(); const onEdit = vi.fn().mockReturnValue(false);
    render(SQLEditor, { value: 'SELECT 1', onEdit });
    await waitFor(() => expect(model.editor.updateOptions).toHaveBeenCalled());
    model.edit('SELECT 999', [{ rangeOffset: 7, rangeLength: 1, text: '999' }]);
    expect(model.editor.getValue()).toBe('SELECT 1');
    expect(onEdit).toHaveBeenCalledOnce();
});
