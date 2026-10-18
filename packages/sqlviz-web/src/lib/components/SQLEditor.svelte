<script lang="ts">
    import { onDestroy, onMount } from 'svelte';
    import { editorRef } from '$lib/stores/editorRef';
    import type * as Monaco from 'monaco-editor';
    import type { SqlEditorChange } from '$lib/sql/sqlIdentityDraft';

    let {
        value = $bindable(''),
        onRun,
        onEdit,
        disabled = false,
        theme = 'dark',
    }: {
        value?: string;
        onRun?: () => void;
        onEdit?: (event: SqlEditorChange) => boolean | void;
        disabled?: boolean;
        theme?: 'dark' | 'light';
    } = $props();

    let container: HTMLDivElement;
    let editor: any = null;
    let monacoInstance: any = null;
    let monacoReady = $state(false);
    let destroyed = false;
    let focusFrame = 0;
    // Guard against setValue triggering onDidChangeModelContent
    let syncing = false;
    let modelSource = '';

    function setEditorContent(text: string) {
        syncing = true;
        try {
            editor.setValue(text);
            modelSource = editor.getValue();
        } finally { syncing = false; }
    }

    onMount(async () => {
        // Set MonacoEnvironment before importing monaco-editor.
        // Classic blob worker: avoids module-worker browser compatibility issues.
        // Monaco runs in main-thread mode for SQL (no language server needed).
        if (!(window as any).MonacoEnvironment) {
            (window as any).MonacoEnvironment = {
                getWorker(_id: string, _label: string) {
                    return new Worker(
                        URL.createObjectURL(
                            new Blob(['self.onmessage=function(){}'], { type: 'text/javascript' })
                        )
                    );
                },
            };
        }

        try {
            const monaco = await import('monaco-editor');
            // Navigation or focus changes may remove this editor while its
            // lazy import is still pending. Never create an orphan instance.
            if (destroyed) return;

            monaco.editor.defineTheme('sqlviz-dark', {
                base: 'vs-dark',
                inherit: true,
                rules: [
                    { token: 'keyword', foreground: 'a78bfa' },
                    { token: 'string',  foreground: '22c55e' },
                    { token: 'comment', foreground: '64748b', fontStyle: 'italic' },
                    { token: 'number',  foreground: 'f59e0b' },
                ],
                colors: {
                    'editor.background':                '#0f172a',
                    'editor.foreground':                '#f1f5f9',
                    'editor.lineHighlightBackground':   '#1e293b',
                    'editor.selectionBackground':       '#6366f133',
                    'editorLineNumber.foreground':      '#475569',
                    'editorLineNumber.activeForeground':'#94a3b8',
                    'editorCursor.foreground':          '#6366f1',
                    'scrollbarSlider.background':       '#334155',
                    'scrollbarSlider.hoverBackground':  '#475569',
                    'editorBracketMatch.background':    '#6366f120',
                    'editorBracketMatch.border':        '#6366f1',
                },
            });

            monaco.editor.defineTheme('sqlviz-light', {
                base: 'vs',
                inherit: true,
                rules: [
                    { token: 'keyword', foreground: '4f46e5' },
                    { token: 'string',  foreground: '16a34a' },
                    { token: 'comment', foreground: '64748b', fontStyle: 'italic' },
                    { token: 'number',  foreground: 'd97706' },
                ],
                colors: {
                    'editor.background':                '#ffffff',
                    'editor.foreground':                '#0f172a',
                    'editor.lineHighlightBackground':   '#f8fafc',
                    'editor.selectionBackground':       '#6366f133',
                    'editorLineNumber.foreground':      '#94a3b8',
                    'editorLineNumber.activeForeground':'#64748b',
                    'editorCursor.foreground':          '#6366f1',
                    'scrollbarSlider.background':       '#e2e8f0',
                    'scrollbarSlider.hoverBackground':  '#cbd5e1',
                    'editorBracketMatch.background':    '#6366f120',
                    'editorBracketMatch.border':        '#6366f1',
                },
            });

            editor = monaco.editor.create(container, {
                value,
                language: 'sql',
                theme: theme === 'light' ? 'sqlviz-light' : 'sqlviz-dark',
                // Monaco observes its own container, including drawer height
                // and sidebar/inspector width changes, without recreating it.
                automaticLayout: true,
                minimap: { enabled: false },
                fontSize: 13,
                fontFamily: "'JetBrains Mono', 'Cascadia Code', 'Fira Code', 'Consolas', monospace",
                lineNumbers: 'on',
                scrollBeyondLastLine: false,
                wordWrap: 'off',
                tabSize: 4,
                renderLineHighlight: 'line',
                padding: { top: 12, bottom: 12 },
                folding: false,
                // Disable worker-backed word occurrences until the SQL worker
                // is implemented. Pending highlighter tasks can reject with
                // "Canceled" when this editor is disposed.
                occurrencesHighlight: 'off',
                lineNumbersMinChars: 3,
                glyphMargin: false,
                overviewRulerLanes: 0,
            });

            // Ctrl+Enter and Ctrl+S both trigger run
            editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => onRun?.());
            editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS,  () => onRun?.());

            modelSource = editor.getValue();
            editor.onDidChangeModelContent((event: Monaco.editor.IModelContentChangedEvent) => {
                if (syncing) return;
                const after = editor.getValue();
                const accepted = onEdit?.({ before: modelSource, after, isFlush: event.isFlush,
                    changes: event.changes.map(change => ({ rangeOffset: change.rangeOffset,
                        rangeLength: change.rangeLength, text: change.text })) });
                if (accepted === false) { setEditorContent(value); return; }
                modelSource = after;
                value = after;
            });

            // The backend supplies statement positions; Monaco does not parse SQL.
            editorRef.set({
                focusOffset(offset: number) {
                    if (!editor) return;
                    const model = editor.getModel();
                    if (!model) return;

                    if (!Number.isInteger(offset) || offset < 0 || offset > editor.getValue().length) return;
                    const pos = model.getPositionAt(offset);
                    editor.revealLineInCenter(pos.lineNumber);
                    editor.setPosition(pos);
                    editor.focus();
                },
                setContent(text: string) {
                    if (!editor || editor.getValue() === text) return;
                    setEditorContent(text);
                    value = text;
                },
            });

            monacoInstance = monaco;
            monacoReady = true;
            // Force Monaco to measure its container after it becomes visible,
            // then hand focus so the user can type immediately.
            focusFrame = requestAnimationFrame(() => {
                editor?.layout();
                editor?.focus();
            });
        } catch (err) {
            if (destroyed) return;
            console.error('[SQLEditor] Monaco init failed:', err);
            // Make container visible even if Monaco failed — shows empty dark area
            // rather than an infinite "Loading editor…" spinner.
            monacoReady = true;
        }
    });

    // Async onMount cannot return a cleanup fn — use onDestroy instead
    onDestroy(() => {
        destroyed = true;
        if (focusFrame) cancelAnimationFrame(focusFrame);
        editorRef.set({});
        editor?.dispose();
        editor = null;
    });

    // Sync external value changes into the editor (e.g. loading saved SQL on mount)
    $effect(() => {
        const text = value;
        if (monacoReady && editor && !syncing && editor.getValue() !== text) {
            const pos = editor.getPosition();
            setEditorContent(text);
            if (pos) editor.setPosition(pos);
        }
    });

    $effect(() => {
        if (monacoReady && editor) editor.updateOptions({ readOnly: disabled });
    });

    $effect(() => {
        if (!monacoReady || !monacoInstance || !editor) return;
        monacoInstance.editor.setTheme(theme === 'light' ? 'sqlviz-light' : 'sqlviz-dark');
    });
</script>

<div class="editor-host">
    {#if !monacoReady}
        <div class="editor-loading">Loading editor…</div>
    {/if}
    <div bind:this={container} class="editor-container" class:hidden={!monacoReady}></div>
</div>

<style>
    .editor-host {
        position: relative;
        width: 100%;
        height: 100%;
    }

    .editor-loading {
        position: absolute;
        inset: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--sqlviz-text-muted);
        font-size: 0.875rem;
        background: #0f172a;
        font-family: var(--sqlviz-font-mono);
    }

    .editor-container {
        width: 100%;
        height: 100%;
    }

    .hidden {
        visibility: hidden;
    }
</style>
