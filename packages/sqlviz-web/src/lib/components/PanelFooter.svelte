<script lang="ts">
    import type { InferenceResult } from '$lib/types';

    let { result, data }: {
        result: InferenceResult;
        data: Record<string, unknown>[];
    } = $props();

    const elapsedDisplay = $derived(
        result.elapsed_ms > 0 ? result.elapsed_ms.toFixed(1) + ' ms' : '—'
    );
    const rowDisplay = $derived(
        data.length === 1 ? '1 row' : `${data.length} rows`
    );
</script>

<!-- DOC6 §5.5 — execution metadata, visible only in Edit mode (parent gates rendering) -->
<div class="panel-footer">
    <span class="meta">{elapsedDisplay}</span>
    <span class="sep">·</span>
    <span class="meta">{rowDisplay}</span>
    <span class="sep">·</span>
    <span class="meta engine">DuckDB</span>
</div>

<style>
    .panel-footer {
        display: flex;
        align-items: center;
        gap: 0.25rem;
        padding: 0.375rem 1rem;
        border-top: 1px solid var(--sqlviz-border);
        flex-shrink: 0;
    }

    .meta {
        font-size: 0.6875rem;
        color: var(--sqlviz-text-muted);
        font-family: var(--sqlviz-font-mono);
        letter-spacing: 0.01em;
    }

    .sep {
        font-size: 0.6875rem;
        color: var(--sqlviz-border);
    }

    .engine {
        color: var(--sqlviz-primary);
        opacity: 0.7;
    }
</style>
