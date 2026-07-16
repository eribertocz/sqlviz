# Changelog

All notable changes to SQLviz are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [v0.2.2] — 2026-07-15

### Fixed
- **FeedbackEngine** ya no reemplaza silenciosamente la inferencia original.
  `run_apply` es ahora un no-op; la preferencia aprendida se expone en
  `feedback_preferred_chart` pero nunca se aplica automáticamente.
- **Chart Selector orden fijo**: la lista de alternativas ya no se reordena al
  seleccionar un ítem. `engineWinner` (antes del override) ancla el orden; solo
  cambia el radio button seleccionado.
- **Item duplicado**: `ScoringModel._update_winner()` podía mover el winner a
  una posición que ya estaba en `chart_alternatives`. Corregido filtrando
  `a.chart !== engineWinner` en la construcción de la lista.
- **Item seleccionado se movía al primer lugar**: causa raíz era `Math.random()`
  como row key en `DashboardGrid`, que provocaba remount del panel y reset del
  estado local. Corregido exponiendo `chart_engine_winner` en `InferenceResult`
  e inicializando `_override` desde `result.chart_winner !== engineWinner`.
- **Chart Selector recortado por el contenedor del panel**: convertido a modal
  flotante con `position: fixed` via acción Svelte `portal` que monta el nodo
  directamente en `document.body`, escapando cualquier `overflow: hidden`.

### Added
- **Preferencia ★ en Chart Selector**: cuando `feedback_preferred_chart` coincide
  con un ítem de la lista, se muestra una estrella dorada (★) junto al nombre.
  La preferencia es una sugerencia visual, nunca se aplica automáticamente.
- **Chart Selector muestra los 8 tipos siempre**, organizados en dos grupos:
  - **Recomendados** (score ≥ 50 %): charts que el motor considera adecuados.
  - **Disponibles** (score < 50 %): el resto, accesibles pero no recomendados.
  `ScoringModel` ahora expone `total_score` en `ChartCandidateV2`; el pipeline
  reconstruye `chart_alternatives` con los 8 tipos y un campo `pct` normalizado
  (winner = 1.0) después del scoring.

---

## [v0.2.1] — 2026-07-14

### Changed
- All packages unified at version `0.2.1`

### Fixed
- 38 ruff errors (import sorting, unused imports, line length) across test files
- New Dashboard button now clears previous query on navigation
- New Dashboard state no longer carries SQL from prior dashboard

### Added
- `GET /api/v1/meta` endpoint — returns version, build hash, feature flags
- `README.md` with installation and usage instructions
- `CHANGELOG.md` (this file)

---

## [v0.2.0] — 2026-07-13

### Added — Cognitive Dashboard Compiler (DOC6 §12)

**Inference pipeline (V0.2):**
- `DataProfile` + `VisualSpec` contracts (Fase 0)
- 11 typed contracts in `sqlviz_inference.contracts` (Fase A)
- `ColumnRoleDetector` + `ConstraintEngine` with 6 hard rules (Fase B)
- `ReadabilityModel` + `ScoringModel` (Fase C)
- `LayoutDeclarationBuilder` + `DashboardRoleClassifier` + `DashboardLayoutOptimizer`
  + `DashboardObjective` + `InformationGainEngine` (Fase D)
- `OverrideSystem` + `FeedbackEngine` — learned chart preferences (Fase E)
- `ExplanationEngine` V2 (Fase F)
- Benchmark suite: 52/52 gold (100%), 48/52 adversarial (92.3%) (Fase G)

**API:**
- `PATCH /api/v1/panels/{id}/override` — apply user chart/layout override
- `PanelOverrideRequest` model

**Storage:**
- `brain_db.py` — feedback patterns, layout patterns, feedback events
- `override_system.py` — `store_inference()` + `apply_override()`
- Migrations 0002–0014 (fingerprint, override columns, dashboard classification)
- `dashboard_hint` + `dashboard_domain` on dashboards table
- `inferred_intent_type` on panels table

**Frontend:**
- `ChartSelectorPanel.svelte` — chart alternatives with scores, "Reset to auto"
- `DashboardSidebar.svelte` — dashboard-level navigation with inferred icons
- `LayoutOverrideControls.svelte` — column span + height overrides
- `DashboardScorePanel.svelte` — utility score + breakdown + suggestions
- `DashboardGrid.svelte` — panel IDs, override props
- `PanelRenderer.svelte` — 150ms fade-out / 200ms fade-in animation on chart change
- `dashboardIcons.ts` — `resolveDashboardIcon()` with 4-level fallback
- Dashboard management UI: create dashboard, navigate between dashboards,
  active dashboard name in app bar
- `lucide-svelte@1.0.1` installed

---

## [v0.1.0] — 2026-06-01 (approx.)

### Added — V0.1 Foundation

- Core inference pipeline: intent detection → chart selection
- DuckDB-backed storage for dashboards, panels, SQL content
- FastAPI REST API: dashboards + panels CRUD, panel execution
- SvelteKit frontend: SQL editor, panel grid, ECharts rendering
- `sqlviz-cli` package
- 523 passing tests across all packages
