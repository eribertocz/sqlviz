<script lang="ts">
    import { X } from 'lucide-svelte';
    import ChartSection from '$lib/components/explain/ChartSection.svelte';
    import DiagnosticsSection from '$lib/components/explain/DiagnosticsSection.svelte';
    import IntentSection from '$lib/components/explain/IntentSection.svelte';
    import QualitySection from '$lib/components/explain/QualitySection.svelte';
    import { explainTarget } from '$lib/stores/explainStore';

    function close() {
        explainTarget.set(null);
    }

    function handleKeydown(e: KeyboardEvent) {
        if (e.key === 'Escape') close();
    }
</script>

<svelte:window onkeydown={handleKeydown} />

{#if $explainTarget}
    {@const ir = $explainTarget.inference_result}

    <!-- Backdrop (click to close) -->
    <div
        class="backdrop"
        role="presentation"
        onclick={close}
        onkeydown={() => {}}
    ></div>

    <!-- Drawer -->
    <aside class="explain-drawer" aria-label="Explainability panel">
        <!-- Header -->
        <div class="drawer-header">
            <h2 class="drawer-title">Why this chart?</h2>
            <button class="close-btn" onclick={close} aria-label="Close"><X size={16} /></button>
        </div>

        <div class="drawer-body">

            <!-- Fallback banner -->
            {#if ir.fallback_applied}
                <div class="banner fallback">
                    <span class="banner-icon">⚠</span>
                    <div>
                        <strong>Inference without data</strong>
                        <p>{ir.fallback_reason || 'The query could not be executed, so inference ran on SQL structure only.'}</p>
                    </div>
                </div>
            {/if}

            <IntentSection {ir} />
            <ChartSection {ir} />
            <QualitySection {ir} />
            <DiagnosticsSection {ir} />

        </div>
    </aside>
{/if}

<style>
    /* ── Backdrop ─────────────────────────────────────────────── */
    .backdrop {
        position: fixed;
        inset: 0;
        z-index: 200;
        background: rgba(0, 0, 0, 0.25);
    }

    /* ── Drawer ───────────────────────────────────────────────── */
    .explain-drawer {
        position: fixed;
        top: 48px;               /* below app bar */
        right: 0;
        bottom: 0;
        width: 380px;
        z-index: 201;
        background: var(--sqlviz-bg-surface);
        border-left: 1px solid var(--sqlviz-hairline);
        display: flex;
        flex-direction: column;
        box-shadow: -8px 0 32px var(--sqlviz-shadow-color);
        animation: slideIn 0.18s ease-out;
    }

    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to   { transform: translateX(0);    opacity: 1; }
    }

    /* ── Drawer header ────────────────────────────────────────── */
    .drawer-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.875rem 1rem;
        border-bottom: 1px solid var(--sqlviz-border);
        flex-shrink: 0;
    }

    .drawer-title {
        margin: 0;
        font-size: 0.9375rem;
        font-weight: 700;
        color: var(--sqlviz-text);
    }

    .close-btn {
        display: inline-flex;
        align-items: center;
        background: none;
        border: none;
        cursor: pointer;
        color: var(--sqlviz-text-muted);
        padding: 0.25rem;
        border-radius: var(--sqlviz-radius);
        transition: color 0.15s;
        line-height: 1;
    }

    .close-btn:hover { color: var(--sqlviz-text); }

    /* ── Drawer body ──────────────────────────────────────────── */
    .drawer-body {
        flex: 1;
        overflow-y: auto;
        padding: 1rem;
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }

    /* ── Fallback banner ──────────────────────────────────────── */
    .banner {
        display: flex;
        gap: 0.75rem;
        padding: 0.75rem;
        border-radius: var(--sqlviz-radius-lg);
        margin-bottom: 0.5rem;
    }

    .banner.fallback {
        background: color-mix(in srgb, var(--sqlviz-negative) 10%, transparent);
        border: 1px solid color-mix(in srgb, var(--sqlviz-negative) 30%, transparent);
        color: var(--sqlviz-negative);
    }

    .banner-icon { font-size: 1.125rem; flex-shrink: 0; margin-top: 0.1rem; }

    .banner strong { font-size: 0.875rem; font-weight: 600; }

    .banner p {
        margin: 0.25rem 0 0;
        font-size: 0.8125rem;
        opacity: 0.85;
    }
</style>
