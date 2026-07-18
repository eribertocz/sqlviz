<script lang="ts">
    import ExecutionStateBadge from '$lib/components/shared/ExecutionStateBadge.svelte';
    import type { InferenceResult } from '$lib/types';

    let { ir }: { ir: InferenceResult } = $props();
</script>

<section class="section section-diag">
    <h3 class="section-title">Diagnostics</h3>

    <div class="diag-grid">
        <span class="diag-label">State</span>
        <span class="diag-value">
            <ExecutionStateBadge state={ir.execution_state ?? 'success'} />
        </span>

        <span class="diag-label">Trace</span>
        <code class="diag-value diag-mono">{ir.trace_id ?? '—'}</code>

        <span class="diag-label">Time</span>
        <span class="diag-value diag-mono">{ir.elapsed_ms.toFixed(1)} ms</span>

        <span class="diag-label">Fingerprint</span>
        <code class="diag-value diag-mono">{ir.fingerprint.slice(0, 12)}…</code>

        <span class="diag-label">Engine</span>
        <span class="diag-value diag-mono">{ir.engine_version}</span>
    </div>

    {#if ir.module_timings}
        <div class="subsection-title">Module timings</div>
        <div class="timings-grid">
            {#each Object.entries(ir.module_timings) as [mod, ms]}
                <span class="timing-module">{mod}</span>
                <span class="timing-ms">{ms.toFixed(1)} ms</span>
            {/each}
        </div>
    {/if}
</section>

<style>
    .section {
        padding: 0.75rem 0;
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

    .section-diag { border-top: 1px solid var(--sqlviz-border); }

    .diag-grid {
        display: grid;
        grid-template-columns: 80px 1fr;
        gap: 0.25rem 0.75rem;
        font-size: 0.75rem;
    }
    .diag-label { color: var(--sqlviz-text-muted); align-self: center; }
    .diag-value { color: var(--sqlviz-text); align-self: center; }
    .diag-mono  { font-family: var(--sqlviz-font-mono); font-size: 0.7rem; }

    .timings-grid {
        display: grid;
        grid-template-columns: 1fr auto;
        gap: 0.125rem 0.75rem;
        font-size: 0.6875rem;
        font-family: var(--sqlviz-font-mono);
        margin-top: 0.25rem;
    }
    .timing-module { color: var(--sqlviz-text-muted); }
    .timing-ms     { color: var(--sqlviz-text); text-align: right; }
</style>
