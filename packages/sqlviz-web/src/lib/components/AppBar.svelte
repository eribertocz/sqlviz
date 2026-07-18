<script lang="ts">
    import { ChevronDown, ChevronUp, Loader2, Moon, Sun } from 'lucide-svelte';
    import { dashboardStore } from '$lib/stores/dashboardStore.svelte';
    import { editMode } from '$lib/stores/editMode';
    import { executionStore } from '$lib/stores/executionStore.svelte';
    import { uiStore } from '$lib/stores/uiStore.svelte';

    // Inline dashboard-name editing (UX spec §"Cambiar nombre").
    let editingName = $state(false);
    let nameValue = $state('');

    function startEditName() {
        const d = dashboardStore.activeDashboard;
        if (!d) return;
        nameValue = d.name;
        editingName = true;
    }
    function commitName() {
        const d = dashboardStore.activeDashboard;
        if (d && nameValue.trim() && nameValue.trim() !== d.name) {
            dashboardStore.renameDashboard(d.id, nameValue);
        }
        editingName = false;
    }
    function nameKeydown(e: KeyboardEvent) {
        if (e.key === 'Enter') { e.preventDefault(); commitName(); }
        else if (e.key === 'Escape') { e.preventDefault(); editingName = false; }
    }
    function selectOnMount(node: HTMLInputElement) { node.focus(); node.select(); }

    // Subtle save/run status shown only in the header (UX spec §"Estados visuales").
    type Status = { text: string; kind: 'draft' | 'saving' | 'saved' | 'running' | 'error' } | null;
    const status = $derived.by<Status>(() => {
        if (executionStore.executing) return { text: 'Running', kind: 'running' };
        if (executionStore.errorMsg)  return { text: 'Error', kind: 'error' };
        if (executionStore.saveStatus === 'saving') return { text: 'Saving…', kind: 'saving' };
        if (executionStore.saveStatus === 'saved')  return { text: 'Saved', kind: 'saved' };
        if (executionStore.saveStatus === 'draft')  return { text: 'Draft', kind: 'draft' };
        return null;
    });

    function handleModeKeydown(e: KeyboardEvent) {
        if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
        e.preventDefault();
        const next = !$editMode;
        editMode.set(next);
        const group = (e.currentTarget as HTMLElement).parentElement;
        group?.querySelectorAll<HTMLButtonElement>('.mode-btn')[next ? 1 : 0]?.focus();
    }
</script>

<header class="app-bar">
    <div class="bar-left">
        <span class="app-logo">SQLviz</span>

        {#if dashboardStore.activeDashboard}
            {#if editingName}
                <input
                    class="dash-name-input"
                    bind:value={nameValue}
                    use:selectOnMount
                    onkeydown={nameKeydown}
                    onblur={commitName}
                    aria-label="Dashboard name"
                />
            {:else}
                <button
                    class="dash-name"
                    title="Click to rename"
                    onclick={startEditName}
                >{dashboardStore.activeDashboard.name}</button>
            {/if}

            {#if status}
                <span class="save-status" class:running={status.kind === 'running'} class:error={status.kind === 'error'}>
                    {#if status.kind === 'running'}
                        <Loader2 size={12} class="spin" />
                    {:else if status.kind === 'draft'}
                        <span class="dot" aria-hidden="true">●</span>
                    {/if}
                    {status.text}
                </span>
            {/if}
        {/if}
    </div>

    <div class="bar-right">
        <!-- Dashboard Score button (DOC6 §12.3, edit mode only) -->
        {#if $editMode}
            <button
                class="score-btn"
                class:active={uiStore.showScorePanel}
                aria-pressed={uiStore.showScorePanel}
                onclick={() => uiStore.showScorePanel = !uiStore.showScorePanel}
                title="Dashboard Score"
            >
                Score{dashboardStore.utilityPct != null ? `: ${dashboardStore.utilityPct}` : ''}
                {#if uiStore.showScorePanel}
                    <ChevronDown size={13} />
                {:else}
                    <ChevronUp size={13} />
                {/if}
            </button>
        {/if}

        <div class="mode-toggle" role="tablist" aria-label="Dashboard mode">
            <button
                class="mode-btn"
                role="tab"
                aria-selected={!$editMode}
                tabindex={!$editMode ? 0 : -1}
                class:active={!$editMode}
                onclick={() => editMode.set(false)}
                onkeydown={handleModeKeydown}
            >Preview</button>
            <button
                class="mode-btn"
                role="tab"
                aria-selected={$editMode}
                tabindex={$editMode ? 0 : -1}
                class:active={$editMode}
                onclick={() => editMode.set(true)}
                onkeydown={handleModeKeydown}
            >Edit</button>
        </div>

        <button
            class="theme-btn"
            onclick={uiStore.toggleTheme}
            aria-label={uiStore.theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            title={uiStore.theme === 'dark' ? 'Light mode' : 'Dark mode'}
        >
            {#if uiStore.theme === 'dark'}
                <Sun size={16} />
            {:else}
                <Moon size={16} />
            {/if}
        </button>
    </div>
</header>

<style>
    .app-bar {
        height: 48px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 1rem;
        background: var(--sqlviz-bg-surface);
        border-bottom: 1px solid var(--sqlviz-hairline);
        flex-shrink: 0;
    }

    .bar-left {
        display: flex;
        align-items: center;
        gap: 0.625rem;
        min-width: 0;
    }

    .app-logo {
        font-size: 1rem;
        font-weight: 700;
        color: var(--sqlviz-primary);
        letter-spacing: -0.02em;
        flex-shrink: 0;
    }

    /* Active dashboard name */
    .dash-name {
        font-size: 0.8125rem;
        font-weight: 500;
        color: var(--sqlviz-text-muted);
        max-width: 180px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        border: none;
        background: none;
        border-left: 1px solid var(--sqlviz-border);
        border-radius: 0;
        padding: 0.125rem 0.375rem 0.125rem 0.625rem;
        cursor: text;
        transition: color 0.12s;
    }
    .dash-name:hover { color: var(--sqlviz-text); }

    .dash-name-input {
        font-size: 0.8125rem;
        font-weight: 500;
        color: var(--sqlviz-text);
        background: var(--sqlviz-bg);
        border: 1px solid var(--sqlviz-primary);
        border-radius: var(--sqlviz-radius);
        padding: 0.125rem 0.375rem;
        margin-left: 0.5rem;
        max-width: 200px;
        outline: none;
    }

    .save-status {
        display: inline-flex;
        align-items: center;
        gap: 0.3125rem;
        font-size: 0.6875rem;
        color: var(--sqlviz-text-muted);
        white-space: nowrap;
    }
    .save-status .dot { color: var(--sqlviz-primary); font-size: 0.625rem; line-height: 1; }
    .save-status.running { color: var(--sqlviz-primary); }
    .save-status.error { color: var(--sqlviz-negative); }
    .save-status :global(.spin) { animation: appbar-spin 0.8s linear infinite; }

    @keyframes appbar-spin { to { transform: rotate(360deg); } }

    .mode-toggle {
        display: flex;
        border: 1px solid var(--sqlviz-border);
        border-radius: var(--sqlviz-radius);
        overflow: hidden;
    }

    .mode-btn {
        padding: 0.25rem 0.875rem;
        background: none;
        border: none;
        cursor: pointer;
        font-size: 0.8125rem;
        font-weight: 500;
        color: var(--sqlviz-text-muted);
        transition: background 0.15s, color 0.15s;
    }

    .mode-btn.active {
        background: var(--sqlviz-primary);
        color: #fff;
    }

    .mode-btn:not(.active):hover {
        background: var(--sqlviz-bg-base);
        color: var(--sqlviz-text);
    }

    .bar-right {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* Score button (DOC6 §12.3, edit mode) */
    .score-btn {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        padding: 0.25rem 0.75rem;
        background: none;
        border: 1px solid var(--sqlviz-border);
        border-radius: var(--sqlviz-radius);
        cursor: pointer;
        font-size: 0.8125rem;
        font-weight: 500;
        color: var(--sqlviz-text-muted);
        transition: background 0.15s, color 0.15s, border-color 0.15s;
        white-space: nowrap;
    }
    .score-btn:hover, .score-btn.active {
        background: var(--sqlviz-bg-base);
        color: var(--sqlviz-text);
        border-color: var(--sqlviz-primary);
    }

    .theme-btn {
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: none;
        border: 1px solid var(--sqlviz-border);
        border-radius: var(--sqlviz-radius);
        cursor: pointer;
        font-size: 1rem;
        color: var(--sqlviz-text-muted);
        transition: background 0.15s, color 0.15s, border-color 0.15s;
        line-height: 1;
    }

    .theme-btn:hover {
        background: var(--sqlviz-bg);
        color: var(--sqlviz-text);
        border-color: var(--sqlviz-primary);
    }
</style>
