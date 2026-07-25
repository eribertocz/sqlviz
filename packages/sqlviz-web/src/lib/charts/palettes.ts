/**
 * Curated, modern categorical palettes for dashboard charts.
 *
 * Applied at the DASHBOARD level (every panel shares one palette) so a dashboard
 * always reads as one system. `brand` is the default and is CVD-validated with
 * the dataviz checker in both light and dark; the others are hand-curated,
 * modern sets inspired by developer-tool design systems.
 *
 * Colour follows the ENTITY by fixed slot order, never the rank — a filter that
 * changes the series count must not repaint the survivors.
 */
export type Palette = { id: string; name: string; colors: string[] };

export const PALETTES: Palette[] = [
    {
        id: 'brand',
        name: 'Brand',
        // Indigo-led; validated (adjacent CVD ΔE ≥ 8) in light + dark.
        colors: ['#6366f1', '#d95926', '#199e70', '#c98500', '#d55181', '#008300', '#9085e9', '#e66767'],
    },
    {
        id: 'vercel',
        name: 'Vercel',
        colors: ['#0070f3', '#8b5cf6', '#e5484d', '#f5a623', '#12a594', '#ff6b9d', '#7c3aed', '#0cce6b'],
    },
    {
        id: 'linear',
        name: 'Linear',
        colors: ['#5e6ad2', '#26b5ce', '#f2c94c', '#eb5757', '#4cb782', '#b59aff', '#e0794b', '#8590a2'],
    },
    {
        id: 'figma',
        name: 'Figma',
        colors: ['#0d99ff', '#9747ff', '#14ae5c', '#ffcd29', '#f24822', '#ff7ab2', '#1bc47d', '#ffa629'],
    },
    {
        id: 'midnight',
        name: 'Midnight',
        // Deep, cool blues + violets with teal/pink accents.
        colors: ['#6366f1', '#22d3ee', '#a855f7', '#3b82f6', '#ec4899', '#14b8a6', '#818cf8', '#c084fc'],
    },
    {
        id: 'aurora',
        name: 'Aurora',
        // Vivid greens → teals → blues → violets (northern-lights).
        colors: ['#34d399', '#22d3ee', '#818cf8', '#a78bfa', '#4ade80', '#2dd4bf', '#60a5fa', '#c084fc'],
    },
    {
        id: 'emerald',
        name: 'Emerald',
        colors: ['#10b981', '#14b8a6', '#059669', '#34d399', '#0d9488', '#6ee7b7', '#047857', '#5eead4'],
    },
    {
        id: 'graphite',
        name: 'Graphite',
        // Cool slate ramp — minimal dashboards; lightness carries the identity.
        colors: ['#475569', '#64748b', '#334155', '#94a3b8', '#1e293b', '#cbd5e1', '#0f172a', '#e2e8f0'],
    },
    {
        id: 'monochrome',
        name: 'Monochrome',
        // Neutral grayscale ramp — single-metric / print-friendly.
        colors: ['#525252', '#737373', '#404040', '#a3a3a3', '#262626', '#d4d4d4', '#171717', '#e5e5e5'],
    },
];

export const DEFAULT_PALETTE_ID = 'brand';

export function getPaletteById(id: string | null | undefined): Palette {
    return PALETTES.find(p => p.id === id) ?? PALETTES[0];
}

/** The default brand palette colours (used when a dashboard sets no override). */
export const BRAND_COLORS: string[] = PALETTES[0].colors;
