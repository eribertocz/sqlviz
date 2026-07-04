<script lang="ts">
    import { onMount } from 'svelte';
    import * as echarts from 'echarts';
    import type { InferenceResult } from '$lib/types';

    let { chartType, result, data }: {
        chartType: string;
        result: InferenceResult;
        data: Record<string, unknown>[];
    } = $props();

    // DOC6 §2 colors reproduced as JS constants (CSS vars not readable by ECharts)
    const C = {
        primary:  '#6366f1',
        positive: '#22c55e',
        negative: '#ef4444',
        neutral:  '#94a3b8',
        text:     '#f1f5f9',
        muted:    '#94a3b8',
        border:   '#334155',
        palette:  ['#6366f1', '#22c55e', '#f59e0b', '#06b6d4', '#ef4444', '#a78bfa', '#fbbf24', '#34d399'],
    };

    const BASE: echarts.EChartsOption = {
        backgroundColor: 'transparent',
        animation: false,
        grid: { top: 12, right: 16, bottom: 36, left: 48, containLabel: true },
        textStyle: { color: C.text, fontFamily: 'Inter, system-ui, sans-serif', fontSize: 11 },
        tooltip: {
            backgroundColor: '#1e293b',
            borderColor: C.border,
            textStyle: { color: C.text },
        },
    };

    function buildOption(): echarts.EChartsOption {
        if (data.length === 0) return BASE;

        const keys = Object.keys(data[0]);
        // Convention: first column = category / x-axis; last column = primary value
        const xKey = keys[0];
        const yKey = keys[keys.length - 1];
        const xData = data.map(r => String(r[xKey]));
        const yData = data.map(r => Number(r[yKey]));

        const axisStyle = {
            axisLine:  { lineStyle: { color: C.border } },
            axisLabel: { color: C.muted },
            splitLine: { lineStyle: { color: C.border, opacity: 0.5 } },
        };

        switch (chartType) {
            case 'line':
                return {
                    ...BASE,
                    xAxis: { type: 'category', data: xData, ...axisStyle },
                    yAxis: { type: 'value', ...axisStyle },
                    series: [{
                        type: 'line',
                        data: yData,
                        smooth: 0.4,
                        color: C.primary,
                        lineStyle: { width: 2 },
                        areaStyle: { opacity: 0.08 },
                        symbol: 'circle',
                        symbolSize: 5,
                    }],
                };

            case 'bar':
                return {
                    ...BASE,
                    xAxis: { type: 'category', data: xData, ...axisStyle },
                    yAxis: { type: 'value', ...axisStyle },
                    series: [{
                        type: 'bar',
                        data: yData,
                        color: C.primary,
                        barMaxWidth: 48,
                        itemStyle: { borderRadius: [3, 3, 0, 0] },
                    }],
                };

            case 'bar_horizontal':
                return {
                    ...BASE,
                    grid: { top: 12, right: 16, bottom: 16, left: 80, containLabel: true },
                    xAxis: { type: 'value', ...axisStyle },
                    yAxis: { type: 'category', data: xData, inverse: true, ...axisStyle },
                    series: [{
                        type: 'bar',
                        data: yData,
                        color: C.primary,
                        barMaxWidth: 32,
                        itemStyle: { borderRadius: [0, 3, 3, 0] },
                    }],
                };

            case 'pie':
                return {
                    ...BASE,
                    grid: undefined,
                    series: [{
                        type: 'pie',
                        radius: ['30%', '65%'],
                        data: data.map((r, i) => ({
                            name: String(r[xKey]),
                            value: Number(r[yKey]),
                            itemStyle: { color: C.palette[i % C.palette.length] },
                        })),
                        label: { color: C.muted, fontSize: 11 },
                        emphasis: { label: { color: C.text, fontWeight: 'bold' } },
                    }],
                };

            case 'scatter': {
                // Scatter: first two numeric columns as x, y
                const numKeys = keys.filter(k => typeof data[0][k] === 'number');
                const sx = numKeys[0] ?? keys[0];
                const sy = numKeys[1] ?? keys[1] ?? keys[0];
                return {
                    ...BASE,
                    xAxis: { type: 'value', name: sx, ...axisStyle },
                    yAxis: { type: 'value', name: sy, ...axisStyle },
                    series: [{
                        type: 'scatter',
                        data: data.map(r => [Number(r[sx]), Number(r[sy])]),
                        symbolSize: 8,
                        color: C.primary,
                    }],
                };
            }

            case 'histogram':
                return {
                    ...BASE,
                    xAxis: { type: 'category', data: xData, ...axisStyle },
                    yAxis: { type: 'value', ...axisStyle },
                    series: [{
                        type: 'bar',
                        data: yData,
                        color: C.primary,
                        barCategoryGap: '2%',
                        itemStyle: { borderRadius: 0 },
                    }],
                };

            default:
                return BASE;
        }
    }

    let container: HTMLDivElement;
    let chart: echarts.ECharts | null = null;

    onMount(() => {
        chart = echarts.init(container);
        chart.setOption(buildOption());

        const ro = new ResizeObserver(() => chart?.resize());
        ro.observe(container);

        return () => {
            ro.disconnect();
            chart?.dispose();
            chart = null;
        };
    });

    // Re-render when data or chartType changes after mount
    $effect(() => {
        const _dep = [chartType, data, result];  // track dependencies
        if (chart) chart.setOption(buildOption(), { notMerge: true });
    });
</script>

<div bind:this={container} class="chart-container"></div>

<style>
    .chart-container {
        flex: 1;
        min-height: 140px;
        width: 100%;
    }
</style>
