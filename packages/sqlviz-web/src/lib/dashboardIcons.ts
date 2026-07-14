/**
 * Dashboard icon resolution — DOC6 §12 sidebar.
 *
 * The BACKEND emits dashboard_hint + dashboard_domain.
 * The FRONTEND decides which icon to render (never the backend).
 *
 * Resolution order (first match wins):
 *   1. HINT_ICON_MAP[hint]
 *   2. DOMAIN_ICON_MAP[domain]
 *   3. INTENT_ICON_MAP[intentType]  (fallback when hint/domain absent)
 *   4. LayoutDashboard              (always present)
 */

import type { Component } from 'svelte';
import {
    Activity,
    ChartBar,
    ChartBarDecreasing,
    ChartLine,
    ChartPie,
    ChartScatter,
    Hash,
    LayoutDashboard,
    ListFilter,
    Table2,
    TrendingUp,
    TriangleAlert,
    Trophy,
    Users,
} from 'lucide-svelte';

// ── Level 1: hint → icon ────────────────────────────────────────────────────

export const HINT_ICON_MAP: Record<string, Component> = {
    // KPI
    kpi_overview:            Hash,
    kpi_performance:         TrendingUp,
    financial_kpi:           Hash,
    sales_kpi:               Hash,
    hr_overview:             Users,

    // Trend / growth
    trend_analysis:          TrendingUp,
    financial_trend:         TrendingUp,
    product_growth:          TrendingUp,
    sales_performance:       TrendingUp,
    marketing_performance:   TrendingUp,
    hr_trend:                TrendingUp,
    ops_monitoring:          Activity,

    // User lifecycle
    user_lifecycle:          Users,
    user_retention:          Users,
    retention_analysis:      Users,
    cohort_analysis:         Users,
    product_retention:       Users,

    // Funnel
    funnel_analysis:         ListFilter,
    product_funnel:          ListFilter,

    // Domain dashboards
    financial_dashboard:     TrendingUp,
    financial_comparison:    ChartBar,
    sales_dashboard:         TrendingUp,
    sales_ranking:           Trophy,
    marketing_analytics:     ChartLine,
    marketing_comparison:    ChartBar,
    product_analytics:       Users,
    hr_analytics:            Users,

    // Analysis types
    comparison_analysis:     ChartBar,
    competitive_analysis:    ChartBar,
    ranking_analysis:        Trophy,
    distribution_analysis:   ChartBarDecreasing,
    correlation_analysis:    ChartScatter,
    composition_analysis:    ChartPie,
    anomaly_detection:       TriangleAlert,
    anomaly_monitoring:      TriangleAlert,
    incident_monitoring:     TriangleAlert,
    data_detail:             Table2,
    analytics_overview:      LayoutDashboard,
};

// ── Level 2: domain → icon ──────────────────────────────────────────────────

export const DOMAIN_ICON_MAP: Record<string, Component> = {
    finance:   TrendingUp,
    product:   Users,
    marketing: ChartLine,
    hr:        Users,
    ops:       Activity,
    sales:     TrendingUp,
    analytics: LayoutDashboard,
};

// ── Level 3: intent_winner → icon (same as panel-level icons) ───────────────

export const INTENT_ICON_MAP: Record<string, Component> = {
    kpi:          Hash,
    trend:        TrendingUp,
    comparison:   ChartBar,
    ranking:      Trophy,
    composition:  ChartPie,
    distribution: ChartBarDecreasing,
    correlation:  ChartScatter,
    funnel:       ListFilter,
    retention:    Users,
    cohort:       Users,
    anomaly:      TriangleAlert,
    detail:       Table2,
};

// ── Resolver ────────────────────────────────────────────────────────────────

/**
 * Resolve the best icon for a dashboard.
 *
 * @param hint       dashboard_hint from the API (may be null/undefined)
 * @param domain     dashboard_domain from the API (may be null/undefined)
 * @param intentType dominant intent_winner across panels (optional level-3 fallback)
 * @returns A lucide-svelte icon component, always defined.
 */
export function resolveDashboardIcon(
    hint?: string | null,
    domain?: string | null,
    intentType?: string | null,
): Component {
    if (hint && HINT_ICON_MAP[hint])       return HINT_ICON_MAP[hint];
    if (domain && DOMAIN_ICON_MAP[domain]) return DOMAIN_ICON_MAP[domain];
    if (intentType && INTENT_ICON_MAP[intentType]) return INTENT_ICON_MAP[intentType];
    return LayoutDashboard;
}
