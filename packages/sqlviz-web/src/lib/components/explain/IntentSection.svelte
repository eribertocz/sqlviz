<script lang="ts">
    import type { InferenceResult } from '$lib/types';
    import ScoreBars from './ScoreBars.svelte';
    import { intentMeta, signalLabel, topSignals } from './explainMeta';

    let { ir }: { ir: InferenceResult } = $props();

    const im = $derived(intentMeta(ir.intent_winner));
    const signals = $derived(topSignals(ir));
    const allIntents = $derived([
        { intent: ir.intent_winner, raw_score: ir.intent_raw_score },
        ...(ir.intent_alternatives as Array<{ intent: string; raw_score: number }>),
    ]);
</script>

<section class="section">
    <h3 class="section-title">Detected intent</h3>
    <div class="intent-badge">
        <span class="intent-icon">{im.icon}</span>
        <div>
            <div class="intent-name">{im.label}</div>
            {#if im.description}
                <div class="intent-desc">{im.description}</div>
            {/if}
        </div>
    </div>

    <!-- Signals that drove the intent -->
    {#if signals.length > 0}
        <div class="subsection-title">Key signals</div>
        <ul class="signal-list">
            {#each signals as s}
                <li class="signal-item">
                    <span class="signal-dot">✓</span>
                    <span class="signal-name">{signalLabel(s.signal)}</span>
                    <span class="signal-score">{s.contribution.toFixed(2)}</span>
                </li>
            {/each}
        </ul>
    {:else}
        <p class="muted-note">Signal data unavailable — run the panel to see details.</p>
    {/if}

    <!-- Intent score comparison -->
    {#if allIntents.length > 1}
        <div class="subsection-title">Intent scores</div>
        <ScoreBars items={allIntents.map(x => ({ label: intentMeta(x.intent).label, raw_score: x.raw_score }))} />
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

    /* ── Intent badge ─────────────────────────────────────────── */
    .intent-badge {
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        padding: 0.5rem 0.75rem;
        background: color-mix(in srgb, var(--sqlviz-primary) 10%, transparent);
        border: 1px solid color-mix(in srgb, var(--sqlviz-primary) 25%, transparent);
        border-radius: var(--sqlviz-radius-lg);
    }

    .intent-icon {
        font-size: 1.25rem;
        flex-shrink: 0;
        color: var(--sqlviz-primary);
        margin-top: 0.1rem;
        font-style: normal;
    }

    .intent-name {
        font-size: 0.9375rem;
        font-weight: 600;
        color: var(--sqlviz-text);
    }

    .intent-desc {
        font-size: 0.8125rem;
        color: var(--sqlviz-text-muted);
        margin-top: 0.25rem;
        line-height: 1.45;
    }

    /* ── Signal list ──────────────────────────────────────────── */
    .signal-list {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: 0.3125rem;
    }

    .signal-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.8125rem;
    }

    .signal-dot {
        color: var(--sqlviz-positive);
        font-size: 0.6875rem;
        flex-shrink: 0;
    }

    .signal-name {
        flex: 1;
        color: var(--sqlviz-text);
        line-height: 1.4;
    }

    .signal-score {
        font-family: var(--sqlviz-font-mono);
        font-size: 0.6875rem;
        color: var(--sqlviz-text-muted);
        flex-shrink: 0;
    }

    .muted-note {
        font-size: 0.8125rem;
        color: var(--sqlviz-text-muted);
        font-style: italic;
        margin: 0;
    }
</style>
