# Changelog

All notable changes to SQLviz are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [v0.2.5] — 2026-07-18

### Added
- **`sqlviz_api.routers.api.ts`**: cliente HTTP centralizado en el frontend
  para las llamadas a `/api/v1/*`, reemplazando `fetch()` dispersos por la app.
- **Stores dedicados** (`dashboardStore.svelte.ts`, `executionStore.svelte.ts`,
  `uiStore.svelte.ts`): extraen el estado y la lógica de orquestación que vivía
  en `+page.svelte` (bootstrap de dashboard, ejecución de paneles, filtros,
  overrides de layout, estado de UI) a stores de Svelte 5 (`$state`) testeables
  de forma aislada.
- **Componentes nuevos**: `AppBar.svelte`, `DashboardArea.svelte`,
  `EditorSection.svelte`, `ToastHost.svelte`, `VerticalResizer.svelte`
  (panel de editor SQL redimensionable), y `explain/*`
  (`ChartSection`, `DiagnosticsSection`, `IntentSection`, `QualitySection`,
  `ScoreBars`, `explainMeta.ts`) extraídos de `ExplainPanel.svelte`.
  `shared/ExecutionStateBadge.svelte` y `shared/StateMessage.svelte` para
  estados de carga/error reutilizados entre componentes.
- **Infraestructura de testing frontend**: `vitest-setup.ts` + primeros tests
  (`routes/page.test.ts`, `routes/login/page.test.ts`,
  `routes/view/[token]/page.test.ts`).
- **CI**: nuevo job `frontend` en `.github/workflows/ci.yml`
  (`svelte-check` + `vitest` + `vite build`), corriendo junto al job de
  backend existente.
- **Filtros paramétricos**: soporte para `col IN ($var)` (multiselect) y
  `col BETWEEN $a AND $b` (date_range_picker / range_slider) en
  `FilterEngine._find_associated_column` — antes ninguno de los dos producía
  un `filter_control`, así que la FilterBar no mostraba ningún control para
  esos patrones de SQL.

### Changed
- `+page.svelte` reducido de ~985 a un fragmento delgado que compone los
  nuevos componentes/stores; `ExplainPanel.svelte` reducido de forma análoga
  al extraer sus secciones a `explain/*`.
- `execute_panel` (`panels.py`): en el flujo sin valores (fallback), la
  query ahora se prueba con cada `$variable` ligada a `NULL` para recuperar
  el schema real de columnas antes de correr `FilterEngine` — sin esto,
  columnas numéricas/fecha se mostraban como controles de texto plano en
  vez de `numeric`/`date_picker`.
- El dedup de `$variables` en `FilterEngine` pasó de `set()` a
  `dict.fromkeys()`: preserva el orden de aparición en el SQL, evitando que
  el hash-seed del proceso invirtiera aleatoriamente qué caja de un rango
  (`desde`/`hasta`, `min`/`max`) queda ligada a cada variable.

### Fixed
- `col IN ($var)` con un valor de tipo lista fallaba en DuckDB con
  `Conversion Error` (los paréntesis hacen que DuckDB trate el parámetro
  como escalar, no como array). `execute_panel` ahora reescribe a
  `IN $var` cuando el valor ligado es una lista.

---

## [v0.2.4] — 2026-07-16

### Added
- **Versioning de contratos**: `InferenceResult` expone `result_schema_version`
  (constante `INFERENCE_RESULT_SCHEMA_VERSION = "1"`). `VisualSpec` expone
  `schema_version` (constante `VISUAL_SPEC_SCHEMA_VERSION = "1"`). El schema
  `.sqlviz` expone `schema_version = "1"` en la tabla `_sqlviz_meta`. Los
  consumidores pueden detectar cambios breaking comparando estas versiones.
- **`APP_VERSION` y `SCHEMA_VERSION`** exportadas públicamente desde
  `sqlviz_storage.project_db` para que los tests y la API puedan referenciarlas
  sin hardcodear strings.
- **Golden tests de serialización** (`test_serialization_golden.py`): freezan
  el conjunto de campos de `InferenceResult` y `VisualSpec`. Fallan cuando
  cualquier campo es agregado, eliminado o renombrado, forzando actualización
  intencional del fixture en `tests/golden/`.
- **Política formal de contratos** (`docs/architecture/sqlviz-contract-policy.md`):
  define `backward-compatible` / `breaking` / `deprecated`, lista los contratos
  versionados, y documenta el proceso para cambios breaking.
- **Migración 0015** (`meta_set_schema_version`): backfill de `schema_version`
  en proyectos `.sqlviz` creados antes de v0.2.4.

### Changed
- `_APP_VERSION` en `project_db.py` actualizado de `"0.1.0"` a `"0.2.4"`.
- Directorio `packages/sqlviz-inference/rules/` eliminado. Era una copia stale
  de `src/sqlviz_inference/rules/` (el `YAMLLoader` ya cargaba desde `src/`).
  La fuente de verdad única es `src/sqlviz_inference/rules/`.

### Fixed
- `sqlviz_logging.py`: anotación `dict` sin argumentos de tipo → `dict[str, object]`.
- `server.py`: comentario `# type: ignore[import-not-found]` redundante eliminado
  (mypy con `--ignore-missing-imports` suprime el error nativamente).
- `result.py`: comentario `# type: ignore[arg-type]` redundante eliminado.

Suite de tests: **1325 passed, 3 skipped** (antes: 1319).

---

## [v0.2.3] — 2026-07-16

### Added
- **Structured JSON logging** (`sqlviz_logging.py`): cada módulo del pipeline
  emite líneas JSON con `ts`, `level`, `logger`, `msg` y campos opcionales
  (`trace_id`, `elapsed_ms`, `execution_state`, `error_count`). Nivel
  configurable vía variable de entorno `SQLVIZ_LOG_LEVEL` (default: `WARNING`).
- **`trace_id`** por ejecución: identificador hex de 8 caracteres generado en
  `RuntimeContext`, propagado a través de todo el pipeline y expuesto en
  `InferenceResult`. Permite correlacionar logs de una misma inferencia.
- **`execution_state`** en `InferenceResult`: `"success"` / `"warning"` /
  `"degraded"` / `"failed"`, calculado por `pipeline.py` a partir de
  `context.errors` y `context.fallback_applied`.
- **Timings por módulo** (`module_timings`): cuando se pasa `?debug=1` al
  endpoint de ejecución, `InferenceResult` incluye un dict con el tiempo en ms
  de cada uno de los 21 pasos del pipeline.
- **Panel de Diagnósticos en ExplainPanel**: muestra estado de ejecución con
  badge de color, trace ID, tiempo total, fingerprint, versión del motor y
  grilla de timings por módulo (visible solo en modo debug).
- **14 nuevos tests** de observabilidad (`test_observability.py`) — suite total:
  1319 passed, 3 skipped.

### Fixed
- Todos los bloques `except Exception: pass` (17 módulos de inferencia)
  reemplazados por `_log.warning(...)` con `trace_id` en `extra`. Los errores
  silenciosos ahora son observables sin cambiar el comportamiento del pipeline.

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
