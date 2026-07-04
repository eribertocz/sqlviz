import { writable } from 'svelte/store';

/** Global edit-mode toggle (DOC6 §6). false = Preview, true = Edit. */
export const editMode = writable(false);
