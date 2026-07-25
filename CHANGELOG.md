# Changelog

All notable changes to SQLviz are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [v0.2.11] — 2026-07-25

Objetivo: compartir dashboards en la red local de forma confiable, motor de
charts profesional y controles de filtro consistentes.

### Added
- **Motor de charts profesional** con paletas a nivel dashboard, y nuevas
  paletas seleccionables desde el Panel Properties.
- **Títulos de panel y de ejes editables**, persistidos y visibles también en
  los dashboards compartidos.
- **Selector de paleta en los viewers**: cada visitante elige su paleta, que se
  guarda por dashboard en su navegador.
- **Compartir con alcance**: `dashboard` (uno solo) o `workspace` (todos, con
  navegación), cada uno con su viewer.
- **Modo privado** = preview solo para el admin, links listos para LAN y
  generador de contraseñas fuertes (16 caracteres, sin caracteres ambiguos),
  con botón para copiarla.
- **El CLI escucha en `0.0.0.0`** por defecto, para que `sqlviz` a secas alcance
  para compartir en la red local.
- **Command palette**, sidebar tipo rail, focus mode y editor drawer.
- **Vistas de filtro guardadas** (combinaciones con nombre, en localStorage por
  dashboard), disponibles también en el viewer.
- **El dropdown de filtros ahora es un combobox con búsqueda**, igual que el
  multiselect: dominios de docenas de valores se buscan en vez de scrollearse.
- **Identidad visual**: logo oficial de SQLviz, Geist Sans para el wordmark y
  color de marca indigo `#5B5BD6`.
- `$lib/clipboard.ts`: helper de copiado con fallback para contexto inseguro.
- Polyfills de jsdom para Pointer Capture y `PointerEvent` en `vitest-setup.ts`,
  sin los cuales ningún test podía abrir un menú de bits-ui.

### Changed
- **Viewer rediseñado**: sidebar colapsable, filtros flotantes y la misma barra
  de filtros que el modo edición.
- Share pasa a botón icon-only, Preview/Edit a control segmentado y los filtros
  a pills.
- Scrollbars finas y sensibles al tema.

### Fixed
- **Copiar el link de share copiaba otra cosa**: sin contexto seguro se caía a
  `execCommand`, que seleccionaba un `<textarea>` colgado de `<body>` — fuera
  del focus trap del diálogo de bits-ui, que le robaba el foco antes de copiar.
  La selección ahora ocurre siempre dentro del diálogo.
- **Las vistas de filtro no se podían guardar desde la red local**:
  `crypto.randomUUID()` solo existe en contexto seguro, así que tiraba
  `TypeError` en `http://<LAN-IP>`. Ahora el id sale de `crypto.getRandomValues`.
- **El dropdown con muchas opciones se salía de la pantalla sin scroll**: tenía
  `overflow-y-auto` pero nada que acotara su altura, y una caja libre de crecer
  nunca produce scrollbar.
- El viewer no cargaba: se separó la navegación del fetch de datos, se sirve la
  SPA para `/view/<token>` y se dejó de devolver HTML cacheado a su fetch JSON.
- Los dominios de filtro no se cargaban en el viewer, así que los dropdowns se
  renderizaban como cajas de texto.
- Las posiciones de los paneles se mantienen estables al cambiar un filtro.
- Windows: se usa el event loop Selector para evitar el ruido de resets del
  Proactor.
- El título del eje Y se renderiza vertical (rotado 90°), también en edición.
- Propiedades de panel obsoletas al cambiar de panel.

---

## [v0.2.10] — 2026-07-21

> Entrada reconstruida el 2026-07-25 a partir del historial: esta release se
> tagueó sin registrarse en el changelog.

### Added
- **Creación inline estilo VSCode** en el sidebar: nombrar carpetas y
  dashboards directamente en el árbol, sin modal (Enter confirma, Escape
  cancela, nombre vacío muestra un aviso inline).
- **Selección explícita de carpeta/raíz** como destino de creación, visualmente
  distinta del dashboard activo (línea fina a la izquierda vs. resaltado).
- **Caché de resultados en memoria** por dashboard (charts, layout, dominios y
  selección de filtros): navegar entre dashboards restaura la vista al instante
  en vez de mostrar el editor vacío. Se invalida en cuanto el SQL borrador
  diverge de la query que produjo esos resultados.

### Changed
- El estado de los filtros paramétricos migró a runes de Svelte 5: el cambio de
  un filtro pasó a ser una escritura de estado pura, con un `$effect` que
  debouncea (350 ms) y re-ejecuta solo los paneles afectados.
- El botón "Run Again" se eliminó y "Last run X ago" quedó como línea
  informativa.
- El botón de limpiar del dropdown reemplaza a la opción "All".

### Fixed
- Limpiar un filtro no re-ejecutaba la query: la ejecución abortaba si alguna
  variable estaba vacía, así que el chart seguía mostrando los datos filtrados.
  Un valor vacío significa "All" y el API neutraliza ese predicado.
- La paleta elegida no se aplicaba a line/bar/scatter/histogram: solo el pie
  usaba la paleta, el resto tenía el color de serie hardcodeado.
- Cursor DuckDB por request, para que los resultados no se pisen entre threads.
- Migraciones idempotentes: se acabó el traceback al reabrir un proyecto.

---

## [v0.2.9] — 2026-07-18

> Entrada reconstruida el 2026-07-25 a partir del historial: esta release se
> tagueó sin registrarse en el changelog.

### Added
- **Panel de Propiedades del panel** (`PanelPropertiesPanel.svelte`): panel
  lateral derecho que se abre al hacer clic en cualquier panel en modo edición y
  centraliza toda su configuración — tipo de chart (el Chart Selector ahora
  embebido), título editable, ejes X/Y, colores, dimensiones (ancho en columnas
  y alto en px, con reset a automático), SQL editable con Apply que re-ejecuta
  solo ese panel, e inferencia (intent/chart/calidad + explicación del motor).
  Reemplaza el modal flotante del Chart Selector y el popover de layout.
- **Roadmap completo** (`sqlviz-roadmap.md`): V0.2.x → V1.0 con convención de
  versiones, y **DOC11**, el plan de construcción del Filter Engine de V0.4.0
  (20 motores). Solo documentación.

---

## [v0.2.8] — 2026-07-18

> Entrada reconstruida el 2026-07-25 a partir del historial: esta release se
> tagueó sin registrarse en el changelog.

### Added
- **Auto-guardado del borrador**: el texto exacto del editor se persiste solo,
  2 s después de dejar de tipear, al cambiar de dashboard, al perder foco la
  ventana y al cerrar la pestaña (PATCH con `keepalive`). El usuario nunca
  piensa en guardar.
- **Indicadores de estado en el header**, discretos y nunca modales:
  ● Draft · Saving… · Saved (se desvanece) · Running · Error.
- **Restore al refrescar**: reabre el último dashboard activo, restaura el
  borrador exacto y, en vez de re-ejecutar, muestra "Last run X min ago".
- **Botón "Restore last run"**: revierte el borrador al SQL de la última
  ejecución exitosa, que ahora se persiste aparte en `dashboards.last_run_sql`
  (migración 0018). Solo aparece mientras borrador y última ejecución difieren.
- **Sidebar de dashboards colapsable y dual-mode**, con drag-and-drop, borrado
  de grupos y edición inline.

---

## [v0.2.7] — 2026-07-18

> Entrada reconstruida el 2026-07-25 a partir del historial: esta release se
> tagueó sin registrarse en el changelog.

### Added
- **Dashboard Explorer**: sidebar de navegación entre dashboards.

---

## [v0.2.6] — 2026-07-18

Objetivo: filtros paramétricos completos y controles de UI profesionales
(ver `docs/architecture/sqlviz-roadmap-v02x.md`).

### Added
- **Los 8 tipos de filtro paramétrico** funcionando end-to-end en la FilterBar:
  `dropdown`, `multiselect`, `date_picker`, `date_range_picker`, `numeric`,
  `range_slider`, `search`, `toggle`.
- **Controles ricos por dominio de columna**: nuevo endpoint
  `POST /api/v1/panels/{id}/filter-domain` (body `{column, kind}`) que devuelve
  los valores distintos (dropdown/multiselect) o el `MIN`/`MAX` (slider) de la
  columna. El dominio se calcula reescribiendo el SQL del panel con sqlglot
  (se quita el `WHERE` paramétrico y se proyecta la columna), en
  `sqlviz_inference.filters.domain.build_domain_query`.
- **Migración a shadcn-svelte** de todos los controles de filtro: Select,
  Combobox (Popover + Command), Calendar/RangeCalendar, Slider, Switch, Input.
  Nuevas dependencias: `bits-ui`, `clsx`, `tailwind-merge`, `tailwind-variants`,
  `@internationalized/date`, `@lucide/svelte`, `tw-animate-css`.
- **Tema dark/light**: los tokens de shadcn (`--background`, `--primary`,
  `--border`, `--ring`, `--radius`, …) se aliasean sobre los design tokens de
  DOC6 (`--sqlviz-*`) mediante una capa `@theme inline` en `app.css`; la
  variante `dark:` se remapea al esquema dark-por-defecto de SQLviz. Una sola
  definición maneja ambos temas.
- Tests: builder de dominio (inference), endpoint `filter-domain` (API),
  cobertura end-to-end de los 8 tipos, y tests de componente de FilterControl.

### Changed
- `FilterEngine._find_associated_column`: reconoce `col IN ($var)` (multiselect)
  y `col BETWEEN $a AND $b` (rangos de fecha/numéricos) — antes ninguno producía
  un `filter_control`.
- Dedup de `$variables` con `dict.fromkeys()` en vez de `set()`: preserva el
  orden de aparición para que el par de un rango (`desde`/`hasta`, `min`/`max`)
  no se invierta según el hash-seed del proceso.
- `execute_panel`: en el flujo sin valores prueba la query con cada `$variable`
  ligada a `NULL` para recuperar el schema real de columnas antes de correr
  `FilterEngine` (numéricos/fechas ya no caen a texto plano).

### Fixed
- `col IN ($var)` con valor de tipo lista fallaba en DuckDB (`Conversion Error`);
  `execute_panel` reescribe a `IN $var` cuando el valor ligado es una lista.
- Switch (toggle): track/thumb invisibles — las clases usaban `data-checked:` /
  `data-unchecked:` pero bits-ui 2.18 emite `data-state="checked|unchecked"`.
  Reapuntadas a `data-[state=…]`.
- Slider de rango: la barra y el rango resaltado no se veían — usaban
  `data-horizontal:` / `data-vertical:` pero bits-ui emite
  `data-orientation="…"`. Reapuntadas a `data-[orientation=…]`.
- Popover/Select/Dialog: animaciones de apertura/cierre no disparaban
  (`data-open:` / `data-closed:` → `data-[state=open]:` / `data-[state=closed]:`)
  y `tw-animate-css` no estaba cableado.

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
