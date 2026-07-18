<script lang="ts">
    import { ArrowDown, ArrowRight, ArrowUp } from 'lucide-svelte';
    import type { InferenceResult } from '$lib/types';

    let { result, data }: {
        result: InferenceResult;
        data: Record<string, unknown>[];
    } = $props();

    // DOC6 §5.4 (corrected per DOC5 §16.6): read trend_direction_label ONLY.
    // This is a pure rendering lookup — no feature_vector indexing, no thresholds here.
    type TrendLabel = 'growing' | 'declining' | 'flat' | 'unknown';
    const TREND_DISPLAY: Record<TrendLabel, { icon: typeof ArrowUp | null; cls: string }> = {
        growing:   { icon: ArrowUp,    cls: 'positive' },
        declining: { icon: ArrowDown,  cls: 'negative' },
        flat:      { icon: ArrowRight, cls: 'neutral'  },
        unknown:   { icon: null,       cls: 'neutral'  },
    };

    const trend = $derived(TREND_DISPLAY[result.trend_direction_label as TrendLabel]);

    // Extract the first row's first entry as the KPI value.
    // KPI queries return 1 row with 1 (or few) columns; display the first.
    const row = $derived(data[0] ?? {});
    const entries = $derived(Object.entries(row));
    const kpiValue = $derived(entries[0]?.[1]);

    function formatNumber(val: unknown): string {
        if (val == null) return '—';
        const n = Number(val);
        if (isNaN(n)) return String(val);
        if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
        if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K';
        return n.toLocaleString(undefined, { maximumFractionDigits: 2 });
    }
</script>

<div class="kpi-body">
    <div class="kpi-value">{formatNumber(kpiValue)}</div>
    {#if result.trend_direction_label !== 'unknown' && trend.icon}
        {@const TrendIcon = trend.icon}
        <span class="kpi-trend {trend.cls}">
            <TrendIcon size={20} strokeWidth={2.5} />
        </span>
    {/if}
</div>

<style>
    .kpi-body {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 0.375rem;
        padding: 1.25rem;
    }

    .kpi-value {
        font-size: 2.25rem;
        font-weight: 700;
        color: var(--sqlviz-text);
        letter-spacing: -0.03em;
        line-height: 1;
    }

    .kpi-trend {
        display: flex;
        align-items: center;
        line-height: 1;
    }

    .kpi-trend.positive { color: var(--sqlviz-positive); }
    .kpi-trend.negative { color: var(--sqlviz-negative); }
    .kpi-trend.neutral  { color: var(--sqlviz-neutral);  }
</style>
