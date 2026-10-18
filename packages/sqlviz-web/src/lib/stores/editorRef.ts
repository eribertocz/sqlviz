import { writable } from 'svelte/store';

/** Imperative handle to the mounted Monaco editor instance. */
export interface EditorRef {
    /** Move cursor to an offset supplied by source analysis, in UTF-16 units. */
    focusOffset?: (offset: number) => void;
    /** Imperatively replace the editor content (used to clear on new dashboard). */
    setContent?: (text: string) => void;
}

export const editorRef = writable<EditorRef>({});
