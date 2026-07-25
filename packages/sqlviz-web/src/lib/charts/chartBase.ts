/**
 * Shared ECharts option fragments — one source of truth for motion, tooltip,
 * crosshair, grid and axis styling. Every chart type composes on top of these,
 * so the whole system animates and reacts consistently, driven by tokens.
 */
import type { EChartsOption } from 'echarts';
import type { ChartTokens } from './chartTokens';
import { formatNumber, withAlpha } from './chartTokens';

const FONT = 'Inter, system-ui, sans-serif';

/** Entrance/update animation — lively but calm. Off under reduced-motion. */
export function motion(reduce: boolean): EChartsOption {
    if (reduce) return { animation: false };
    return {
        animation: true,
        animationDuration: 650,
        animationEasing: 'cubicOut',
        animationDurationUpdate: 450,
        animationEasingUpdate: 'cubicInOut',
    };
}

/** Per-item stagger so marks cascade in instead of popping. */
export function stagger(reduce: boolean): number | ((idx: number) => number) {
    return reduce ? 0 : (idx: number) => idx * 18;
}

export function baseOption(t: ChartTokens, reduce: boolean): EChartsOption {
    return {
        backgroundColor: 'transparent',
        ...motion(reduce),
        textStyle: { color: t.text, fontFamily: FONT, fontSize: 11 },
        grid: { top: 16, right: 18, bottom: 30, left: 46, containLabel: true },
        tooltip: {
            confine: true,
            backgroundColor: t.surface,
            borderColor: t.border,
            borderWidth: 1,
            padding: [8, 11],
            extraCssText:
                'border-radius:8px; box-shadow:0 6px 20px rgba(0,0,0,0.28); backdrop-filter:saturate(1.1);',
            textStyle: { color: t.text, fontFamily: FONT, fontSize: 12 },
            valueFormatter: (v: unknown) => formatNumber(v),
        },
    };
}

/** Recessive axes + grid: faint lines, muted labels, tabular figures. */
export function axisStyle(t: ChartTokens) {
    return {
        axisLine: { show: true, lineStyle: { color: t.border } },
        axisTick: { show: false },
        axisLabel: {
            color: t.muted,
            fontFamily: FONT,
            fontSize: 11,
            hideOverlap: true,
            formatter: (v: unknown) =>
                typeof v === 'number' ? formatNumber(v) : String(v),
        },
        splitLine: { show: true, lineStyle: { color: t.grid, width: 1 } },
    };
}

/** Category-axis variant: no split lines, no axis line — cleaner for bars/lines. */
export function categoryAxis(t: ChartTokens) {
    return {
        ...axisStyle(t),
        splitLine: { show: false },
        axisLine: { show: true, lineStyle: { color: t.border } },
        axisLabel: { ...axisStyle(t).axisLabel },
    };
}

/** Crosshair pointer for line/bar — soft, theme-aware. */
export function axisPointer(t: ChartTokens, kind: 'line' | 'shadow') {
    return kind === 'shadow'
        ? { type: 'shadow' as const, shadowStyle: { color: withAlpha(t.muted, 0.12) } }
        : {
            type: 'line' as const,
            lineStyle: { color: t.muted, width: 1, type: [4, 4] as [number, number], opacity: 0.7 },
        };
}

/** Hover emphasis: focus the hovered series, gently fade the rest. */
export const focusEmphasis = {
    focus: 'series' as const,
    blurScope: 'coordinateSystem' as const,
};

/** Vertical gradient fill for line areas (colour → transparent). */
export function areaGradient(color: string) {
    return {
        color: {
            type: 'linear' as const,
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
                { offset: 0, color: withAlpha(color, 0.26) },
                { offset: 1, color: withAlpha(color, 0.02) },
            ],
        },
    };
}
