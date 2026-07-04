# SQLviz — UI Design System
**Version:** v0.1.0 (Draft)
**Status:** Work in Progress
**Last Updated:** 2026-06-08
**Prerequisites:** DOC 1 (Vision & Philosophy), DOC 3 (Technical Stack, Sections 3 & 6-7),
DOC 5 (Inference Engine — consumes its output directly), DOC 7 (Security & Roles)

---

## 1. Purpose of This Document

DOC 1 states the philosophy: "the user writes SQL, SQLviz infers
everything else." DOC 5 is the engine that makes that true. This
document is the **face** that makes it *visible* — the exact
visual language, components, and layout rules that turn an
`InferenceResult` (DOC 5, Section 12.4) and a `DashboardLayout`
(DOC 5, Section 15.4) into pixels on screen.

```
DOC 1  →  the user writes SQL, sees a dashboard      (the promise)
DOC 5  →  InferenceResult + DashboardLayout           (the data)
DOC 6  →  exact components, colors, spacing            (this document)
          that render that data without the user
          ever touching layout, color, or chart config
```

### 1.1 The One Rule That Governs Every Decision in This Document

```
The frontend NEVER infers. The frontend ONLY renders.

Every chart_winner, col_span, row_span, title, and
filter_controls value arrives already decided from
sqlviz-api (DOC 5's output, DOC 3 Section 9's "frontend
never infers" rule, restated here because DOC 6 is where
violating it would actually happen if not careful).

If implementing a UI component requires a decision about
WHAT to show (not HOW to show it) — that decision belongs
in sqlviz-inference (DOC 5), not here.
```

---

## 2. Design Tokens

These are already defined in DOC 3, Section 6, reproduced here
as the canonical source because DOC 6 is where they are
actually consumed. If DOC 3's copy and this one ever diverge,
**this document wins** — DOC 3 will be updated to match.

```css
:root {
  /* Color */
  --sqlviz-primary:       #6366f1;  /* indigo — brand, CTAs, links */
  --sqlviz-primary-hover: #818cf8;
  --sqlviz-bg:            #0f172a;  /* dark background (default theme) */
  --sqlviz-bg-surface:    #1e293b;  /* card / panel background */
  --sqlviz-border:        #334155;
  --sqlviz-text:          #f1f5f9;  /* primary text */
  --sqlviz-text-muted:    #94a3b8;  /* secondary text, metadata */

  /* Semantic colors — used ONLY for KPI trend indicators
     (DOC 4, Section 8.2 trend direction; DOC 5 Section 16.2
     dim 38 trend_direction feeds this directly) */
  --sqlviz-positive:      #22c55e;  /* green — growing KPI */
  --sqlviz-negative:      #ef4444;  /* red — declining KPI */
  --sqlviz-neutral:       #94a3b8;  /* gray — flat KPI */

  /* Geometry */
  --sqlviz-radius:        6px;
  --sqlviz-radius-lg:     10px;
  --sqlviz-gap:           16px;     /* the gap between grid panels —
                                       see Section 4.2, must match
                                       the spacing assumed by
                                       DOC 5 Section 9 col_span math */

  /* Typography */
  --sqlviz-font-sans:     'Inter', system-ui, sans-serif;
  --sqlviz-font-mono:     'JetBrains Mono', 'Fira Code', monospace;
                          /* used ONLY in the Monaco editor and
                             execution-time/row-count metadata —
                             DOC 3 Section 3 Monaco integration */
}

[data-theme="light"] {
  --sqlviz-bg:            #ffffff;
  --sqlviz-bg-surface:    #f8fafc;
  --sqlviz-border:        #e2e8f0;
  --sqlviz-text:          #0f172a;
  --sqlviz-text-muted:    #64748b;
  /* --sqlviz-primary and semantic colors stay the same in both themes —
     this is a deliberate consistency choice, not an oversight */
}
```

### 2.1 Why These Specific Choices

```
Indigo (#6366f1) as primary:
    Distinct from the "default Bootstrap blue" (#0d6efd) that
    signals "generic admin template." SQLviz should not look
    like every other internal tool. Already used consistently
    in v0.1 prototype screenshots reviewed earlier in this
    project — kept for continuity, not re-litigated here.

Dark theme as default, not light:
    SQL editors and data tools are conventionally dark-first
    (VS Code, DataGrip, most modern BI tools default dark).
    Matches Monaco's natural habitat (DOC 3, Section 3).

JetBrains Mono / Fira Code for monospace:
    Both have programming ligatures and are free/open license
    (DOC 3, Section 9, dependency philosophy applies to fonts
    too — no paid font licenses).
```

---

## 3. Layout Philosophy — What Changed From the V0.1 Prototype

The original SQLviz prototype (rescued lessons, referenced in
DOC 1's "lessons learned") had the user manually create rows,
drag panels, and configure widths. This was identified during
that prototype's review as **breaking the core philosophy** —
the UI made the user think about the tool instead of the data.

DOC 5's Dashboard Engine (Section 15) now does this work
automatically. This document's job is to render its output,
**not to provide manual row/drag/width controls as the primary
interaction model.**

```
V0.1 Prototype (rejected pattern — DO NOT reintroduce):
    [+ Add row] → [+ Add panel] → drag to position →
    configure width % → configure height px

SQLviz V0.1 (this document):
    User writes SQL → panel appears, already positioned by
    DashboardEngine.compose() (DOC 5, Section 15.4) →
    DONE. No manual layout step exists in the primary flow.
```

A minimal override exists (Section 7) for the rare case where
inference gets it wrong — but it is explicitly an *escape
hatch*, never the expected interaction.

---

## 4. The Dashboard Grid

### 4.1 CSS Grid, 12 Columns — Consuming DOC 5's Output Directly

DOC 5 Section 9 (Layout Engine) and Section 15 (Dashboard
Engine) already compute `col_span` (1-12) and `row_span` (1-3)
per panel, and group panels into `DashboardRow` objects. This
section is the literal CSS that renders that data structure —
no additional layout logic exists in the frontend.

```css
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: var(--sqlviz-gap);
  padding: var(--sqlviz-gap);
}

.dashboard-panel {
  grid-column: span var(--panel-col-span);
  grid-row: span var(--panel-row-span);
  background: var(--sqlviz-bg-surface);
  border: 1px solid var(--sqlviz-border);
  border-radius: var(--sqlviz-radius-lg);
  overflow: hidden;
}
```

```svelte
<!-- DashboardGrid.svelte — renders DashboardLayout from DOC 5 Section 15.4 -->
<script lang="ts">
  import type { DashboardLayout } from '$lib/types';
  export let layout: DashboardLayout;
</script>

<div class="dashboard-grid">
  {#each layout.rows as row}
    {#each row.panels as panel}
      <div
        class="dashboard-panel"
        style="--panel-col-span: {panel.final_col_span};
               --panel-row-span: {panel.inference_result.row_span}"
      >
        <PanelRenderer result={panel.inference_result} />
      </div>
    {/each}
  {/each}
</div>
```

**Note the absence of any client-side logic deciding position,
span, or order** — `layout.rows` arrives pre-computed and is
iterated in the exact sequence `DashboardEngine.compose()`
produced. This is the direct, literal embodiment of Section 1.1.

### 4.2 Why the Gap Must Match Both Themes' Visual Weight

```
--sqlviz-gap: 16px applies identically in dark and light theme.
A panel with col_span=6 in a 12-column grid with 16px gaps
occupies exactly the same proportion of the viewport regardless
of theme — DashboardEngine's row-packing math (DOC 5, Section
15.3, Rule 3) assumes panels of a given col_span are visually
equal-weight; an inconsistent gap between themes would silently
break that assumption's visual truth even though the underlying
data is identical.
```

---

## 5. Panel Anatomy

### 5.1 Structure

```
┌─────────────────────────────────────┐
│ Title                          [···] │  ← header: title (DOC 5 §11) +
│                                       │     overflow menu (Section 7)
│                                       │
│            [chart renders here]      │  ← body: ECharts/Plotly per
│                                       │     chart_winner (DOC 5 §8)
│                                       │
├───────────────────────────────────────┤
│ 64ms · 1,204 rows · DuckDB            │  ← footer: execution metadata
└─────────────────────────────────────┘     (edit mode only — Section 6)
```

### 5.2 Title Rendering

```svelte
<!-- PanelHeader.svelte -->
<script lang="ts">
  export let title: string;          // DOC 5 Section 11 TitleResult.title
  export let titleConfidence: number; // DOC 5 Section 11 title_confidence
</script>

<div class="panel-header">
  <h3 class="panel-title">{title || 'Untitled query'}</h3>
  <!-- fallback "Untitled query" only fires when TitleEngine's
       graceful degradation (DOC 5 Section 11.3) returned ""
       — this is the one place the frontend supplies a string
       the backend didn't, and it is explicitly NOT an inference,
       just a placeholder label, consistent with Section 1.1 -->
</div>
```

```
titleConfidence is NOT shown visually as a number or badge in
V0.1. DOC 5's explainability data (score_trace, confidence_gap)
is surfaced through the "Why this chart?" panel (Section 8),
not scattered as inline confidence indicators next to every
title — that would clutter the dashboard and contradicts DOC 1
Principle 2 ("infer everything, the user should rarely need to
think about confidence at all").
```

### 5.3 Chart Body — Engine Selection

```svelte
<!-- PanelRenderer.svelte -->
<script lang="ts">
  import type { InferenceResult } from '$lib/types';
  import EChartsRenderer from './EChartsRenderer.svelte';
  import KPIRenderer from './KPIRenderer.svelte';
  import TableRenderer from './TableRenderer.svelte';

  export let result: InferenceResult;
</script>

<PanelHeader title={result.title} titleConfidence={result.title_confidence} />

{#if result.chart_winner === 'kpi'}
  <KPIRenderer {result} />
{:else if result.chart_winner === 'table'}
  <TableRenderer {result} />
{:else}
  <EChartsRenderer chartType={result.chart_winner} {result} />
{/if}

<PanelFooter {result} />
```

```
Why KPI and Table get dedicated Svelte components instead of
going through ECharts:
    KPI (DOC 5 Section 13.3 — col_span=3, the smallest panel
    type) is a number + label + optional trend arrow, not a
    chart in the visualization-library sense. Forcing it
    through ECharts would mean configuring an invisible axis
    system to display one number — unnecessary complexity.
    Table is plain HTML <table> for the same reason: DOC 5's
    8 V0.1 chart types (Section 13.3) include exactly one
    "show the raw rows" type, and HTML tables already do that
    correctly with zero charting-library overhead.
```

### 5.3.1 Chart Type Support — V0.1, V0.2, V1 Roadmap

EChartsRenderer.svelte is already built on ECharts. Adding a new
chart type in V0.2 requires only a new `case` in the switch/
dispatcher and the corresponding ECharts series configuration —
no architectural changes. ECharts supports all types below natively.

```
Chart type               Version    Status        Notes
────────────────────────────────────────────────────────────────
kpi                      V0.1       IMPLEMENTED   KPIRenderer.svelte
line                     V0.1       IMPLEMENTED   EChartsRenderer
bar                      V0.1       IMPLEMENTED   EChartsRenderer
bar_horizontal           V0.1       IMPLEMENTED   EChartsRenderer
pie                      V0.1       IMPLEMENTED   EChartsRenderer
scatter                  V0.1       IMPLEMENTED   EChartsRenderer
table                    V0.1       IMPLEMENTED   TableRenderer.svelte
histogram                V0.1       IMPLEMENTED   EChartsRenderer

── V0.2: Combos básicos (2 tipos de serie mezclados) ───────────
combo_line_bar           V0.2       PLANNED       line + bar mismo eje
                                                  (tendencia + volumen)
combo_line_area          V0.2       PLANNED       line + area rellena
combo_bar_line_dual      V0.2       PLANNED       bar + line, eje Y dual
combo_line_scatter       V0.2       PLANNED       tendencia + puntos
combo_bar_scatter        V0.2       PLANNED       comparación + correlac.
waterfall                V0.2       PLANNED       bridge chart, P&L
area_stacked             V0.2       PLANNED       composición temporal
bar_stacked              V0.2       PLANNED       composición categórica

── V0.2: Chart types nuevos independientes ─────────────────────
boxplot                  V0.2       PLANNED       distribución estadística
treemap                  V0.2       PLANNED       jerarquía + drill-down
heatmap                  V0.2       PLANNED       matriz de valores
funnel_chart             V0.2       PLANNED       embudo real
                                                  (intent=funnel existe,
                                                  falta el chart type)
gauge                    V0.2       PLANNED       velocímetro KPI + target
sankey                   V0.2       PLANNED       flujos entre nodos

── V1: Combos avanzados (3+ series, alta complejidad) ──────────
combo_triple             V1         FUTURE        bar + line + scatter
candlestick_volume       V1         FUTURE        OHLC financiero + vol.
heatmap_line             V1         FUTURE        heatmap + tendencia
radar                    V1         FUTURE        araña multidimensional
parallel                 V1         FUTURE        coordenadas paralelas
sunburst                 V1         FUTURE        jerarquía radial
bubble                   V1         FUTURE        scatter 3 variables
                                                  (x, y, tamaño)
```

```
Work required per new V0.2 chart type (no architectural changes):
1. Nueva entrada en chart_affinity_matrix.yaml
   (qué intents favorecen este chart)
2. Nueva entrada en chart_penalties.yaml si aplica
3. Nueva serie/configuración en EChartsRenderer.svelte
   (un nuevo case en el switch de chartType)
4. Nuevo case en el dispatcher de PanelRenderer.svelte
   si el chart requiere un renderer dedicado (como KPI
   y Table — la mayoría de V0.2 irán por EChartsRenderer)

ECharts ya soporta todos estos nativamente.
El único trabajo es el "puente" de inferencia (YAML)
y la configuración de series (Svelte).
```

### 5.4 KPI Renderer — Consuming trend_direction_label (DOC 5 Section 16.6)

> **Correction (third review round):** an earlier version of this
> component computed `trendClass`/`trendIcon` directly from
> `result.feature_vector[38]` and `result.feature_vector[28]`
> using hardcoded thresholds (0.65/0.35) in Svelte. That was a
> semantic decision made in the rendering layer — a direct
> violation of this document's own Section 1.1 rule. The fix
> (DOC 5, Section 16.6) moved threshold evaluation into
> `InferenceResult.from_context()`, which now returns a single
> pre-computed `trend_direction_label: "growing"|"declining"|
> "flat"|"unknown"`. The component below reads only that string —
> no `feature_vector` indexing, no thresholds, in the frontend.

```svelte
<!-- KPIRenderer.svelte -->
<script lang="ts">
  export let result: InferenceResult;

  // trend_direction_label arrives already decided by the backend
  // (DOC 5 Section 16.6) — this is a pure lookup table, not a
  // decision. Mapping a known string to an icon/color is
  // rendering; deciding "growing vs declining" from raw numbers
  // would not be.
  const TREND_DISPLAY = {
    growing:   { icon: '↑', class: 'positive' },
    declining: { icon: '↓', class: 'negative' },
    flat:      { icon: '→', class: 'neutral'  },
    unknown:   { icon: '',  class: 'neutral'  }, // no arrow shown at all
  } as const;

  $: trend = TREND_DISPLAY[result.trend_direction_label];
</script>

<div class="kpi-body">
  <div class="kpi-value">{formatNumber(result.kpi_value)}</div>
  {#if result.trend_direction_label !== 'unknown'}
    <span class="kpi-trend {trend.class}">{trend.icon}</span>
  {/if}
</div>

<style>
  .kpi-trend.positive { color: var(--sqlviz-positive); }
  .kpi-trend.negative { color: var(--sqlviz-negative); }
  .kpi-trend.neutral   { color: var(--sqlviz-neutral); }
</style>
```

### 5.5 Footer — Execution Metadata, Edit Mode Only

```svelte
<!-- PanelFooter.svelte -->
<script lang="ts">
  export let result: InferenceResult;
  import { editMode } from '$lib/stores/dashboard';
</script>

{#if $editMode}
  <div class="panel-footer">
    {formatMs(result.elapsed_ms)} · {formatRowCount(result.row_count)} rows · DuckDB
  </div>
{/if}
```

```
This was an explicit bug fix during the V0.1 prototype review
(rescued lesson): preview mode was showing execution metadata
and editor chrome that should only appear in edit mode. The
fix — gating on $editMode — is now a first-class rule of this
design system, not an afterthought: Section 6 makes the
preview/edit distinction explicit everywhere it matters.
```

---

## 6. Preview Mode vs Edit Mode

This distinction governs visibility of every "tool" element
(footers, overflow menus, drag handles, the SQL editor itself)
versus every "content" element (title, chart, filters).

```
                          Preview mode    Edit mode
─────────────────────────────────────────────────────
Panel title                  ✓                ✓
Chart / KPI / Table           ✓                ✓
FilterBar (if filters exist)  ✓                ✓
Execution metadata footer     ✗                ✓
Panel overflow menu [···]     ✗                ✓
SQL editor                    ✗                ✓ (Section 7)
Row/panel borders             subtle           visible
```

```css
/* Preview mode — rows have no visible chrome, panels float
   with just enough border to separate them visually */
.dashboard-grid:not(.edit-mode) .dashboard-row {
  border: none;
  background: transparent;
  padding: 0;
}

/* Edit mode — affordances become visible */
.dashboard-grid.edit-mode .dashboard-panel:hover .panel-overflow-menu {
  opacity: 1;
}
.dashboard-grid.edit-mode .dashboard-panel:hover .panel-footer {
  /* footer is always rendered in edit mode (Section 5.5);
     hover only affects the overflow menu's opacity, not the
     footer's existence */
}
```

---

## 7. The Minimal Override — When Inference Gets It Wrong

Per Section 3, manual layout controls are explicitly NOT the
primary interaction model. But DOC 1's Principle 2 also states
inference failures need *some* override — minimal and rare,
never the default path.

### 7.1 The Overflow Menu — Exactly Three Options

```
┌─────────────────┐
│ 📊 Change chart  │   → opens a dropdown of DOC 5's 8 V0.1
│                  │     chart types (Section 13.3); selecting
│                  │     one calls PATCH /panels/{id} with an
│                  │     explicit chart_type override, which
│                  │     sqlviz-api stores and uses to SKIP
│                  │     ChartEngine on subsequent re-renders
│                  │     of that panel (the override persists)
│ ✏️ Edit SQL       │   → opens the Monaco editor (Section 7.2)
│                  │     for this panel's query only
│ 🗑 Delete         │   → removes the panel; DashboardEngine
│                  │     re-composes the remaining panels
│                  │     (re-runs Section 15's row-packing,
│                  │     since removing a panel can change
│                  │     how the rest fit together)
└─────────────────┘
```

```
No layout/size/position options appear here — by design
(Section 3). If a chart override changes col_span needs
(e.g. switching KPI → Table needs more space), the
DashboardEngine recomputes layout automatically on save;
the user never manually sets a width or row.
```

### 7.2 The SQL Editor (Monaco)

```
Per DOC 3, Section 3: Monaco is the editor, chosen specifically
for handling CTEs, window functions, multi-line JOINs — the
real-world SQL complexity a lightweight editor (CodeMirror) was
rejected for in the V0.1 prototype.

Editor surface:
    - One Monaco instance per dashboard (DOC 2, Section 8 — "one
      SQL file per dashboard, queries separated by ;"), NOT one
      per panel. The "Edit SQL" overflow option (Section 7.1)
      scrolls/focuses the editor to that panel's specific
      statement rather than opening a separate per-panel editor.
    - Syntax highlighting: SQL, dialect-aware per DOC 2's
      connection model (DOC 2, Section "Engine roadmap" —
      DuckDB dialect in V0.1)
    - Theme: follows the global dark/light toggle (Section 2)
    - No autocomplete against live schema in V0.1 (logged as
      deferred in DOC 8, Section 6 features table — "schema
      autocomplete" is a V0.3 item, not V0.1)
```

---

## 8. Explainability UI — "Why This Chart?"

DOC 5's entire explainability apparatus (`score_trace`,
`explanation`, `confidence_gap`, `quality` — Section 1.4
Principle 5, and Sections 7.3/8.5 in detail) needs a UI surface,
or it exists only in API responses nobody sees. This is that
surface.

### 8.1 Trigger and Placement

```
A small "ⓘ" icon appears next to the panel title — but ONLY
when chart_quality is "medium" or "low" (DOC 5 Section
8.5/16.1), or when fallback_applied is true. A "high" quality,
high-confidence-gap inference shows NO indicator at all —
consistent with DOC 1 Principle 2 ("the user should rarely
need to think about this").
```

```svelte
<!-- PanelHeader.svelte, extended -->
{#if result.chart_quality !== 'high' || result.fallback_applied}
  <button class="explain-trigger" on:click={() => openExplainPanel(result)}>
    ⓘ
  </button>
{/if}
```

### 8.2 The Explain Panel Content

```
┌────────────────────────────────────────┐
│ Why a Line chart?                       │
│                                          │
│ Confidence: Medium                       │
│                                          │
│ Top signals:                             │
│   ✓ Temporal dimension detected   40%   │
│   ✓ Aggregation (SUM) detected    25%   │
│   ✓ GROUP BY present              20%   │
│                                          │
│ Other charts considered:                 │
│   Bar    — score 0.31                    │
│   Area   — score 0.28                    │
│                                          │
│ [📊 Use Bar instead]  [Keep Line]        │
└────────────────────────────────────────┘
```

```
Data sourced directly from InferenceResult, no client-side
computation:
    Confidence label  ← chart_quality (DOC 5 Section 8.5: maps
                         "high"/"medium"/"low" to a display label)
    Top signals        ← explanation[] (DOC 5 Section 7.4),
                         using contribution_pct once DOC 5's
                         V0.2 patch item lands (Section 16.3 —
                         until then, falls back to raw
                         contribution values, clearly NOT
                         percentages, per the same honesty
                         principle as DOC 4's "normalized_score
                         is not a true probability" stance)
    Other charts        ← chart_alternatives (DOC 5 Section 8.5)
    "Use X instead"     ← same override mechanism as Section 7.1
```

---

## 9. Filter Controls — Rendering DOC 5's 8 Control Types

DOC 5, Section 10.2 defines exactly 8 control types. This
section is their Svelte implementation — one component per
type, no client-side logic deciding WHICH type to use (that
decision already happened in FilterEngine).

```svelte
<!-- FilterBar.svelte -->
<script lang="ts">
  import type { FilterControl } from '$lib/types';
  import DatePicker from './filters/DatePicker.svelte';
  import DateRangePicker from './filters/DateRangePicker.svelte';
  import Dropdown from './filters/Dropdown.svelte';
  import MultiSelect from './filters/MultiSelect.svelte';
  import SearchInput from './filters/SearchInput.svelte';
  import NumericInput from './filters/NumericInput.svelte';
  import RangeSlider from './filters/RangeSlider.svelte';
  import Toggle from './filters/Toggle.svelte';

  export let controls: FilterControl[];  // DOC 5 Section 10.3 output

  const componentMap = {
    date_picker:       DatePicker,
    date_range_picker: DateRangePicker,
    dropdown:           Dropdown,
    multiselect:        MultiSelect,
    search:             SearchInput,
    numeric:            NumericInput,
    range_slider:       RangeSlider,
    toggle:             Toggle,
  };
</script>

<div class="filter-bar">
  {#each controls as control}
    <svelte:component
      this={componentMap[control.control_type]}
      variable={control.variable}
      label={control.label}
    />
  {/each}
</div>
```

```
FilterBar only renders when controls.length > 0 — there is no
"no filters" placeholder state; a dashboard with zero $variable
usage simply has no filter bar, taking zero vertical space
(consistent with DOC 1's "infer everything, show nothing the
user didn't ask for" philosophy).
```

---

## 10. Authentication Screens — Rendering DOC 7's Flows

### 10.1 Admin Login

```
┌──────────────────────┐
│       SQLviz          │
│                       │
│  Admin password        │
│  [____________]       │
│                       │
│  [    Sign in    ]    │
└──────────────────────┘
```

```
Maps directly to DOC 7, Section 3.2 login flow. The generic
error message requirement (DOC 7 Section 3.2 — "never reveal
whether the project even has a password set") means this screen
NEVER shows "incorrect password" vs "no account" as distinct
states — there is exactly one error string for any failure:
"Invalid password."
```

### 10.2 Viewer — Password-Protected Share

```
┌──────────────────────┐
│   Revenue Analysis     │
│   (password protected) │
│                        │
│  [____________]       │
│                        │
│  [     View      ]    │
└──────────────────────┘
```

```
This is the ONLY screen a viewer ever sees that isn't the
dashboard itself, and only for mode='password' shares (DOC 7,
Section 4.2). Private and public mode viewers go straight to
the dashboard with zero intermediate screen — consistent with
DOC 7 Section 4.2's exact flow description.
```

---

## 11. What Is Deferred — Cross-Referenced

Consistent with the discipline established in DOC 5 (Section
16.3-16.4), DOC 7 (Section 7), and DOC 8 (Section 6): nothing
discussed and set aside during this document's writing is
silently dropped.

```
Item                              Why deferred              Returns
─────────────────────────────────────────────────────────────────
Manual layout override            DOC 1 v0.2 vision           V0.2
 (drag, resize, custom rows)       explicitly removes manual
                                  layout as a PRIMARY flow;
                                  if real usage shows the
                                  Section 7.1 minimal override
                                  is insufficient for edge
                                  cases, a manual escape hatch
                                  beyond "change chart type"
                                  may be reconsidered then —
                                  not before.

Schema-aware SQL autocomplete      Logged in DOC 8 Section 6   V0.3
 in Monaco (Section 7.2)

contribution_pct in Explain         Depends on DOC 5 Section    V0.2
Panel (Section 8.2)                16.3 item landing first
                                  in sqlviz-inference — UI
                                  consumes whatever shape
                                  the API returns, cannot
                                  get ahead of it

Cross-filtering (click a bar         DOC 5 Section 15.7 +       V0.2
 to filter another panel)            DOC 8 Section 6 — this
                                    is a Dashboard Engine
                                    capability first, UI
                                    second; UI work waits
                                    for that API shape to exist

Insight/Narrative text in panels      DOC 5 Section 16.4         V0.3
 ("Revenue grew 12%")                 (Insight Engine,
                                     Narrative Engine) —
                                     no UI surface designed
                                     until the backend
                                     produces this data

Domain-specific theming               not previously discussed;   not
 (e.g. an "Energy" color               logged here only because    planned
 preset for utility dashboards)        DOC 5 Section 16.3's
                                     Domain Dictionaries raised
                                     the general "domain
                                     packs" idea — a themed
                                     visual counterpart is
                                     speculative and not
                                     committed to any version
```

---

## 12. V0.2 UI — Cognitive Dashboard Compiler Interface

**Version scope:** This section describes the V0.2 target UI.
All components below are additions. No V0.1 component is removed
or modified. V0.2 UI surfaces the outputs of DOC5 §18 — the new
backend engines — through specific, self-contained Svelte components.

**DOC6 §1.1 principle extended to V0.2:**
The frontend still never infers. It renders the richer inference
output from V0.2's ScoringModel, ReadabilityModel, ImportanceEngine,
and DashboardObjective. Score percentages, suggestions, narrative
roles — all arrive from the backend. The frontend only displays them.

---

### 12.1 Chart Selector Panel

#### 12.1.1 Anatomy

The Chart Selector Panel replaces the V0.1 overflow menu's "Change
chart" button with a full visual panel that shows the scoring model's
output (DOC5 §18.2) and lets the user apply an override (DOC5 §18.7).

```
┌──────────────────────────────────────────────────────┐
│  Chart type                                    [×]   │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ● Horizontal bar                           91%  ✓  │  ← winner (Auto)
│                                                      │
│  ○ Bar                                      73%     │
│  ○ Table                                    62%     │
│  ○ Pie                                       9%     │
│                                                      │
│  ┤ Why these scores? ├────────────────────────────── │
│  │ semantic_fit:        0.92 (ranking intent)        │
│  │ readability:         0.95 (12 categories)         │
│  │ perceptual_accuracy: 0.85 (length encoding)       │
│  │ cognitive_load:      0.18 (simple layout)         │
│                                                      │
│                    [Reset to auto]                   │
└──────────────────────────────────────────────────────┘
```

The `[×]` closes the panel without changing anything.
Clicking a radio button immediately applies the override and
triggers the animation described in §12.1.3.

#### 12.1.2 Score Display Rules

```
Auto label:
    The winner always shows its ABSOLUTE score percentage,
    not 100%. "91%" means the multicriterio score (DOC5 §18.2.4)
    was 0.91 / 1.00.

    This is intentional: a score below 100% signals that the
    chart is a good fit but not perfect — the user can investigate.

Alternative labels:
    Each alternative shows its percentage relative to the winner.
    "Bar [73%]" means bar scored 73% of what bar_horizontal scored.

    Alternatives scoring < 30% are hidden by default with a
    "Show all" toggle — they clutter the list without being useful.

Score color coding:
    ≥ 80%  → --sqlviz-positive (#22c55e)
    60-79% → --sqlviz-text    (#f1f5f9)
    40-59% → --sqlviz-neutral (#94a3b8)
    < 40%  → --sqlviz-negative (#ef4444)
```

#### 12.1.3 Chart Change Animation

When the user selects an alternative chart type:

```
1. Current chart fades out over 150ms (opacity: 1.0 → 0.0)
2. New chart initializes (ECharts or KPIRenderer or TableRenderer)
   behind the fade
3. New chart fades in over 200ms (opacity: 0.0 → 1.0)
4. Panel header label updates: "Auto: Bar [91%]" → "Manual: Line [63%]"

Total transition: 350ms
No layout shift — the panel_height_px is re-read from the new
chart's InferenceResult with the override applied and the panel
container resizes via CSS transition (height, 300ms, ease-out).

If the panel_height_px changes by more than 40px, the dashboard
grid reflowing is animated so surrounding panels don't jump.
```

#### 12.1.4 ChartSelectorPanel.svelte — Structure

```svelte
<!-- ChartSelectorPanel.svelte -->
<script lang="ts">
    import type { InferenceResult } from '$lib/types';

    let { result, onSelect, onClose }: {
        result: InferenceResult;
        onSelect: (chartType: string) => void;
        onClose: () => void;
    } = $props();

    // Score display: winner absolute pct, alternatives relative to winner.
    // All scores arrive from backend (DOC5 §18.2.4) — no computation here.
    const winner = $derived(result.chart_winner);
    const winnerPct = $derived(result.chart_scores?.[winner]?.pct ?? 0);

    const alternatives = $derived(
        (result.chart_alternatives ?? [])
            .filter(a => a.pct >= 30)   // hide very low-scoring alternatives
            .slice(0, 5)                // max 5 alternatives shown
    );

    let showBreakdown = $state(false);
    let selected = $state(result.chart_winner);  // tracks current selection
    const isOverridden = $derived(selected !== winner);

    function handleSelect(chartType: string) {
        selected = chartType;
        onSelect(chartType);
    }
</script>

<div class="chart-selector">
    <div class="selector-header">
        <span class="selector-title">Chart type</span>
        <button class="close-btn" onclick={onClose}>×</button>
    </div>

    <div class="candidates">
        <!-- Winner row -->
        <label class="candidate winner">
            <input type="radio" name="chart" value={winner}
                   checked={selected === winner}
                   onchange={() => handleSelect(winner)} />
            <span class="chart-name">{formatChartName(winner)}</span>
            <span class="score" class:score-high={winnerPct >= 80}>
                {winnerPct}%
            </span>
            {#if selected === winner}
                <span class="auto-badge">{isOverridden ? 'Manual' : 'Auto'}</span>
            {/if}
        </label>

        <!-- Alternative rows -->
        {#each alternatives as alt}
            <label class="candidate">
                <input type="radio" name="chart" value={alt.chart}
                       checked={selected === alt.chart}
                       onchange={() => handleSelect(alt.chart)} />
                <span class="chart-name">{formatChartName(alt.chart)}</span>
                <span class="score" class:score-low={alt.pct < 40}>
                    {alt.pct}%
                </span>
            </label>
        {/each}
    </div>

    <!-- Score breakdown (collapsed by default) -->
    <button class="breakdown-toggle" onclick={() => showBreakdown = !showBreakdown}>
        {showBreakdown ? '▲' : '▶'} Why these scores?
    </button>

    {#if showBreakdown}
        {@const breakdown = result.chart_scores?.[selected]?.breakdown}
        {#if breakdown}
            <dl class="breakdown">
                <dt>semantic_fit</dt>        <dd>{fmtScore(breakdown.semantic_fit)}</dd>
                <dt>readability</dt>         <dd>{fmtScore(breakdown.readability)}</dd>
                <dt>perceptual_accuracy</dt> <dd>{fmtScore(breakdown.perceptual_accuracy)}</dd>
                <dt>cognitive_load</dt>      <dd>{fmtScore(breakdown.cognitive_load)}</dd>
                <dt>task_fit</dt>            <dd>{fmtScore(breakdown.task_fit)}</dd>
            </dl>
        {/if}
    {/if}

    {#if isOverridden}
        <button class="reset-btn"
                onclick={() => handleSelect(winner)}>
            Reset to auto
        </button>
    {/if}
</div>
```

The `onSelect` callback propagates the override to the parent
component, which calls `POST /api/v1/panels/{id}/override` to
persist the choice and trigger a re-render of the panel with the
new chart type applied.

---

### 12.2 Layout Override Controls

#### 12.2.1 Anatomy

Layout Override Controls appear below the Chart Selector Panel
in the panel overflow menu (·  ·  · → Layout). They expose width
and height overrides (DOC5 §18.7.2) as simple button groups.

```
┌──────────────────────────────────────────────────────┐
│  Layout                                        [×]   │
├──────────────────────────────────────────────────────┤
│  Width                                               │
│  [Auto: 12col] [4col] [6col] [8col] [12col]          │
│                                                      │
│  Height                                              │
│  [Auto: 360px] [Compact] [Normal] [Grande]           │
│                                                      │
│  Note: some widths may be unavailable if they        │
│  violate the chart's minimum readable width.         │
│                                                      │
│                    [Reset to auto]                   │
└──────────────────────────────────────────────────────┘
```

#### 12.2.2 Width Controls

```
Available width buttons: 4, 6, 8, 12 columns.

Auto button:
    Shows current auto-computed col_span.
    "Auto: 12col" → the LayoutOptimizer chose 12.

Disabled buttons:
    Any width below the chart's min_width (from layout_preferences.yaml,
    DOC5 §18.5.2) is rendered disabled with a tooltip:
    "Line charts need at least 8 columns for readability"

    The user CAN override to a constrained width — the button is not
    hidden, just visually muted with a warning icon ⚠.
    If they do, a warning banner appears on the panel:
    "This chart may be cramped at 6 columns"
```

#### 12.2.3 Height Controls

```
Height buttons map to the three presets (DOC5 §18.7.2):
    Compact → preferred_height × 0.70
    Normal  → preferred_height        (default — this is "Auto")
    Grande  → preferred_height × 1.40 (clamped to max_height_px)

For dynamic-height charts (bar_horizontal, table):
    The presets scale the computed dynamic height, not a fixed number.
    "Compact" for a table with 10 rows (height=480px): 480 × 0.70 = 336px

Pixel values are shown in the button label:
    [Auto: 360px] [Compact 252px] [Normal 360px] [Grande 504px]
```

#### 12.2.4 LayoutOverrideControls.svelte — Structure

```svelte
<!-- LayoutOverrideControls.svelte -->
<script lang="ts">
    import type { InferenceResult } from '$lib/types';

    const WIDTHS = [4, 6, 8, 12];
    const HEIGHT_PRESETS = [
        { label: 'Compact', factor: 0.70 },
        { label: 'Normal',  factor: 1.00 },
        { label: 'Grande',  factor: 1.40 },
    ];

    let { result, onWidthChange, onHeightChange, onReset }: {
        result: InferenceResult;
        onWidthChange: (cols: number | null) => void;
        onHeightChange: (px: number | null) => void;
        onReset: () => void;
    } = $props();

    // Min width comes from backend (layout_constraints field — DOC5 §18.5)
    const minWidth = $derived(result.layout_constraints?.min_width ?? 3);
    const preferredHeight = $derived(result.panel_height_px);

    function heightForPreset(factor: number): number {
        const maxHeight = result.layout_constraints?.max_height_px ?? 720;
        return Math.min(maxHeight, Math.round(preferredHeight * factor));
    }
</script>

<div class="layout-controls">
    <div class="control-group">
        <span class="control-label">Width</span>
        <div class="btn-group">
            <button class="btn active" onclick={() => onWidthChange(null)}>
                Auto: {result.col_span}col
            </button>
            {#each WIDTHS as w}
                {@const tooNarrow = w < minWidth}
                <button
                    class="btn"
                    class:disabled={tooNarrow}
                    title={tooNarrow ? `Min width: ${minWidth} cols` : undefined}
                    onclick={() => onWidthChange(w)}
                >
                    {w}col {tooNarrow ? '⚠' : ''}
                </button>
            {/each}
        </div>
    </div>

    <div class="control-group">
        <span class="control-label">Height</span>
        <div class="btn-group">
            <button class="btn active" onclick={() => onHeightChange(null)}>
                Auto: {preferredHeight}px
            </button>
            {#each HEIGHT_PRESETS as preset}
                {@const px = heightForPreset(preset.factor)}
                <button class="btn" onclick={() => onHeightChange(px)}>
                    {preset.label} {px}px
                </button>
            {/each}
        </div>
    </div>

    <button class="reset-btn" onclick={onReset}>Reset to auto</button>
</div>
```

---

### 12.3 Dashboard Score Panel

#### 12.3.1 Anatomy

The Dashboard Score Panel is visible only in Edit mode. It renders
the output of the DashboardObjective function (DOC5 §18.6) for the
entire dashboard, surfacing the utility score and actionable suggestions.

```
┌──────────────────────────────────────────────────────┐
│  Dashboard Score                                      │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Utility Score    ████████████░░░░   78 / 100        │
│                                                      │
│  comprehension    ████████████████   0.90 ✓          │
│  narrative_order  ████████░░░░░░░░   0.62 ⚠          │
│  readability      ████████████░░░░   0.78 ✓          │
│  cognitive_load   ████████████████   0.12 ✓  (low=good)│
│  space_waste      ████████░░░░░░░░   0.31 ⚠  (low=good)│
│                                                      │
├──────────────────────────────────────────────────────┤
│  Sugerencias                                         │
│                                                      │
│  ⚠ Panel 3 — "Revenue by Category"                  │
│    Este pie tiene 12 categorías — considera          │
│    bar chart (+8% utility)                           │
│    [Apply] [Dismiss]                                 │
│                                                      │
│  ⚠ Panel 2 — "Monthly Trend"                        │
│    Este chart necesita más ancho (mín. 8 cols)       │
│    para ser legible                                  │
│    [Apply 12col] [Dismiss]                           │
│                                                      │
└──────────────────────────────────────────────────────┘
```

The score bar uses --sqlviz-primary (#6366f1) fill on a
--sqlviz-border (#334155) track. No external library required.

#### 12.3.2 Utility Score Thresholds

```
Utility score display:
    ≥ 85  → "Excellent"  (--sqlviz-positive)
    70-84 → "Good"       (--sqlviz-primary)
    55-69 → "Fair"       (--sqlviz-neutral)
    < 55  → "Needs work" (--sqlviz-negative)

Suggestion display:
    [Apply]   → immediately applies the suggestion (calls the same
                 override API as the Chart Selector Panel §12.1)
    [Dismiss] → hides the suggestion for this session only.
                 It reappears if the dashboard is re-executed.

Suggestions are sorted by score_impact descending —
the highest-value improvements are shown first.
```

#### 12.3.3 DashboardScorePanel.svelte — Structure

```svelte
<!-- DashboardScorePanel.svelte -->
<script lang="ts">
    import type { DashboardLayout } from '$lib/types';

    let { layout, onApplySuggestion }: {
        layout: DashboardLayout;
        onApplySuggestion: (panelId: string, action: Record<string, unknown>) => void;
    } = $props();

    // utility_score and suggestions live on DashboardLayout (DOC5 §18.6.2)
    // They are NOT per-panel fields — they describe the whole dashboard.
    const utilityScore = $derived(layout.utility_score ?? 0);
    const utilityPct = $derived(Math.round(utilityScore * 100));
    const suggestions = $derived(
        (layout.suggestions ?? []).sort((a, b) => b.score_impact - a.score_impact)
    );
    const breakdown = $derived(layout.utility_breakdown ?? {});

    const label = $derived(
        utilityPct >= 85 ? 'Excellent' :
        utilityPct >= 70 ? 'Good' :
        utilityPct >= 55 ? 'Fair' : 'Needs work'
    );
</script>

<div class="score-panel">
    <h3 class="score-heading">Dashboard Score</h3>

    <div class="utility-score">
        <div class="score-bar">
            <div class="score-fill" style="width: {utilityPct}%"></div>
        </div>
        <span class="score-value">{utilityPct} / 100</span>
        <span class="score-label">{label}</span>
    </div>

    <dl class="breakdown">
        {#each Object.entries(breakdown) as [key, value]}
            <dt>{key}</dt>
            <dd>
                <div class="mini-bar">
                    <div class="mini-fill" style="width: {Math.round(Number(value) * 100)}%">
                    </div>
                </div>
                {Number(value).toFixed(2)}
            </dd>
        {/each}
    </dl>

    {#if suggestions.length > 0}
        <div class="suggestions">
            <h4>Sugerencias</h4>
            {#each suggestions as s}
                <div class="suggestion">
                    <div class="suggestion-text">
                        <span class="suggestion-icon">⚠</span>
                        <strong>{s.panel_label ?? s.panel_id}</strong> —
                        {s.suggestion}
                        <span class="impact">(+{Math.round(s.score_impact * 100)}% utility)</span>
                    </div>
                    <div class="suggestion-actions">
                        <button onclick={() => onApplySuggestion(s.panel_id, s.action)}>
                            Apply
                        </button>
                        <!-- Dismiss is session-only; no API call needed -->
                    </div>
                </div>
            {/each}
        </div>
    {/if}
</div>
```

---

### 12.4 Learning Feedback UI

#### 12.4.1 Learning Notification

When the Feedback Engine (DOC5 §18.8) writes a new weight
calibration entry to `brain.duckdb`, the next page load (or
next execution) surfaces a brief notification:

```
┌──────────────────────────────────────────────────────┐
│  💡 SQLviz aprendió algo                    [×]      │
│                                                      │
│  "bar se prefiere sobre pie para datos de            │
│   composición" — basado en 8 correcciones tuyas.     │
│                                                      │
│  [Ver preferencias]                                  │
└──────────────────────────────────────────────────────┘
```

This notification:
- Appears at most once per new calibration event
- Is dismissable with [×] and stays dismissed for 24h in localStorage
- The [Ver preferencias] button opens the Settings > Preferences panel (§12.4.2)
- Never appears in Preview mode — only in Edit mode
- Uses --sqlviz-bg-surface background with --sqlviz-primary left border (4px)

#### 12.4.2 Preferences Panel (Settings)

The Preferences Panel is accessible from the app bar settings icon
in Edit mode. It shows everything the FeedbackEngine has learned:

```
┌──────────────────────────────────────────────────────┐
│  Preferencias aprendidas                              │
├──────────────────────────────────────────────────────┤
│  Lo que SQLviz recordó sobre tus preferencias         │
│                                                      │
│  Chart preferences                                   │
│  ─────────────────────────────────────────────────   │
│  bar_horizontal > bar   [composición]   8 muestras   │
│  bar > pie              [composición]   8 muestras   │
│  line > bar             [tendencia]     5 muestras   │
│                                                 [↩]  │
│                                                      │
│  Layout preferences                                  │
│  ─────────────────────────────────────────────────   │
│  bar: 12col > 6col                      5 muestras   │
│                                                 [↩]  │
│                                                      │
│  [Borrar todas las preferencias]                      │
└──────────────────────────────────────────────────────┘
```

Each preference row has a [↩] revert button that calls
`DELETE /api/v1/brain/calibration/{weight_key}` to remove
the specific calibration entry and restore the YAML baseline.

"Borrar todas las preferencias" resets all weight_calibration
entries to the YAML baselines — the system reverts to Day 1 defaults.

#### 12.4.3 FeedbackNotification.svelte — Structure

```svelte
<!-- FeedbackNotification.svelte -->
<script lang="ts">
    import { editMode } from '$lib/stores/editMode';

    let { calibrationEvents }: {
        calibrationEvents: Array<{ trigger_pattern: string; sample_count: number }>;
    } = $props();

    // Only show in edit mode; last event is the newest calibration.
    const latestEvent = $derived(calibrationEvents.at(-1));

    const DISMISS_KEY = 'sqlviz_feedback_dismissed';

    // Dismiss for 24h using localStorage — pure client storage, no API.
    let dismissed = $state(isDismissed());

    function isDismissed(): boolean {
        const ts = localStorage.getItem(DISMISS_KEY);
        if (!ts) return false;
        return Date.now() - Number(ts) < 24 * 60 * 60 * 1000;
    }

    function dismiss() {
        localStorage.setItem(DISMISS_KEY, String(Date.now()));
        dismissed = true;
    }
</script>

{#if $editMode && latestEvent && !dismissed}
    <div class="feedback-notification">
        <span class="icon">💡</span>
        <div class="message">
            <strong>SQLviz aprendió algo</strong>
            <p>"{latestEvent.trigger_pattern}" —
               basado en {latestEvent.sample_count} correcciones tuyas.</p>
        </div>
        <button class="link-btn">Ver preferencias</button>
        <button class="close-btn" onclick={dismiss}>×</button>
    </div>
{/if}

<style>
    .feedback-notification {
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        padding: 0.875rem 1rem;
        background: var(--sqlviz-bg-surface);
        border-left: 4px solid var(--sqlviz-primary);
        border-radius: var(--sqlviz-radius);
        border: 1px solid var(--sqlviz-border);
        margin: 0.5rem var(--sqlviz-gap);
    }
</style>
```

#### 12.4.4 API Endpoints for Feedback UI

New endpoints required (Phase 7 implementation):

```
GET  /api/v1/brain/calibrations
     Returns: list of weight_calibration rows (sorted by calibrated_at DESC)
     Used by: Preferences Panel (§12.4.2)

DELETE /api/v1/brain/calibration/{weight_key}
     Effect: removes the calibration row; restores YAML baseline
     Used by: [↩] revert button in Preferences Panel

DELETE /api/v1/brain/calibrations
     Effect: removes ALL calibration rows; full reset
     Used by: "Borrar todas las preferencias"

GET  /api/v1/brain/recent-calibration
     Returns: the latest weight_calibration row or null
     Used by: FeedbackNotification (polling every 30s in Edit mode,
              or triggered after each panel execution)
```

---

### 12.5 V0.2 UI Integration Points with Existing V0.1 Components

All V0.2 UI components integrate with V0.1 without replacing
any existing component. The integration points are:

```
V0.1 PanelOverflow.svelte (§7.1)
    Current: [Change chart] [Edit SQL] [Delete]
    V0.2:    [Chart: Auto [91%] ▼] [Layout ▼] [Edit SQL] [Explain] [Delete]
    Change:  First item opens ChartSelectorPanel (§12.1) as a popover.
             Second item opens LayoutOverrideControls (§12.2) as a popover.

V0.1 PanelHeader.svelte (§5.2)
    Current: title only
    V0.2:    title + narrative_role badge (subtle, edit mode only)
    Change:  Add <span class="role-badge">{result.narrative_role}</span>
             visible only when editMode=true and narrative_role != 'primary_story'
             (primary_story is the default, no need to label it)

V0.1 DashboardGrid.svelte (§4.1)
    Current: renders panels with panel_height_px from LayoutEngine
    V0.2:    same, but panel_height_px may come from LayoutOptimizer override
    Change:  none — DashboardGrid already reads panel_height_px from
             inference_result; LayoutOptimizer writes the same field.

V0.1 +page.svelte — app bar area
    Current: Preview/Edit toggle + Run button + SQL editor
    V0.2:    adds Dashboard Score indicator to app bar (edit mode only):
             [Score: 78 ▲] button that opens DashboardScorePanel (§12.3)
             as a right-side slide-in panel.

    The slide-in panel is outside the dashboard grid and does not
    affect panel layout.
```

---

*Section 12 complete. V0.2 UI — Cognitive Dashboard Compiler Interface.*
*All V0.1 components are unchanged. V0.2 adds only new components.*
*Implementation scope: Phase 7.*

---

## 13. Definition of Done — UI Design System (feeds DOC 8, Phase 5)

```
[ ] Design tokens (Section 2) implemented as CSS variables,
    dark theme default, light theme via [data-theme="light"]
[ ] DashboardGrid renders DashboardLayout (DOC 5 Section 15.4)
    with zero client-side layout decisions — col_span/row_span
    consumed directly
[ ] Panel anatomy (Section 5) — KPI, Table, and ECharts-backed
    panels all render through PanelRenderer's single dispatch
[ ] KPI trend arrow reads result.trend_direction_label only —
    no feature_vector indexing, no thresholds in Svelte
    (Section 5.4, corrected per DOC 5 Section 16.6); confirm
    the component contains zero references to
    result.feature_vector anywhere
[ ] Preview mode hides footer, overflow menu, and SQL editor;
    edit mode shows all three (Section 6)
[ ] Overflow menu offers exactly three options — chart change,
    edit SQL, delete — no layout/size controls (Section 7.1)
[ ] One Monaco instance per dashboard, not per panel (Section 7.2)
[ ] Explain panel (Section 8) appears ONLY when quality != high
    or fallback_applied — never on high-confidence panels
[ ] All 8 filter control types (Section 9) render from
    FilterControl.control_type with no client-side type logic
[ ] Admin login and password-protected viewer screens (Section
    10) match DOC 7's exact flows, including the generic
    error-message requirement
[ ] Section 11's deferred list reviewed and accurate before
    V0.1 ships
```

---

*SQLviz UI Design System — v0.1.0 Draft*
*"The frontend never infers. The frontend only renders."*
