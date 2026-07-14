<script lang="ts">
    import type { InferenceResult } from '$lib/types';

    const WIDTHS = [4, 6, 8, 12] as const;
    const HEIGHT_PRESETS = [
        { label: 'Compact', factor: 0.70 },
        { label: 'Normal',  factor: 1.00 },
        { label: 'Grande',  factor: 1.40 },
    ] as const;

    let { result, currentColSpan, onWidthChange, onHeightChange, onReset, onClose }: {
        result: InferenceResult;
        currentColSpan: number;
        onWidthChange: (cols: number | null) => void;
        onHeightChange: (px: number | null) => void;
        onReset: () => void;
        onClose: () => void;
    } = $props();

    // Min width from backend (DOC6 §12.2.2); defaults to 3 when absent.
    const minWidth = $derived(result.layout_constraints?.min_width ?? 3);
    const preferredHeight = $derived(result.panel_height_px);
    const maxHeight = $derived(result.layout_constraints?.max_height_px ?? 720);

    function heightForPreset(factor: number): number {
        return Math.min(maxHeight, Math.round(preferredHeight * factor));
    }

    // Track whether any override is active (to show Reset button).
    let activeWidth = $state<number | null>(null);
    let activeHeight = $state<number | null>(null);
    const hasOverride = $derived(activeWidth !== null || activeHeight !== null);

    function selectWidth(w: number | null) {
        activeWidth = w;
        onWidthChange(w);
    }

    function selectHeight(px: number | null) {
        activeHeight = px;
        onHeightChange(px);
    }

    function reset() {
        activeWidth = null;
        activeHeight = null;
        onReset();
    }
</script>

<svelte:window onkeydown={(e) => { if (e.key === 'Escape') onClose(); }} />

<div class="layout-controls" onclick={(e) => e.stopPropagation()} onkeydown={(e) => e.stopPropagation()} role="dialog" aria-label="Layout controls" tabindex="-1">
    <div class="controls-header">
        <span class="controls-title">Layout</span>
        <button class="close-btn" onclick={onClose} aria-label="Close">×</button>
    </div>

    <!-- Width group (DOC6 §12.2.2) -->
    <div class="control-group">
        <span class="group-label">Width</span>
        <div class="btn-group">
            <button
                class="ctrl-btn"
                class:active={activeWidth === null}
                onclick={() => selectWidth(null)}
            >
                Auto: {currentColSpan}col
            </button>
            {#each WIDTHS as w (w)}
                {@const tooNarrow = w < minWidth}
                <button
                    class="ctrl-btn"
                    class:active={activeWidth === w}
                    class:constrained={tooNarrow}
                    title={tooNarrow ? `Min width for this chart: ${minWidth} cols` : undefined}
                    onclick={() => selectWidth(w)}
                >
                    {w}col{tooNarrow ? ' ⚠' : ''}
                </button>
            {/each}
        </div>
    </div>

    <!-- Height group (DOC6 §12.2.3) -->
    <div class="control-group">
        <span class="group-label">Height</span>
        <div class="btn-group">
            <button
                class="ctrl-btn"
                class:active={activeHeight === null}
                onclick={() => selectHeight(null)}
            >
                Auto: {preferredHeight}px
            </button>
            {#each HEIGHT_PRESETS as preset (preset.label)}
                {@const px = heightForPreset(preset.factor)}
                <button
                    class="ctrl-btn"
                    class:active={activeHeight === px}
                    onclick={() => selectHeight(px)}
                >
                    {preset.label} {px}px
                </button>
            {/each}
        </div>
    </div>

    {#if hasOverride}
        <button class="reset-btn" onclick={reset}>Reset to auto</button>
    {/if}
</div>

<style>
    .layout-controls {
        background: var(--sqlviz-bg-surface);
        border: 1px solid var(--sqlviz-border);
        border-radius: var(--sqlviz-radius-lg);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        width: 280px;
        font-size: 0.8125rem;
        overflow: hidden;
    }

    .controls-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.625rem 0.875rem;
        border-bottom: 1px solid var(--sqlviz-border);
    }

    .controls-title {
        font-weight: 600;
        color: var(--sqlviz-text);
        font-size: 0.8125rem;
    }

    .close-btn {
        background: none;
        border: none;
        cursor: pointer;
        color: var(--sqlviz-text-muted);
        font-size: 1.125rem;
        line-height: 1;
        padding: 0 0.125rem;
        transition: color 0.15s;
    }
    .close-btn:hover { color: var(--sqlviz-text); }

    .control-group {
        padding: 0.625rem 0.875rem;
        border-bottom: 1px solid var(--sqlviz-border);
    }

    .group-label {
        display: block;
        font-size: 0.75rem;
        color: var(--sqlviz-text-muted);
        margin-bottom: 0.375rem;
    }

    .btn-group {
        display: flex;
        flex-wrap: wrap;
        gap: 0.25rem;
    }

    .ctrl-btn {
        padding: 0.25rem 0.5rem;
        background: var(--sqlviz-bg-base);
        border: 1px solid var(--sqlviz-border);
        border-radius: var(--sqlviz-radius);
        cursor: pointer;
        font-size: 0.75rem;
        color: var(--sqlviz-text-muted);
        transition: background 0.12s, color 0.12s, border-color 0.12s;
        white-space: nowrap;
    }

    .ctrl-btn:hover {
        background: var(--sqlviz-bg-surface);
        color: var(--sqlviz-text);
        border-color: var(--sqlviz-primary);
    }

    .ctrl-btn.active {
        background: var(--sqlviz-primary);
        border-color: var(--sqlviz-primary);
        color: #fff;
    }

    .ctrl-btn.constrained {
        color: var(--sqlviz-neutral);
        opacity: 0.7;
    }

    .reset-btn {
        display: block;
        width: 100%;
        padding: 0.5rem 0.875rem;
        background: none;
        border: none;
        text-align: center;
        cursor: pointer;
        font-size: 0.75rem;
        color: var(--sqlviz-text-muted);
        transition: color 0.15s, background 0.15s;
    }
    .reset-btn:hover {
        background: var(--sqlviz-bg-base);
        color: var(--sqlviz-text);
    }
</style>
