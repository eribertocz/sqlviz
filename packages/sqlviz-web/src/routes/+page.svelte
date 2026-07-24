<script lang="ts">
    import { goto } from '$app/navigation';
    import { onDestroy, onMount } from 'svelte';
    import AppBar from '$lib/components/AppBar.svelte';
    import DashboardArea from '$lib/components/DashboardArea.svelte';
    import DashboardScorePanel from '$lib/components/DashboardScorePanel.svelte';
    import DashboardExplorer from '$lib/components/DashboardExplorer.svelte';
    import PanelPropertiesPanel from '$lib/components/PanelPropertiesPanel.svelte';
    import EditorSection from '$lib/components/EditorSection.svelte';
    import ExplainPanel from '$lib/components/ExplainPanel.svelte';
    import CommandPalette from '$lib/components/CommandPalette.svelte';
    import ToastHost from '$lib/components/ToastHost.svelte';
    import VerticalResizer from '$lib/components/VerticalResizer.svelte';
    import WelcomeScreen from '$lib/components/WelcomeScreen.svelte';
    import { dashboardStore } from '$lib/stores/dashboardStore.svelte';
    import { editMode } from '$lib/stores/editMode';
    import { get } from 'svelte/store';
    import { uiStore } from '$lib/stores/uiStore.svelte';
    import Code2Icon from '@lucide/svelte/icons/code-2';
    import MinimizeIcon from '@lucide/svelte/icons/minimize-2';

    let paletteOpen = $state(false);

    // Global keyboard shortcuts (Linear/Superhuman-style speed).
    function onKeydown(e: KeyboardEvent) {
        const mod = e.metaKey || e.ctrlKey;
        if (!mod) {
            if (e.key === 'Escape' && uiStore.focusMode) { uiStore.focusMode = false; }
            return;
        }
        switch (e.key.toLowerCase()) {
            case 'k': e.preventDefault(); paletteOpen = !paletteOpen; break;
            case '\\': e.preventDefault(); uiStore.toggleFocusMode(); break;
            case 'b': e.preventDefault(); uiStore.toggleSidebar(); break;
            case 'e':
                if (get(editMode)) { e.preventDefault(); uiStore.toggleEditor(); }
                break;
        }
    }

    // Welcome screen: no dashboards exist and none is active (fresh install).
    const showWelcome = $derived(
        !dashboardStore.dashboardsLoading
        && dashboardStore.allDashboards.length === 0
        && !dashboardStore.dashboardId
    );

    // Draft auto-save triggers (UX spec §1): save on tab close and on losing
    // browser focus, so no in-flight edit is ever lost.
    const onBeforeUnload = () => dashboardStore.saveDraft(true);
    const onBlur = () => dashboardStore.saveDraft();

    // ── Load existing state on mount ───────────────────────────────────────────
    onMount(async () => {
        uiStore.initTheme();
        window.addEventListener('beforeunload', onBeforeUnload);
        window.addEventListener('blur', onBlur);
        window.addEventListener('keydown', onKeydown);

        const meResp = await fetch('/api/v1/auth/me');
        if (meResp.status === 401) {
            await goto('/login');
            return;
        }
        const meData = await meResp.json() as { status: string; demo: boolean };
        if (meData.demo) {
            editMode.set(true);
        }

        await dashboardStore.bootstrap();
    });

    onDestroy(() => {
        if (typeof window === 'undefined') return;
        window.removeEventListener('beforeunload', onBeforeUnload);
        window.removeEventListener('blur', onBlur);
        window.removeEventListener('keydown', onKeydown);
    });
</script>

<div class="app-shell" class:focus={uiStore.focusMode}>
    {#if !uiStore.focusMode}
        <AppBar />
    {/if}

    <!-- Body: sidebar + main content + optional score panel -->
    <div class="app-body">

        <!-- Dashboard Explorer — rail-by-default left sidebar, hidden in focus -->
        {#if !uiStore.focusMode}
            <DashboardExplorer />
        {/if}

        <!-- Main content column -->
        <div class="app-main">
            {#if showWelcome}
                <!-- Clean welcome screen — no dashboards yet -->
                <WelcomeScreen />
            {:else}
                <!-- Dashboard keeps full height; the editor floats over it -->
                <DashboardArea />

                <!-- Editor drawer — floats at the bottom in Edit mode -->
                {#if $editMode && uiStore.editorOpen}
                    <div class="editor-drawer" style="height: {uiStore.editorHeightPx}px">
                        <VerticalResizer onDrag={(dy) => uiStore.setEditorHeight(uiStore.editorHeightPx - dy)} />
                        <EditorSection />
                    </div>
                {:else if $editMode}
                    <button class="editor-reopen" onclick={uiStore.toggleEditor} title="Open editor (Ctrl+E)">
                        <Code2Icon size={14} /> Editor
                    </button>
                {/if}
            {/if}

            <!-- Focus-mode exit affordance -->
            {#if uiStore.focusMode}
                <button class="focus-exit" onclick={() => (uiStore.focusMode = false)} title="Exit focus (Esc)">
                    <MinimizeIcon size={14} /> Exit focus
                </button>
            {/if}
        </div>

        <!-- Panel Properties panel — right sidebar, opens on panel click (v0.2.9) -->
        {#if $editMode && dashboardStore.selectedPanel}
            <PanelPropertiesPanel panel={dashboardStore.selectedPanel} />
        {/if}

        <!-- Dashboard Score Panel slide-in (DOC6 §12.3, edit mode only) -->
        {#if $editMode && uiStore.showScorePanel && dashboardStore.layout}
            <DashboardScorePanel
                layout={dashboardStore.layout}
                onClose={() => uiStore.showScorePanel = false}
            />
        {/if}

    </div>
</div>

<ToastHost />

<!-- Command palette (Cmd/Ctrl+K) -->
<CommandPalette bind:open={paletteOpen} />

<!-- Explainability drawer (Phase 5.6) -->
<ExplainPanel />

<style>
    .app-shell {
        height: 100vh;
        display: flex;
        flex-direction: column;
        background: var(--sqlviz-bg-base);
        overflow: hidden;
    }

    /* ── App body: sidebar + main + score panel ──────── */
    .app-body {
        flex: 1;
        display: flex;
        flex-direction: row;
        min-height: 0;
        overflow: hidden;
    }

    /* ── Main content column ─────────────────────────── */
    .app-main {
        position: relative;
        flex: 1;
        display: flex;
        flex-direction: column;
        min-width: 0;
        overflow: hidden;
    }

    /* ── Editor drawer — floats over the dashboard bottom ─────────── */
    .editor-drawer {
        position: absolute;
        left: 0;
        right: 0;
        bottom: 0;
        z-index: 15;
        display: flex;
        flex-direction: column;
        background: var(--sqlviz-bg-surface);
        border-top: 1px solid var(--sqlviz-border);
        box-shadow: var(--sqlviz-shadow-drawer);
    }

    /* Floating chip to reopen the editor when the drawer is closed */
    .editor-reopen {
        position: absolute;
        left: 0.75rem;
        bottom: 0.75rem;
        z-index: 15;
        display: inline-flex;
        align-items: center;
        gap: 0.375rem;
        height: 28px;
        padding: 0 0.75rem;
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--sqlviz-text);
        background: var(--sqlviz-bg-surface);
        border: 1px solid var(--sqlviz-border);
        border-radius: 100px;
        cursor: pointer;
        box-shadow: var(--sqlviz-shadow-card);
        transition: border-color 0.12s, color 0.12s;
    }
    .editor-reopen:hover { border-color: var(--sqlviz-primary); color: var(--sqlviz-primary); }

    /* Focus-mode exit chip (top-right) */
    .focus-exit {
        position: absolute;
        top: 0.75rem;
        right: 0.75rem;
        z-index: 30;
        display: inline-flex;
        align-items: center;
        gap: 0.375rem;
        height: 28px;
        padding: 0 0.75rem;
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--sqlviz-text-muted);
        background: var(--sqlviz-bg-surface);
        border: 1px solid var(--sqlviz-border);
        border-radius: 100px;
        cursor: pointer;
        opacity: 0.6;
        box-shadow: var(--sqlviz-shadow-card);
        transition: opacity 0.15s, border-color 0.12s, color 0.12s;
    }
    .focus-exit:hover { opacity: 1; border-color: var(--sqlviz-primary); color: var(--sqlviz-primary); }
</style>
