<script lang="ts">
    import { onDestroy, onMount } from 'svelte';
    import { editorRef } from '$lib/stores/editorRef';

    let {
        value = $bindable(''),
        onRun,
        disabled = false,
    }: {
        value?: string;
        onRun?: () => void;
        disabled?: boolean;
    } = $props();

    let container: HTMLDivElement;
    let editor: any = null;
    let monacoReady = $state(false);
    // Guard against setValue triggering onDidChangeModelContent
    let syncing = false;

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

            editor = monaco.editor.create(container, {
                value,
                language: 'sql',
                theme: 'sqlviz-dark',
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
                lineNumbersMinChars: 3,
                glyphMargin: false,
                overviewRulerLanes: 0,
            });

            // Ctrl+Enter and Ctrl+S both trigger run
            editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => onRun?.());
            editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS,  () => onRun?.());

            editor.onDidChangeModelContent(() => {
                syncing = true;
                value = editor.getValue();
                syncing = false;
            });

            // Register focusStatement so +page.svelte can focus a specific SQL statement
            editorRef.set({
                focusStatement(idx: number) {
                    if (!editor) return;
                    const model = editor.getModel();
                    if (!model) return;

                    const content = editor.getValue();
                    let charIdx = 0;

                    if (idx > 0) {
                        let count = 0;
                        for (let c = 0; c < content.length; c++) {
                            if (content[c] === ';') {
                                count++;
                                if (count === idx) {
                                    charIdx = c + 1;
                                    break;
                                }
                            }
                        }
                        // Skip leading whitespace/newlines after the semicolon
                        while (
                            charIdx < content.length &&
                            (content[charIdx] === '\n' ||
                             content[charIdx] === '\r' ||
                             content[charIdx] === ' ')
                        ) {
                            charIdx++;
                        }
                    }

                    const pos = model.getPositionAt(charIdx);
                    editor.revealLineInCenter(pos.lineNumber);
                    editor.setPosition(pos);
                    editor.focus();
                },
            });

            monacoReady = true;
            // Force Monaco to measure its container after it becomes visible,
            // then hand focus so the user can type immediately.
            requestAnimationFrame(() => {
                editor?.layout();
                editor?.focus();
            });
        } catch (err) {
            console.error('[SQLEditor] Monaco init failed:', err);
            // Make container visible even if Monaco failed — shows empty dark area
            // rather than an infinite "Loading editor…" spinner.
            monacoReady = true;
        }
    });

    // Async onMount cannot return a cleanup fn — use onDestroy instead
    onDestroy(() => {
        editorRef.set({});
        editor?.dispose();
        editor = null;
    });

    // Sync external value changes into the editor (e.g. loading saved SQL on mount)
    $effect(() => {
        if (editor && !syncing && editor.getValue() !== value) {
            const pos = editor.getPosition();
            editor.setValue(value);
            if (pos) editor.setPosition(pos);
        }
    });

    $effect(() => {
        if (editor) editor.updateOptions({ readOnly: disabled });
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
