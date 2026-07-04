<script lang="ts">
    import type { InferenceResult } from '$lib/types';

    let { result, panelId = '', onExplain }: {
        result: InferenceResult;
        panelId?: string;
        onExplain?: (id: string) => void;
    } = $props();

    // DOC6 §8.1: show ⓘ ONLY when quality is not high or fallback was applied.
    // A high-confidence, clean inference shows nothing — per DOC1 Principle 2.
    const showQualityIcon = $derived(
        result.chart_quality !== 'high' || result.fallback_applied
    );
</script>

<div class="panel-header">
    <h3 class="panel-title">{result.title || 'Untitled query'}</h3>
    {#if showQualityIcon}
        <button
            class="explain-trigger"
            title="{result.fallback_applied ? result.fallback_reason : result.chart_quality + ' confidence'}"
            onclick={() => onExplain?.(panelId)}
        >ⓘ</button>
    {/if}
</div>

<style>
    .panel-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.5rem;
        padding: 0.75rem 1rem;
        border-bottom: 1px solid var(--sqlviz-border);
        flex-shrink: 0;
    }

    .panel-title {
        margin: 0;
        font-size: 0.9375rem;
        font-weight: 600;
        color: var(--sqlviz-text);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .explain-trigger {
        flex-shrink: 0;
        background: none;
        border: none;
        cursor: pointer;
        font-size: 0.9375rem;
        color: var(--sqlviz-text-muted);
        padding: 0 0.25rem;
        line-height: 1;
        transition: color 0.15s;
    }

    .explain-trigger:hover {
        color: var(--sqlviz-primary);
    }
</style>
