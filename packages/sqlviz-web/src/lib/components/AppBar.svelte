<script lang="ts">
    import { ChevronDown, ChevronUp, Moon, Sun, X } from 'lucide-svelte';
    import { dashboardStore } from '$lib/stores/dashboardStore.svelte';
    import { editMode } from '$lib/stores/editMode';
    import { executionStore } from '$lib/stores/executionStore.svelte';
    import { uiStore } from '$lib/stores/uiStore.svelte';

    function cancelNewDashboard() {
        uiStore.creatingDashboard = false;
        uiStore.newDashboardName  = '';
    }

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
            <span class="dash-name" title={dashboardStore.activeDashboard.name}>{dashboardStore.activeDashboard.name}</span>
        {/if}

        {#if uiStore.creatingDashboard}
            <form
                class="new-dash-form"
                onsubmit={(e) => { e.preventDefault(); dashboardStore.createDashboard(); }}
            >
                <input
                    class="new-dash-input"
                    aria-label="Dashboard name"
                    bind:value={uiStore.newDashboardName}
                    placeholder="Dashboard name"
                    onkeydown={(e) => { if (e.key === 'Escape') cancelNewDashboard(); }}
                    autofocus
                />
                <button type="submit" class="new-dash-confirm">Create</button>
                <button type="button" class="new-dash-cancel" onclick={cancelNewDashboard} aria-label="Cancel"><X size={14} /></button>
            </form>
        {:else}
            <button
                class="new-dash-btn"
                onclick={() => { uiStore.creatingDashboard = true; }}
                disabled={executionStore.executing}
                title={executionStore.executing ? 'Wait for current run to finish' : 'New dashboard'}
            >+ New</button>
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
        border-left: 1px solid var(--sqlviz-border);
        padding-left: 0.625rem;
    }

    /* New dashboard inline form */
    .new-dash-form {
        display: flex;
        align-items: center;
        gap: 0.25rem;
    }

    .new-dash-input {
        height: 28px;
        padding: 0 0.5rem;
        background: var(--sqlviz-bg-base);
        border: 1px solid var(--sqlviz-primary);
        border-radius: var(--sqlviz-radius);
        color: var(--sqlviz-text);
        font-size: 0.8125rem;
        outline: none;
        width: 160px;
    }

    .new-dash-confirm {
        height: 28px;
        padding: 0 0.625rem;
        background: var(--sqlviz-primary);
        border: none;
        border-radius: var(--sqlviz-radius);
        color: #fff;
        font-size: 0.8125rem;
        font-weight: 500;
        cursor: pointer;
        white-space: nowrap;
    }
    .new-dash-confirm:hover { filter: brightness(1.1); }

    .new-dash-cancel {
        height: 28px;
        width: 28px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: none;
        border: 1px solid var(--sqlviz-border);
        border-radius: var(--sqlviz-radius);
        color: var(--sqlviz-text-muted);
        font-size: 0.875rem;
        cursor: pointer;
        transition: color 0.12s, border-color 0.12s;
    }
    .new-dash-cancel:hover {
        color: var(--sqlviz-text);
        border-color: var(--sqlviz-text-muted);
    }

    .new-dash-btn {
        height: 28px;
        padding: 0 0.625rem;
        background: none;
        border: 1px solid var(--sqlviz-border);
        border-radius: var(--sqlviz-radius);
        color: var(--sqlviz-text-muted);
        font-size: 0.8125rem;
        font-weight: 500;
        cursor: pointer;
        white-space: nowrap;
        transition: color 0.12s, border-color 0.12s, background 0.12s;
        flex-shrink: 0;
    }
    .new-dash-btn:hover:not(:disabled) {
        color: var(--sqlviz-primary);
        border-color: var(--sqlviz-primary);
        background: color-mix(in srgb, var(--sqlviz-primary) 8%, transparent);
    }
    .new-dash-btn:disabled {
        opacity: 0.4;
        cursor: not-allowed;
    }

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
