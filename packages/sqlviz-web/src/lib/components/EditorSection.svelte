<script lang="ts">
    import { Loader2, Play, X, ChevronsDownUp } from 'lucide-svelte';
    import SQLEditor from '$lib/components/SQLEditor.svelte';
    import { dashboardStore } from '$lib/stores/dashboardStore.svelte';
    import { executionStore } from '$lib/stores/executionStore.svelte';
    import { uiStore } from '$lib/stores/uiStore.svelte';
</script>

<div class="editor-section">
    <div class="editor-toolbar">
        <button class="run-btn" onclick={dashboardStore.run} disabled={executionStore.executing}>
            <span class="run-icon">
                {#if executionStore.executing}
                    <Loader2 size={12} class="spin" />
                {:else}
                    <Play size={12} fill="currentColor" />
                {/if}
            </span>
            {executionStore.executing ? (executionStore.statusMsg ?? 'Running…') : 'Run'}
        </button>
        <kbd class="shortcut">Ctrl+Enter</kbd>

        <div class="toolbar-status">
            {#if executionStore.errorMsg}
                <div class="error-chip" title={executionStore.errorMsg}>
                    <X size={12} />
                    <span class="error-text">{executionStore.errorMsg}</span>
                </div>
            {:else if executionStore.executing && executionStore.statusMsg && dashboardStore.hasLayout}
                <span class="exec-inline">{executionStore.statusMsg}</span>
            {:else if dashboardStore.statementCount > 0}
                <span class="statement-count">
                    {dashboardStore.statementCount} {dashboardStore.statementCount === 1 ? 'statement' : 'statements'}
                    → {dashboardStore.statementCount} {dashboardStore.statementCount === 1 ? 'panel' : 'panels'}
                </span>
            {/if}
        </div>

        <button class="editor-close" onclick={uiStore.toggleEditor} title="Hide editor (Ctrl+E)" aria-label="Hide editor">
            <ChevronsDownUp size={14} />
        </button>
    </div>

    <div class="editor-wrapper">
        <SQLEditor bind:value={dashboardStore.sql} onRun={dashboardStore.run} disabled={executionStore.executing} theme={uiStore.theme} />
    </div>
</div>

<style>
    .editor-section {
        flex: 1;
        min-height: 0;
        display: flex;
        flex-direction: column;
    }

    .toolbar-status {
        margin-left: auto;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        min-width: 0;
        overflow: hidden;
    }

    .editor-close {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 26px;
        height: 26px;
        flex-shrink: 0;
        border: none;
        background: none;
        color: var(--sqlviz-text-muted);
        border-radius: var(--sqlviz-radius);
        cursor: pointer;
        transition: background 0.12s, color 0.12s;
    }
    .editor-close:hover { background: var(--sqlviz-bg-base); color: var(--sqlviz-text); }

    .editor-toolbar {
        height: 32px;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0 0.875rem;
        background: var(--sqlviz-bg-surface);
        border-bottom: 1px solid var(--sqlviz-hairline);
        flex-shrink: 0;
        overflow: hidden;
    }

    .run-btn {
        display: flex;
        align-items: center;
        gap: 0.375rem;
        height: 24px;
        padding: 0 0.75rem;
        background: var(--sqlviz-primary);
        color: #fff;
        border: none;
        border-radius: var(--sqlviz-radius);
        font-size: 0.75rem;
        font-weight: 600;
        cursor: pointer;
        white-space: nowrap;
        transition: opacity 0.15s;
    }

    .run-btn:hover:not(:disabled) { opacity: 0.85; }
    .run-btn:disabled { opacity: 0.5; cursor: not-allowed; }

    .run-icon {
        display: flex;
        align-items: center;
    }

    .run-icon :global(svg.spin) {
        animation: spin 1s linear infinite;
    }

    @keyframes spin { to { transform: rotate(360deg); } }

    .shortcut {
        font-family: var(--sqlviz-font-mono);
        font-size: 0.6875rem;
        background: var(--sqlviz-bg-base);
        border: 1px solid var(--sqlviz-border);
        border-radius: var(--sqlviz-radius);
        padding: 0.125rem 0.375rem;
        color: var(--sqlviz-text-muted);
    }

    .error-chip {
        display: flex;
        align-items: center;
        gap: 0.375rem;
        color: var(--sqlviz-negative);
        font-size: 0.8125rem;
        min-width: 0;
    }

    .error-text {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .exec-inline {
        font-size: 0.8125rem;
        color: var(--sqlviz-text-muted);
    }

    .statement-count {
        flex-shrink: 1;
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        font-size: 0.75rem;
        color: var(--sqlviz-text-muted);
    }

    .editor-wrapper {
        flex: 1;
        min-height: 0;
    }
</style>
