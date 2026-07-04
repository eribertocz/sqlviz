/**
 * Mirror of FilterControl (filters/filter_engine.py).
 * Populated by the inference pipeline whenever the SQL contains $variables.
 * For range controls (date_range_picker, range_slider), `variable` is
 * "var1,var2" (comma-separated) — the pair produced by range_pairing.py.
 */
export interface FilterControl {
    variable: string;    // "$region" → "region"; range → "start,end"
    label: string;       // Human-readable column label
    control_type:
        | 'dropdown'
        | 'multiselect'
        | 'date_picker'
        | 'date_range_picker'
        | 'numeric'
        | 'range_slider'
        | 'search'
        | 'toggle';
    column_name: string;
    column_type: string;
    scope: string;       // "global" for now
}

/**
 * TypeScript mirrors of the sqlviz_inference data structures.
 *
 * InferenceResult  — result.py (from POST /api/v1/panels/{id}/execute)
 * DashboardPanel   — dashboard_engine.py, within a DashboardLayout row
 * DashboardRow     — dashboard_engine.py
 * DashboardLayout  — dashboard_engine.py (from GET /api/v1/demo/dashboard)
 */
export interface InferenceResult {
    // Versioning
    rules_version: string;
    feature_vector_version: string;
    engine_version: string;

    // Intent
    intent_winner: string;
    intent_raw_score: number;
    intent_normalized_score: number;
    intent_confidence_gap: number;
    intent_quality: string;
    intent_alternatives: Array<{ intent: string; raw_score: number }>;

    // Chart
    chart_winner: string;
    chart_raw_score: number;
    chart_normalized_score: number;
    chart_confidence_gap: number;
    chart_quality: string;
    chart_alternatives: Array<{ chart: string; raw_score: number }>;

    // Layout — consumed directly by DashboardGrid (DOC6 §4.1)
    col_span: number;         // 1-12
    row_span: number;         // 1-3
    layout_importance: number;
    panel_height_px: number;  // exact pixel height, computed by LayoutEngine

    // KPI trend — pre-computed by backend (DOC5 §16.6, never inferred in frontend)
    trend_direction_label: 'growing' | 'declining' | 'flat' | 'unknown';

    // Filters
    filter_controls: FilterControl[];

    // Title
    title: string;
    title_confidence: number;

    // Fallback
    fallback_applied: boolean;
    fallback_reason: string;

    // Explainability
    explanation: unknown[];
    score_trace: Record<string, unknown>;
    fingerprint: string;
    feature_vector: number[];

    // Diagnostics
    errors: string[];
    elapsed_ms: number;
}

/** Mirror of DashboardPanel (dashboard_engine.py) plus query result data. */
export interface DashboardPanel {
    panel_id: string;
    final_col_span: number;   // may differ from inference_result.col_span (KPI grouping)
    col_offset: number;       // leading empty columns before the first panel in a KPI row
    row_index: number;
    data: Record<string, unknown>[];   // query result rows (from demo endpoint)
    inference_result: InferenceResult;
}

/** Mirror of DashboardRow (dashboard_engine.py). */
export interface DashboardRow {
    panels: DashboardPanel[];
}

/** Mirror of DashboardLayout (dashboard_engine.py, DOC5 §15.4). */
export interface DashboardLayout {
    rows: DashboardRow[];
}
