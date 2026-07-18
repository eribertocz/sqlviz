<script lang="ts">
    import { goto } from '$app/navigation';
    import { onDestroy, onMount } from 'svelte';
    import AppBar from '$lib/components/AppBar.svelte';
    import DashboardArea from '$lib/components/DashboardArea.svelte';
    import DashboardScorePanel from '$lib/components/DashboardScorePanel.svelte';
    import DashboardExplorer from '$lib/components/DashboardExplorer.svelte';
    import EditorSection from '$lib/components/EditorSection.svelte';
    import ExplainPanel from '$lib/components/ExplainPanel.svelte';
    import FilterBar from '$lib/components/FilterBar.svelte';
    import ToastHost from '$lib/components/ToastHost.svelte';
    import VerticalResizer from '$lib/components/VerticalResizer.svelte';
    import WelcomeScreen from '$lib/components/WelcomeScreen.svelte';
    import { dashboardStore } from '$lib/stores/dashboardStore.svelte';
    import { editMode } from '$lib/stores/editMode';
    import { filterValues } from '$lib/stores/filterValues';
    import { uiStore } from '$lib/stores/uiStore.svelte';

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
    });
</script>

<div class="app-shell">
    <AppBar />

    <!-- Body: sidebar + main content + optional score panel -->
    <div class="app-body">

        <!-- Dashboard Explorer — always visible left sidebar (v0.2.7) -->
        <DashboardExplorer />

        <!-- Main content column -->
        <div class="app-main">
            {#if showWelcome}
                <!-- Clean welcome screen — no dashboards yet -->
                <WelcomeScreen />
            {:else}
                <!-- Filter bar — both modes when panels have $variables -->
                {#if dashboardStore.hasFilters}
                    <FilterBar
                        controls={dashboardStore.allFilterControls}
                        filterVals={$filterValues}
                        domains={dashboardStore.filterDomains}
                        onChange={dashboardStore.handleFilterChange}
                    />
                {/if}

                <!-- Editor section — hidden in Preview mode -->
                {#if $editMode}
                    <EditorSection />
                    <VerticalResizer onDrag={(dy) => uiStore.setEditorHeight(uiStore.editorHeightPx + dy)} />
                {/if}

                <DashboardArea />
            {/if}
        </div>

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
        flex: 1;
        display: flex;
        flex-direction: column;
        min-width: 0;
        overflow: hidden;
    }
</style>
