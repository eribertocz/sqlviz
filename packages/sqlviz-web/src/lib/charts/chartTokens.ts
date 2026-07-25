/**
 * Reads the live SQLviz design tokens so charts are driven by CSS variables
 * instead of hardcoded colours. ECharts can't read CSS vars directly, so we
 * resolve them once per render via getComputedStyle — call this again whenever
 * the theme changes and re-apply the option, and charts follow light/dark.
 */
export type ChartTokens = {
    text: string;
    muted: string;
    border: string;
    surface: string;
    primary: string;
    positive: string;
    negative: string;
    /** Recessive grid line colour (a faint tint of text). */
    grid: string;
};

function cssVar(styles: CSSStyleDeclaration, name: string, fallback: string): string {
    const v = styles.getPropertyValue(name).trim();
    return v || fallback;
}

export function readChartTokens(): ChartTokens {
    // SSR / test guard.
    if (typeof window === 'undefined' || typeof getComputedStyle === 'undefined') {
        return {
            text: '#f1f5f9', muted: '#94a3b8', border: '#334155', surface: '#1e293b',
            primary: '#5b5bd6', positive: '#22c55e', negative: '#ef4444',
            grid: 'rgba(148,163,184,0.16)',
        };
    }
    const s = getComputedStyle(document.documentElement);
    const text = cssVar(s, '--sqlviz-text', '#f1f5f9');
    return {
        text,
        muted: cssVar(s, '--sqlviz-text-muted', '#94a3b8'),
        border: cssVar(s, '--sqlviz-border', '#334155'),
        surface: cssVar(s, '--sqlviz-bg-surface', '#1e293b'),
        primary: cssVar(s, '--sqlviz-primary', '#5b5bd6'),
        positive: cssVar(s, '--sqlviz-positive', '#22c55e'),
        negative: cssVar(s, '--sqlviz-negative', '#ef4444'),
        // Faint, theme-aware grid — recessive, never competes with the marks.
        grid: withAlpha(cssVar(s, '--sqlviz-text-muted', '#94a3b8'), 0.16),
    };
}

/** Convert a #rgb/#rrggbb colour to rgba() with alpha. ECharts/zrender parse
 *  rgba() reliably (unlike CSS color-mix), so we resolve alpha here. */
export function withAlpha(color: string, alpha: number): string {
    let hex = color.trim();
    if (hex.startsWith('#')) hex = hex.slice(1);
    if (hex.length === 3) hex = hex.split('').map(c => c + c).join('');
    if (hex.length !== 6) return color; // not a hex we can parse — pass through
    const r = parseInt(hex.slice(0, 2), 16);
    const g = parseInt(hex.slice(2, 4), 16);
    const b = parseInt(hex.slice(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

export function prefersReducedMotion(): boolean {
    return typeof window !== 'undefined'
        && typeof window.matchMedia === 'function'
        && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/** Compact number formatting for axes + tooltips (1.2k, 3.4M, tidy decimals). */
export function formatNumber(value: unknown): string {
    const n = typeof value === 'number' ? value : Number(value);
    if (!Number.isFinite(n)) return String(value ?? '');
    const abs = Math.abs(n);
    if (abs >= 1_000_000_000) return trim(n / 1_000_000_000) + 'B';
    if (abs >= 1_000_000) return trim(n / 1_000_000) + 'M';
    if (abs >= 1_000) return trim(n / 1_000) + 'k';
    if (Number.isInteger(n)) return n.toLocaleString();
    return trim(n);
}

function trim(n: number): string {
    return (Math.round(n * 100) / 100).toLocaleString(undefined, { maximumFractionDigits: 2 });
}
