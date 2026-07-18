<script lang="ts">
    import { pct } from './explainMeta';

    let { items }: {
        items: Array<{ label: string; raw_score: number }>;
    } = $props();

    const maxScore = $derived(Math.max(...items.map(x => x.raw_score), 0.01));
</script>

<div class="score-bars">
    {#each items as item, i}
        <div class="score-row">
            <span class="score-label" class:winner={i === 0}>{item.label}</span>
            <div class="bar-track">
                <div
                    class="bar-fill"
                    class:bar-winner={i === 0}
                    style="width: {pct(item.raw_score, maxScore)}"
                ></div>
            </div>
            <span class="score-value" class:winner={i === 0}>
                {item.raw_score.toFixed(2)}
            </span>
        </div>
    {/each}
</div>

<style>
    .score-bars {
        display: flex;
        flex-direction: column;
        gap: 0.4375rem;
    }

    .score-row {
        display: grid;
        grid-template-columns: 120px 1fr 36px;
        align-items: center;
        gap: 0.5rem;
    }

    .score-label {
        font-size: 0.75rem;
        color: var(--sqlviz-text-muted);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .score-label.winner { color: var(--sqlviz-text); font-weight: 600; }

    .bar-track {
        height: 6px;
        background: var(--sqlviz-bg-base);
        border-radius: 3px;
        overflow: hidden;
    }

    .bar-fill {
        height: 100%;
        background: var(--sqlviz-neutral);
        border-radius: 3px;
        transition: width 0.3s ease-out;
    }

    .bar-fill.bar-winner { background: var(--sqlviz-primary); }

    .score-value {
        font-size: 0.6875rem;
        font-family: var(--sqlviz-font-mono);
        color: var(--sqlviz-text-muted);
        text-align: right;
    }

    .score-value.winner { color: var(--sqlviz-primary); font-weight: 600; }
</style>
