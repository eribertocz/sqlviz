<script lang="ts">
    import { onMount } from 'svelte';
    import * as echarts from 'echarts';
    import type { VisualSpec } from '$lib/types';
    import { uiStore } from '$lib/stores/uiStore.svelte';
    import { readChartTokens, prefersReducedMotion, type ChartTokens } from '$lib/charts/chartTokens';
    import {
        baseOption, axisStyle, categoryAxis, axisPointer, focusEmphasis, areaGradient, stagger,
        axisName, cartesianGrid,
    } from '$lib/charts/chartBase';
    import { BRAND_COLORS } from '$lib/charts/palettes';

    let { visualSpec, data, palette, hideAxisNames = false }: {
        visualSpec: VisualSpec | null;
        data: Record<string, unknown>[];
        // Dashboard-level palette; falls back to the brand palette.
        palette?: string[];
        // Edit mode overlays editable HTML axis titles → hide ECharts' own.
        hideAxisNames?: boolean;
    } = $props();

    const reduce = prefersReducedMotion();

    function buildOption(t: ChartTokens): echarts.EChartsOption {
        const BASE = baseOption(t, reduce);
        if (!visualSpec || data.length === 0) return BASE;

        const PAL = (palette && palette.length > 0) ? palette : BRAND_COLORS;
        const xField = visualSpec.x_field ?? '';
        const yField = visualSpec.y_fields[0] ?? '';
        // Axis titles: user override (x_label/y_label) wins, else the field name.
        // Blanked in edit mode where PanelRenderer overlays editable HTML titles.
        const xName = hideAxisNames ? '' : ((visualSpec.x_label || xField) ?? '');
        const yName = hideAxisNames ? '' : ((visualSpec.y_label || yField) ?? '');
        const xData = xField ? data.map(r => String(r[xField])) : [];
        const yData = yField ? data.map(r => Number(r[yField])) : [];
        const delay = stagger(reduce);

        switch (visualSpec.chart_type) {
            case 'line':
                return {
                    ...BASE,
                    grid: cartesianGrid,
                    tooltip: { ...BASE.tooltip, trigger: 'axis', axisPointer: axisPointer(t, 'line') },
                    xAxis: { type: 'category', boundaryGap: false, data: xData, ...categoryAxis(t), ...axisName(t, xName, 'middle') },
                    yAxis: { type: 'value', ...axisStyle(t), ...axisName(t, yName, 'left') },
                    series: [{
                        type: 'line',
                        data: yData,
                        smooth: 0.35,
                        color: PAL[0],
                        lineStyle: { width: 2 },
                        areaStyle: areaGradient(PAL[0]),
                        symbol: 'circle',
                        symbolSize: 7,
                        showSymbol: false,
                        emphasis: { ...focusEmphasis, scale: 1.4 },
                        animationDelay: delay,
                    }],
                };

            case 'bar':
                return {
                    ...BASE,
                    grid: cartesianGrid,
                    tooltip: { ...BASE.tooltip, trigger: 'axis', axisPointer: axisPointer(t, 'shadow') },
                    xAxis: { type: 'category', data: xData, ...categoryAxis(t), ...axisName(t, xName, 'middle') },
                    yAxis: { type: 'value', ...axisStyle(t), ...axisName(t, yName, 'left') },
                    series: [{
                        type: 'bar',
                        data: yData,
                        color: PAL[0],
                        barMaxWidth: 46,
                        itemStyle: { borderRadius: [4, 4, 0, 0] },
                        emphasis: { focus: 'series', itemStyle: { shadowBlur: 12, shadowColor: 'rgba(0,0,0,0.22)' } },
                        animationDelay: delay,
                    }],
                };

            case 'bar_horizontal':
                return {
                    ...BASE,
                    grid: { top: 26, right: 20, bottom: 40, left: 90, containLabel: true },
                    tooltip: { ...BASE.tooltip, trigger: 'axis', axisPointer: axisPointer(t, 'shadow') },
                    xAxis: { type: 'value', ...axisStyle(t), ...axisName(t, yName, 'middle') },
                    yAxis: { type: 'category', data: xData, inverse: true, ...categoryAxis(t), ...axisName(t, xName, 'end') },
                    series: [{
                        type: 'bar',
                        data: yData,
                        color: PAL[0],
                        barMaxWidth: 30,
                        itemStyle: { borderRadius: [0, 4, 4, 0] },
                        emphasis: { focus: 'series', itemStyle: { shadowBlur: 12, shadowColor: 'rgba(0,0,0,0.22)' } },
                        animationDelay: delay,
                    }],
                };

            case 'pie':
                return {
                    ...BASE,
                    grid: undefined,
                    tooltip: { ...BASE.tooltip, trigger: 'item' },
                    series: [{
                        type: 'pie',
                        radius: ['42%', '70%'],
                        avoidLabelOverlap: true,
                        padAngle: 2,
                        itemStyle: { borderColor: t.surface, borderWidth: 2, borderRadius: 4 },
                        data: data.map((r, i) => ({
                            name: String(r[xField]),
                            value: Number(r[yField]),
                            itemStyle: { color: PAL[i % PAL.length] },
                        })),
                        label: { color: t.muted, fontSize: 11 },
                        labelLine: { lineStyle: { color: t.border } },
                        emphasis: {
                            scale: true, scaleSize: 6,
                            label: { color: t.text, fontWeight: 'bold' },
                            itemStyle: { shadowBlur: 16, shadowColor: 'rgba(0,0,0,0.28)' },
                        },
                        animationType: reduce ? undefined : 'scale',
                        animationDelay: delay,
                    }],
                };

            case 'scatter': {
                const sx = visualSpec.x_field ?? '';
                const sy = visualSpec.y_fields[0] ?? '';
                return {
                    ...BASE,
                    grid: cartesianGrid,
                    tooltip: { ...BASE.tooltip, trigger: 'item', axisPointer: axisPointer(t, 'line') },
                    xAxis: { type: 'value', ...axisStyle(t), ...axisName(t, xName, 'middle') },
                    yAxis: { type: 'value', ...axisStyle(t), ...axisName(t, yName, 'left') },
                    series: [{
                        type: 'scatter',
                        data: data.map(r => [Number(r[sx]), Number(r[sy])]),
                        symbolSize: 9,
                        color: PAL[0],
                        itemStyle: { opacity: 0.78, borderColor: t.surface, borderWidth: 1 },
                        emphasis: { focus: 'series', scale: 1.5, itemStyle: { opacity: 1 } },
                        animationDelay: delay,
                    }],
                };
            }

            case 'histogram':
                return {
                    ...BASE,
                    grid: cartesianGrid,
                    tooltip: { ...BASE.tooltip, trigger: 'axis', axisPointer: axisPointer(t, 'shadow') },
                    xAxis: { type: 'category', data: xData, ...categoryAxis(t), ...axisName(t, xName, 'middle') },
                    yAxis: { type: 'value', ...axisStyle(t), ...axisName(t, yName, 'left') },
                    series: [{
                        type: 'bar',
                        data: yData,
                        color: PAL[0],
                        barCategoryGap: '2%',
                        itemStyle: { borderRadius: [2, 2, 0, 0] },
                        emphasis: { focus: 'series', itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.2)' } },
                        animationDelay: delay,
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
        chart.setOption(buildOption(readChartTokens()));

        const ro = new ResizeObserver(() => chart?.resize());
        ro.observe(container);

        return () => {
            ro.disconnect();
            chart?.dispose();
            chart = null;
        };
    });

    // Re-render on data/spec/palette change AND on theme toggle (tokens change).
    $effect(() => {
        const _dep = [visualSpec, data, palette, uiStore.theme, hideAxisNames];
        void _dep;
        if (chart) chart.setOption(buildOption(readChartTokens()), { notMerge: true });
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
