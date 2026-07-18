import { writable } from 'svelte/store';

/** Imperative handle to the mounted Monaco editor instance. */
export interface EditorRef {
    /** Move cursor to the start of SQL statement at 0-based index. */
    focusStatement?: (idx: number) => void;
    /** Imperatively replace the editor content (used to clear on new dashboard). */
    setContent?: (text: string) => void;
}

export const editorRef = writable<EditorRef>({});
