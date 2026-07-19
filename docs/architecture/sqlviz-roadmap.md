# SQLviz Roadmap — V0.2.x → V1.0

Roadmap completo de SQLviz usando **semver**. Cada versión es independiente y
shippeable.

## Convención de versiones

- **Patch** (`vX.Y.Z`) — correcciones y mejoras acotadas sobre una minor. La
  serie **V0.2.x** (v0.2.1 … v0.2.11+) es enteramente una secuencia de patches
  que endurecen y completan el Cognitive Dashboard Compiler de V0.2 (DOC10).
- **Minor** (`vX.Y.0`) — un salto de capacidad mayor con su propio plan de
  construcción. Desde **V0.3.0** en adelante cada minor es una versión mayor
  temática: Semantic Intelligence (V0.3), Filter Engine (V0.4), Connectors
  (V0.5), Combo Charts (V0.6).
- **Major** (`v1.0.0`) — el Cognitive BI Operating System completo (DOC9).

Las mejoras no planificadas que surjan durante el desarrollo se agregan como
patches adicionales dentro de la serie correspondiente (v0.2.12, v0.3.4, etc.).

## Mapa de un vistazo

| Versión | Tema | Plan |
| --- | --- | --- |
| **V0.2.x** | Cognitive Dashboard Compiler — hardening + UX (patches) | DOC10 |
| **V0.3.0** | Semantic Dashboard Intelligence | DOC9 §V0.3 |
| **V0.4.0** | Filter Engine — Parameter Intelligence (20 motores) | **DOC11** |
| **V0.5.0** | Connectors & Data Sources | — |
| **V0.6.0** | Combo Charts + Advanced Visualizations | — |
| **V1.0.0** | Cognitive BI Operating System | DOC9 §V1.0 |

---

## v0.2.1 — Release Integrity

Objetivo: dejar la base en estado profesional antes de seguir construyendo.

- Unificar versiones de todos los paquetes (`pyproject.toml`, `package.json`)
- Corregir los 38 errores ruff pendientes
- CI completamente verde: backend (pytest + ruff + mypy) + frontend (build)
- `README.md` con instrucciones de instalación y uso básico
- `CHANGELOG.md` con entradas para v0.1.0 y v0.2.0
- Endpoint `GET /api/v1/meta` — devuelve versión, build hash, feature flags
- Fix: botón "New Dashboard" en app bar no funciona en todos los estados
- Fix: nuevo dashboard no arrastra la query ejecutada del dashboard anterior

---

## v0.2.2 — Bug Fixes Simples

Correcciones de comportamiento que afectan la experiencia directa del usuario.

- Fix: FeedbackEngine no debe reemplazar la inferencia original cuando el
  usuario no ha dado feedback explícito — solo aplicar cuando hay patrón
  confirmado por override del usuario
- Chart Selector: mostrar la preferencia aprendida del usuario marcada con ★

---

## v0.2.3 — Observability & Diagnostics

Objetivo: saber qué pasa internamente sin necesidad de debuggear a ciegas.

- Logging estructurado por módulo (JSON lines, nivel configurable)
- `trace_id` por ejecución — propagado desde API hasta cada módulo del pipeline
- Estados de ejecución explícitos: `success` / `warning` / `degraded` / `failed`
- Reemplazar todos los `except Exception` silenciosos por logging con nivel WARNING
- Panel técnico en ExplainPanel: muestra pipeline steps, timings, modules_run
- Modo debug activable por variable de entorno o query param (`?debug=1`)

---

## v0.2.4 — Contract Stabilization

Objetivo: contratos estables que permitan evolucionar sin romper silenciosamente.

- Versionar `InferenceResult`, `VisualSpec` y el schema `.sqlviz`
- Eliminar duplicación entre YAMLs de reglas (consolidar fuentes de verdad)
- Golden tests de serialización: aseguran que el JSON de salida no cambia forma
- Política formal documentada: `backward-compatible` / `breaking` / `deprecated`

---

## v0.2.5 — Frontend Maintainability

Objetivo: que el frontend sea mantenible antes de agregar más UI.

- Dividir `+page.svelte` (~36 KB) en componentes por responsabilidad
- Dividir `ExplainPanel.svelte` (~27 KB) — separar secciones en subcomponentes
- Stores por dominio: `dashboardStore`, `executionStore`, `uiStore`
- Estados uniformes en todos los componentes: `loading` / `empty` / `error` / `degraded`
- Accesibilidad básica: roles ARIA, navegación por teclado en sidebar y app bar
- Smoke tests frontend: al menos un test por ruta crítica
- Resizer vertical entre editor Monaco y dashboard: el usuario arrastra la barra
  divisoria para ajustar la altura del editor vs los gráficos

---

## v0.2.6 — Filtros Paramétricos + shadcn-svelte

Objetivo: filtros paramétricos completos y controles de UI profesionales.

- Los 8 tipos de filtro paramétrico funcionando end-to-end en la FilterBar:
  `dropdown`, `multiselect`, `date_picker`, `date_range_picker`, `numeric`,
  `range_slider`, `search`, `toggle`
- FilterEngine: detección de columna para `col IN ($var)` (multiselect) y
  `col BETWEEN $a AND $b` (rangos de fecha/numéricos)
- Reescritura `IN ($var)` → `IN $var` al bindear listas (DuckDB no castea un
  array dentro de paréntesis)
- Orden determinista de las variables de rango (`dict.fromkeys` en vez de
  `set()` — evitaba que el hash-seed invirtiera `desde`/`hasta`, `min`/`max`)
- Controles "ricos" alimentados por el dominio real de la columna: nuevo
  endpoint `POST /api/v1/panels/{id}/filter-domain` (valores distintos para
  dropdown/multiselect, `MIN`/`MAX` para el slider) vía reescritura del SQL
  con sqlglot; degradación elegante a input de texto si no hay dominio
- Migración a **shadcn-svelte** de todos los controles de filtro:
  Select, Combobox, Calendar/RangeCalendar, Slider, Switch, Input
- Tema dark/light: tokens de shadcn aliaseados sobre los design tokens de
  DOC6 (`--sqlviz-*`) — una definición maneja ambos temas
- Auditoría de variantes de atributo de los componentes generados contra la
  versión de bits-ui instalada (`data-[state=…]` / `data-[orientation=…]`),
  más animaciones de apertura/cierre (`tw-animate-css`)

---

## v0.2.7 — Explorador de Dashboards Tipo VSCode

Objetivo: sidebar como explorador de proyectos, no solo lista plana.

- Sidebar izquierdo siempre visible, como explorador de proyectos
- Sidebar con grupos (carpetas) — el usuario crea grupos y organiza
  dashboards dentro de ellos
- Lista con icono inferido + nombre; dashboard activo resaltado
- **Skeleton** (shadcn) mientras carga la lista de dashboards
- **Skeleton** en los paneles del dashboard mientras se ejecuta el SQL
- Editar nombre y descripción de dashboard
- Eliminar dashboard con confirmación
- Menú por dashboard (click derecho o botón): editar nombre, editar
  descripción, mover a grupo, eliminar
- Click en dashboard: el editor Monaco muestra su SQL y posiciona el cursor
  al inicio
- Reubicar botón "Nuevo Dashboard" dentro del explorador
  (hoy está en la app bar, poco visible y fuera de contexto)
- Al crear nuevo dashboard no arrastrar la query del dashboard anterior
  (el editor SQL debe iniciar vacío)
- Todo con shadcn-svelte, a nivel profesional

---

## v0.2.8 — Sidebar Colapsable + Modo Dual

Objetivo: el sidebar se adapta al modo (Edit vs Preview) y puede colapsarse
para no ocupar espacio cuando no se necesita.

### Modo Edit — árbol tipo VSCode

Explorador editable (el de v0.2.7):

```
📁 Carpeta (colapsable/expandible)
  📊 Dashboard
  📊 Dashboard
📁 Otra carpeta
  📊 Dashboard
📊 Dashboard sin grupo
[+ Nuevo Dashboard]
```

- Carpetas colapsables/expandibles con click
- Menú de opciones por item (renombrar, descripción, mover, eliminar — v0.2.7)
- Organizar dashboards por grupos (drag o click)
- Botón "Nuevo Dashboard" visible

### Modo Preview — sidebar navegable limpio

Sin gestión, solo navegación:

```
── COMERCIAL ──────────      ← label de grupo + separador
  📊 Ventas mensuales
  📊 Pipeline

── RRHH ───────────────
  📊 Nómina

📊 Dashboard sin grupo
```

- Sin menús de gestión, sin botón "Nuevo Dashboard"
- Solo navegación por click
- Los grupos se muestran como labels con separador (no como carpetas)

### Colapsable (ambos modos)

- Modo expandido: icono + label
- Modo colapsado: solo iconos + tooltip al hover + separadores entre grupos
- Botón colapsar/expandir en el header del sidebar
- Animación suave de ancho
- Estado persistido en localStorage
- **Skeleton** (shadcn) coherente con el modo colapsado/expandido mientras carga

Todo con shadcn-svelte.

---

## v0.2.9 — Panel de Propiedades Lateral

Objetivo: panel de propiedades lateral completo que centraliza todas las
opciones de configuración de un panel, reemplazando los controles dispersos.

- Reemplaza el modal flotante del Chart Selector (solución temporal introducida
  en v0.2.2) con un panel lateral persistente y coherente
- Centraliza todas las propiedades del panel en un único lugar:
  - Tipo de chart (reemplaza el modal flotante actual)
  - Colores y paleta de la visualización
  - Dimensiones (ancho en columnas, altura en px)
  - Título editable
  - Ejes X e Y (campos, etiquetas, escala)
  - SQL content con editor inline
  - Explicación de inferencia (por qué el motor eligió ese chart)
- Se activa al hacer click en cualquier panel del dashboard en edit mode
- Reemplaza los controles de resize inline que hoy son poco descubribles

---

## v0.2.10 — Inference Hardening

Objetivo: motor de inferencia robusto, medido y determinista.

- Dataset de regresión congelado — ningún commit puede degradar accuracy
- Matriz de confusión sobre el dataset congelado, reportada en CI
- Abstención inteligente: cuando `confidence: low`, forzar `table` antes que
  arriesgar un chart incorrecto
- Benchmarks de latencia: p50/p95/p99 del pipeline completo
- Pruebas de determinismo: misma entrada → misma salida en 100 ejecuciones

---

## v0.2.11 — Chart Selector Mejorado

Objetivo: que la UI del chart selector refleje con precisión el estado del motor.

- Preferencia aprendida del usuario marcada con ★ en la lista de alternativas
- El motor nunca reemplaza silenciosamente la inferencia original — siempre
  muestra primero el resultado del pipeline y separa visualmente el override
- Historial de overrides por panel visible en el Chart Selector

---

# ═══════════════════════════════════════════════════════════════════════════
# V0.3 — Semantic Dashboard Intelligence
# ═══════════════════════════════════════════════════════════════════════════

## V0.3.0 — Semantic Dashboard Intelligence

> Comienza después de completar la serie V0.2.x. Plan detallado: DOC9 §"V0.3 —
> The Cognitive Foundation".

Objetivo: que SQLviz entienda semánticamente lo que el usuario está construyendo
y proponga estructura, no solo visualización. Es la primera capa cognitiva
(Levels 1–5 del CBIOS de DOC9).

Módulos (DOC9):

- **BusinessKnowledgeGraph** — SQL → extracción de entidades/métricas
  (extiende el Semantic Engine de DOC5); persiste entre sesiones.
- **InformationGainEngine** — cuánto conocimiento nuevo aporta cada panel;
  detección de redundancia (similitud > 0.85).
- **CoverageEngine** — mapa de cobertura sobre dominios configurables.
- **CuriosityEngine** (V0.3: solo generación de preguntas) — al menos 1
  propuesta después de cada query.
- **UncertaintyEngine** — score de incertidumbre por panel.

Criterios de salida: Knowledge Graph persiste, actualización < 100 ms por query,
cobertura para ≥ 3 dominios, ≥ 80 % test coverage.

---

## V0.3.x — Patches de Semantic Intelligence

Serie de patches sobre V0.3.0. Alcance se define durante el desarrollo; ejemplos
esperables:

- v0.3.1 — Tuning del InformationGain (umbral de redundancia configurable)
- v0.3.2 — Editor de dominios de cobertura (`coverage_domains.yaml` en la UI)
- v0.3.3 — Persistencia y visualización del Knowledge Graph
- v0.3.x — Correcciones y endurecimiento de los 5 motores cognitivos

---

# ═══════════════════════════════════════════════════════════════════════════
# V0.4 — Filter Engine: Parameter Intelligence
# ═══════════════════════════════════════════════════════════════════════════

## V0.4.0 — Filter Engine: Parameter Intelligence

> Plan de construcción completo y oficial: **DOC11**
> (`sqlviz-doc11-filter-engine-roadmap-v0.1.0.md`).

Objetivo: convertir los filtros paramétricos de V0.2 en un **Parameter
Intelligence Engine** de 20 motores — descubrimiento, tipado, comportamiento,
valores inteligentes, cascada, estado, validación, presets, historial,
preview, explicación y caché.

Estado de los 20 motores:

| # | Motor | Estado |
| --- | --- | --- |
| 1 | Parameter Discovery Engine | Parcial en V0.2 |
| 2 | Parameter AST Intelligence | Parcial en V0.2 |
| 3 | Parameter Type Intelligence | Parcial en V0.2 |
| 4 | Parameter Behavior Detection | Parcial en V0.2 |
| 5 | Dynamic Filter UI Generator | Parcial en V0.2 |
| 6 | Parameter Metadata System | Parcial en V0.2 |
| 7 | Value Provider Engine | Parcial en V0.2 |
| 8 | Smart Value Discovery | Parcial en V0.2 |
| 9 | Cascading Filter Engine | **V0.4.0** |
| 10 | Parameter State Management | **V0.4.0** |
| 11 | Parameter Validation Engine | **V0.4.0** |
| 12 | Parameter Preset System | **V0.4.0** |
| 13 | Parameter History Engine | **V0.4.0** |
| 14 | Parameter Preview Engine | **V0.4.0** |
| 15 | Parameter Explain Engine | **V0.4.0** |
| 16 | Parameter Cache Engine | **V0.4.0** |
| 18 | Parameter Session Engine | **V0.4.0** |
| 17 | Parameter Security Engine | V1.0 |
| 19 | Parameter Analytics | V1.0 |
| 20 | Parameter SDK | V1.0 |

V0.4.0 endurece los motores 1–8 (parciales) y construye los motores 9–16 y 18.
Los motores 17, 19 y 20 se difieren a V1.0. Ver DOC11 para la especificación
completa de cada motor.

---

## V0.4.x — Patches del Filter Engine

Serie de patches sobre V0.4.0 (endurecimiento de cada motor, cobertura de
tests, correcciones de UX de filtros). Alcance se define durante el desarrollo.

---

# ═══════════════════════════════════════════════════════════════════════════
# V0.5 — Connectors & Data Sources
# ═══════════════════════════════════════════════════════════════════════════

## V0.5.0 — Connectors & Data Sources

Objetivo: que SQLviz consulte más allá de DuckDB local.

- Conectores a fuentes externas (Postgres, MySQL, archivos remotos, warehouses)
- Gestión de conexiones (`connection_id` ya existe en el modelo de datos)
- Credenciales seguras por conexión
- Introspección de schema por fuente para alimentar el DataProfile
- Aislamiento de ejecución por conexión (DOC7 §5)

---

# ═══════════════════════════════════════════════════════════════════════════
# V0.6 — Combo Charts + Advanced Visualizations
# ═══════════════════════════════════════════════════════════════════════════

## V0.6.0 — Combo Charts + Advanced Visualizations

Objetivo: ampliar el vocabulario visual más allá de los charts V0.1.

- Combo charts (líneas + barras, doble eje Y)
- Visualizaciones avanzadas (waterfall, funnel, heatmap, boxplot, sankey)
- Nuevas afinidades chart↔intent en la matriz (DOC5)
- El ScoringModel y el VisualizationCandidateGenerator aprenden los nuevos tipos

---

# ═══════════════════════════════════════════════════════════════════════════
# V1.0 — Cognitive BI Operating System
# ═══════════════════════════════════════════════════════════════════════════

## V1.0.0 — Cognitive BI Operating System (CBIOS)

> Visión completa: **DOC9** (`sqlviz-doc9-cognitive-bi-vision-v0.1.0.md`),
> §"V1.0 — The Full Cognitive Operating System".

Objetivo: los 10 niveles del CBIOS operativos. El sistema operativo cognitivo de
BI completo.

- **CuriosityEngine (enhanced)** — propuesta → ejecución en un click (genera SQL)
- **CognitiveCostEngine** — costo cognitivo por dashboard
- **AttentionSimulator** — modelo de atención (KPI → trend → detalle)
- **DashboardGenome** — genoma que diferencia clusters de dashboards
- **DashboardEvolution** — evolución del dashboard
- **CognitiveTwin** — gemelo cognitivo (mejora la selección de chart ≥ 15 %)
- **Filter Engine — motores diferidos:** Parameter Security (17), Parameter
  Analytics (19), Parameter SDK (20) — ver DOC11.

Criterios de salida (DOC9): los 10 niveles operativos, ≥ 85 % test coverage,
sostenible por una persona (Principio 5), y garantía de privacidad (datos del
twin locales).
