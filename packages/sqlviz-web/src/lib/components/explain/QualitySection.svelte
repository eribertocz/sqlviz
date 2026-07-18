<script lang="ts">
    import type { InferenceResult } from '$lib/types';
    import { qualityMeta } from './explainMeta';

    let { ir }: { ir: InferenceResult } = $props();

    const qm = $derived(qualityMeta(ir.chart_quality));
</script>

<section class="section">
    <h3 class="section-title">Inference confidence</h3>
    <div class="quality-row">
        <span class="quality-badge {qm.cls}">{qm.label}</span>
    </div>
    <p class="quality-detail">{qm.detail}</p>

    {#if ir.errors.length > 0}
        <div class="subsection-title">Errors</div>
        <ul class="error-list">
            {#each ir.errors as err}
                <li class="error-item">{err}</li>
            {/each}
        </ul>
    {/if}
</section>

<style>
    .section {
        padding: 0.75rem 0;
        border-bottom: 1px solid var(--sqlviz-border);
    }

    .section-title {
        margin: 0 0 0.625rem;
        font-size: 0.6875rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        color: var(--sqlviz-text-muted);
    }

    .subsection-title {
        margin: 0.875rem 0 0.5rem;
        font-size: 0.6875rem;
        font-weight: 600;
        color: var(--sqlviz-text-muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .quality-row { margin-bottom: 0.5rem; }

    .quality-badge {
        display: inline-block;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.25rem 0.625rem;
        border-radius: var(--sqlviz-radius);
    }

    .quality-badge.positive {
        background: color-mix(in srgb, var(--sqlviz-positive) 15%, transparent);
        color: var(--sqlviz-positive);
    }

    .quality-badge.neutral {
        background: color-mix(in srgb, var(--sqlviz-neutral) 15%, transparent);
        color: var(--sqlviz-neutral);
    }

    .quality-badge.negative {
        background: color-mix(in srgb, var(--sqlviz-negative) 15%, transparent);
        color: var(--sqlviz-negative);
    }

    .quality-detail {
        margin: 0;
        font-size: 0.8125rem;
        color: var(--sqlviz-text-muted);
        line-height: 1.5;
    }

    .error-list {
        list-style: none;
        margin: 0;
        padding: 0;
    }

    .error-item {
        font-size: 0.75rem;
        font-family: var(--sqlviz-font-mono);
        color: var(--sqlviz-negative);
        padding: 0.25rem 0;
    }
</style>
