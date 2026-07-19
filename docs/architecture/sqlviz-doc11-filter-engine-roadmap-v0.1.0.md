# SQLviz — DOC11: Filter Engine Roadmap (Parameter Intelligence)

**Plan de construcción oficial de V0.4.0.**
Mismo rol para V0.4 que DOC10 tuvo para V0.2: define el alcance, los módulos, las
fases de construcción, el modelo de datos y la definición de Done.

| | |
| --- | --- |
| **Estado** | Frozen para V0.4.0 |
| **Versión objetivo** | V0.4.0 (minor mayor temática) + serie V0.4.x |
| **Difiere a V1.0** | Motores 17, 19, 20 |
| **Documentos relacionados** | DOC5 (Inference Engine), DOC6 (UI), DOC7 (Security), DOC10 (V0.2 plan), `sqlviz-roadmap.md` |

---

## 0. Propósito

Convertir los **filtros paramétricos** de V0.2 en un **Parameter Intelligence
Engine** completo: un subsistema de 20 motores que descubre parámetros en el
SQL, infiere su tipo y comportamiento, genera el control de UI correcto, provee
valores inteligentes, gestiona estado/cascada/validación/presets/historial, y
explica todo — sin que el usuario declare nada manualmente.

El principio es el mismo que el del Cognitive Dashboard Compiler (DOC10): **el
usuario escribe SQL; el sistema infiere el resto.** Aquí el "resto" son los
filtros.

---

## 1. Diagnóstico del estado actual (V0.2)

V0.2 entregó filtros paramétricos funcionales (v0.2.6). Verificado por código:

- `sqlviz_inference.filters.filter_engine.FilterEngine` — detecta `$variable`,
  asocia columna+operador (regex), clasifica el `control_type`.
- `sqlviz_inference.filters.range_pairing.pair_range_filters` — funde pares de
  rango (`desde`/`hasta`, `min`/`max`) en un control único.
- `sqlviz_inference.filters.domain.build_domain_query` — reescribe el SQL con
  sqlglot para obtener valores distintos / min-max de una columna.
- API: `POST /api/v1/panels/{id}/execute` (bind de variables, rewrite
  `IN ($var)` → `IN $var`), `POST /api/v1/panels/{id}/filter-domain`.
- UI: `FilterControl.svelte` (8 tipos con shadcn-svelte), `FilterBar.svelte`,
  store `filterValues`.

Los **8 tipos de control** existentes: `dropdown`, `multiselect`, `date_picker`,
`date_range_picker`, `numeric`, `range_slider`, `search`, `toggle`.

**Veredicto:** esto es una implementación **parcial de los motores 1–8**. Es un
buen motor de filtros V0, no el sistema de Parameter Intelligence completo. Los
motores 9–16 y 18 no existen. Los motores 17, 19, 20 son V1.0.

---

## 2. Los 20 motores — visión general

```
Grupo A — Descubrimiento e inferencia (motores 1–4)   [parcial V0.2 → hardening V0.4]
Grupo B — UI, metadata y valores      (motores 5–8)   [parcial V0.2 → hardening V0.4]
Grupo C — Comportamiento avanzado     (motores 9–16,18)[nuevo — V0.4.0]
Grupo D — Plataforma                  (motores 17,19,20)[V1.0]
```

| # | Motor | Grupo | Estado |
| --- | --- | --- | --- |
| 1 | Parameter Discovery Engine | A | Parcial V0.2 → V0.4 |
| 2 | Parameter AST Intelligence | A | Parcial V0.2 → V0.4 |
| 3 | Parameter Type Intelligence | A | Parcial V0.2 → V0.4 |
| 4 | Parameter Behavior Detection | A | Parcial V0.2 → V0.4 |
| 5 | Dynamic Filter UI Generator | B | Parcial V0.2 → V0.4 |
| 6 | Parameter Metadata System | B | Parcial V0.2 → V0.4 |
| 7 | Value Provider Engine | B | Parcial V0.2 → V0.4 |
| 8 | Smart Value Discovery | B | Parcial V0.2 → V0.4 |
| 9 | Cascading Filter Engine | C | **Nuevo — V0.4.0** |
| 10 | Parameter State Management | C | **Nuevo — V0.4.0** |
| 11 | Parameter Validation Engine | C | **Nuevo — V0.4.0** |
| 12 | Parameter Preset System | C | **Nuevo — V0.4.0** |
| 13 | Parameter History Engine | C | **Nuevo — V0.4.0** |
| 14 | Parameter Preview Engine | C | **Nuevo — V0.4.0** |
| 15 | Parameter Explain Engine | C | **Nuevo — V0.4.0** |
| 16 | Parameter Cache Engine | C | **Nuevo — V0.4.0** |
| 18 | Parameter Session Engine | C | **Nuevo — V0.4.0** |
| 17 | Parameter Security Engine | D | Diferido — V1.0 |
| 19 | Parameter Analytics | D | Diferido — V1.0 |
| 20 | Parameter SDK | D | Diferido — V1.0 |

---

## 3. Especificación por motor

Formato por motor: **Propósito · Estado actual · Entrada → Salida · Alcance
V0.4 · Archivos/contratos.**

### Grupo A — Descubrimiento e inferencia

#### Motor 1 — Parameter Discovery Engine
- **Propósito:** encontrar todos los parámetros (`$variable`) en el SQL.
- **Estado actual:** `VARIABLE_PATTERN = \$(\w+)` en `filter_engine.py`;
  `dict.fromkeys` para dedup con orden estable.
- **Entrada → Salida:** `sql: str` → `list[ParamRef]` (nombre + posiciones).
- **Alcance V0.4:** ignorar `$var` dentro de strings y comentarios (usar tokens/
  AST del Motor 2), soportar sintaxis alternativas (`:name`, `@name`) detrás de
  un flag, múltiples ocurrencias del mismo parámetro.
- **Archivos:** `filters/discovery.py` (extraído de `filter_engine.py`).

#### Motor 2 — Parameter AST Intelligence
- **Propósito:** entender el **rol sintáctico** de cada parámetro vía AST real,
  no regex: a qué columna compara, con qué operador, en qué cláusula.
- **Estado actual:** `_find_associated_column` (regex para `=`, `IN`, `BETWEEN`,
  `ANY`, `LIKE`). Frágil ante SQL complejo.
- **Entrada → Salida:** `sql` → `dict[param, {column, operator, clause, table}]`.
- **Alcance V0.4:** reemplazar el regex por **sqlglot** (ya usado en
  `domain.py`): recorrer el AST, localizar cada `Placeholder`, resolver su
  columna/operador/tabla incluso con joins, subqueries y CTEs.
- **Archivos:** `filters/ast_intelligence.py`.

#### Motor 3 — Parameter Type Intelligence
- **Propósito:** inferir el tipo de dato del parámetro desde la columna asociada.
- **Estado actual:** `_classify_control` mapea tipo de columna → familia; el
  endpoint de execute prueba la query con `$var = NULL` para recuperar el schema.
- **Entrada → Salida:** `{param, column}` + schema → `ParamType`
  (`varchar|date|timestamp|numeric|boolean|enum|array`).
- **Alcance V0.4:** enums (columnas de baja cardinalidad), timestamps con tz,
  arrays (para multiselect nativo), decimales con escala.
- **Archivos:** `filters/type_intelligence.py`.

#### Motor 4 — Parameter Behavior Detection
- **Propósito:** detectar **cómo se usa** el parámetro: igualdad, pertenencia
  (multi), búsqueda (LIKE), rango (BETWEEN / `>= <=`).
- **Estado actual:** `_get_operator_context` (`equality|multi|search|range`) +
  `pair_range_filters`.
- **Entrada → Salida:** `{param, operator, clause}` → `Behavior`.
- **Alcance V0.4:** `NOT IN`, rangos abiertos (`>=` sin `<=`), `ILIKE` anclado
  vs contains, negaciones, comportamiento por defecto configurable en metadata.
- **Archivos:** `filters/behavior.py`.

### Grupo B — UI, metadata y valores

#### Motor 5 — Dynamic Filter UI Generator
- **Propósito:** generar el control de UI correcto para cada parámetro.
- **Estado actual:** `FilterControl.svelte` (8 tipos shadcn), `FilterBar.svelte`.
- **Entrada → Salida:** `FilterControl[]` (+ dominios) → controles renderizados.
- **Alcance V0.4:** controles nuevos derivados de los motores C (combobox con
  búsqueda server-side, cascada visual, presets), layout responsive de la
  FilterBar, estados de validación inline (Motor 11).
- **Archivos:** `packages/sqlviz-web/src/lib/components/FilterControl.svelte`
  (+ subcomponentes por tipo).

#### Motor 6 — Parameter Metadata System
- **Propósito:** metadata declarativa por parámetro (label, columna, tipo,
  scope, default, required, grupo, descripción).
- **Estado actual:** dataclass `FilterControl` (variable, label, control_type,
  column_name, column_type, scope).
- **Entrada → Salida:** `ParamRef` + inferencias → `ParamMetadata` (persistida).
- **Alcance V0.4:** persistir metadata por dashboard/panel (tabla nueva),
  overrides del usuario (renombrar label, fijar default, marcar required),
  agrupar parámetros.
- **Contrato:** `ParamMetadata` (versionado, como `VisualSpec`).

#### Motor 7 — Value Provider Engine
- **Propósito:** proveer el conjunto de valores que un control ofrece.
- **Estado actual:** `POST /filter-domain` (`kind: distinct|range`).
- **Entrada → Salida:** `{param, column}` → `{values[] | min/max}`.
- **Alcance V0.4:** providers pluggables — lista estática, query SQL a medida,
  API externa —, paginación y búsqueda server-side, orden configurable.
- **Archivos:** `filters/value_provider.py` + endpoint.

#### Motor 8 — Smart Value Discovery
- **Propósito:** descubrir el dominio real de una columna de forma barata.
- **Estado actual:** `domain.build_domain_query` (sqlglot: quita el WHERE
  paramétrico y proyecta la columna; distinct/min-max).
- **Entrada → Salida:** `sql, column, kind` → query de dominio.
- **Alcance V0.4:** cardinalidad estimada (decidir dropdown vs combobox vs
  search), top-N con conteos, sampling para columnas enormes, cache (Motor 16).
- **Archivos:** `filters/domain.py` (extendido).

### Grupo C — Comportamiento avanzado (nuevo en V0.4.0)

#### Motor 9 — Cascading Filter Engine
- **Propósito:** filtros dependientes — el valor elegido en un filtro restringe
  los valores disponibles de otro (p. ej. País → Ciudad).
- **Entrada → Salida:** `{param, selección de padres}` → dominio filtrado.
- **Alcance V0.4:** detectar dependencias por columnas correlacionadas o
  declaración explícita en metadata; recomputar dominios hijos al cambiar el
  padre (reusando Motor 7/8 con un WHERE adicional).
- **Archivos:** `filters/cascading.py`.

#### Motor 10 — Parameter State Management
- **Propósito:** fuente de verdad del estado de todos los filtros: valores
  actuales, sincronización, persistencia y URL.
- **Estado actual:** store `filterValues` (session-only).
- **Alcance V0.4:** máquina de estado por dashboard, persistencia (tabla
  `filter_memory` ya existe en el schema), sincronización con la URL
  (deep-linking de filtros), reset y "clear all".
- **Archivos:** `stores/filterState.svelte.ts` + `filter_memory`.

#### Motor 11 — Parameter Validation Engine
- **Propósito:** validar los valores antes de ejecutar (tipo, rango, required,
  formato de fecha, lista permitida).
- **Alcance V0.4:** reglas derivadas de los motores 3/6; feedback inline en el
  control (Motor 5); bloquear/avisar en Run si un `required` está vacío.
- **Archivos:** `filters/validation.py`.

#### Motor 12 — Parameter Preset System
- **Propósito:** guardar y cargar combinaciones de valores de filtro con nombre.
- **Alcance V0.4:** CRUD de presets por dashboard (tabla nueva), aplicar preset
  en un click, preset por defecto opcional.
- **Archivos:** `filters/presets.py` + endpoints + UI en la FilterBar.

#### Motor 13 — Parameter History Engine
- **Propósito:** historial de valores usados por filtro (recientes).
- **Alcance V0.4:** persistir los últimos N valores por parámetro, sugerirlos en
  el control (autocomplete de recientes).
- **Archivos:** `filters/history.py`.

#### Motor 14 — Parameter Preview Engine
- **Propósito:** previsualizar el efecto de un cambio de filtro sin ejecutar
  todo el dashboard (p. ej. conteo de filas resultante).
- **Alcance V0.4:** query ligera `SELECT count(*)` con los filtros aplicados;
  mostrar el delta antes de confirmar.
- **Archivos:** `filters/preview.py` + endpoint.

#### Motor 15 — Parameter Explain Engine
- **Propósito:** explicar por qué un parámetro produjo cierto control y ciertos
  valores (extiende el ExplanationEngine V2 de DOC5).
- **Alcance V0.4:** trazas legibles ("`$region` → columna `region` (VARCHAR),
  operador `IN` → multiselect; 42 valores distintos").
- **Archivos:** `filters/explain.py` (integra con `ExplanationEngine`).

#### Motor 16 — Parameter Cache Engine
- **Propósito:** cachear dominios y resultados de valores para no recomputar.
- **Alcance V0.4:** cache por (dashboard, columna, kind, filtros-padre) con
  invalidación por cambio de SQL/datos; TTL configurable.
- **Archivos:** `filters/cache.py`.

#### Motor 18 — Parameter Session Engine
- **Propósito:** parámetros con scope de sesión — persisten mientras el usuario
  navega entre dashboards dentro de la misma sesión.
- **Alcance V0.4:** distinguir scope `global` / `dashboard` / `session`;
  restaurar valores de sesión al volver a un dashboard.
- **Archivos:** `filters/session.py` + store.

### Grupo D — Plataforma (diferido a V1.0)

#### Motor 17 — Parameter Security Engine (V1.0)
- **Propósito:** sanitización y prevención de inyección, permisos por parámetro
  y por rol (DOC7). Garantizar que ningún valor de filtro pueda alterar la
  semántica de la query más allá del bind previsto.
- **Por qué V1.0:** requiere el modelo de roles/seguridad maduro de DOC7 y el
  hardening del pipeline completo.

#### Motor 19 — Parameter Analytics (V1.0)
- **Propósito:** telemetría de uso de filtros (qué filtros se usan, con qué
  valores, cuánto tardan) para alimentar recomendaciones.
- **Por qué V1.0:** depende de la capa de analytics/observabilidad global.

#### Motor 20 — Parameter SDK (V1.0)
- **Propósito:** API pública para definir, extender y componer filtros
  programáticamente (custom providers, custom controls, custom validaciones).
- **Por qué V1.0:** un contrato público estable solo tiene sentido cuando los
  19 motores anteriores están congelados.

---

## 4. Fases de construcción — V0.4.0

Orden por dependencias (como DOC10 §8). Cada fase es shippeable.

- **Fase 0 — Contratos.** `ParamRef`, `ParamMetadata`, `ParamType`, `Behavior`,
  `FilterDomain` versionados (política de contratos de v0.2.4). Nada de lógica.
- **Fase A — Hardening del descubrimiento (motores 1–4).** Migrar la asociación
  columna/operador de regex a sqlglot (Motor 2); extraer `discovery.py`,
  `ast_intelligence.py`, `type_intelligence.py`, `behavior.py` desde
  `filter_engine.py` sin cambiar el comportamiento observable (los tests
  actuales de filtros deben seguir verdes).
- **Fase B — Value/Metadata (motores 6–8).** `ParamMetadata` persistida +
  `value_provider.py` pluggable + `Smart Value Discovery` con cardinalidad y
  top-N. UI del Motor 5 consume los dominios enriquecidos.
- **Fase C — State + Validation + Session (motores 10, 11, 18).** Máquina de
  estado de filtros, persistencia (`filter_memory`), URL sync, validación
  inline, scope de sesión.
- **Fase D — Cascading + Cache + Preview (motores 9, 16, 14).** Dependencias
  entre filtros, cache de dominios, preview de conteo.
- **Fase E — Presets + History + Explain (motores 12, 13, 15).** CRUD de
  presets, recientes por parámetro, trazas de explicación integradas con el
  ExplanationEngine.
- **Fase F — Benchmark de filtros.** Dataset de queries paramétricas con el
  control esperado por parámetro; regresión que ningún commit puede degradar
  (como el benchmark doctoral de DOC10 §Fase G).

---

## 5. Cambios en el modelo de datos

- **`param_metadata`** (nueva tabla): overrides por (dashboard/panel, param) —
  label, default, required, grupo, scope, provider.
- **`filter_presets`** (nueva tabla): presets con nombre por dashboard.
- **`filter_memory`** (ya existe: `dashboard_id, variable, value, updated_at`):
  la usa el Motor 10 (state) y el Motor 13 (history).
- **`FilterControl` / contratos**: se extienden a `ParamMetadata` versionado;
  `FilterDomain` gana cardinalidad y conteos.

Cada cambio de schema entra por una migración (convención de
`sqlviz_storage.migrations`).

---

## 6. Definición de Done — V0.4.0

V0.4.0 está completo cuando, y solo cuando:

1. Los motores 1–8 están **refactorizados** a módulos dedicados con la
   asociación columna/operador basada en AST (sqlglot), sin regresiones en los
   tests de filtros de V0.2.
2. Los motores 9–16 y 18 están **implementados** con tests (≥ 80 % coverage del
   subpaquete `filters/`).
3. Cascada, validación, presets, historial, preview, explicación, cache y scope
   de sesión funcionan end-to-end en la FilterBar.
4. El estado de filtros persiste y es deep-linkable por URL.
5. Existe el benchmark de filtros y está verde en CI.
6. Los contratos nuevos están versionados y con golden tests.
7. Motores 17, 19, 20 quedan explícitamente diferidos a V1.0.

---

## 7. Qué queda diferido — y cuándo vuelve

```
Motor / feature                        Vuelve en
──────────────────────────────────────────────────
Parameter Security Engine (17)         V1.0
Parameter Analytics (19)               V1.0
Parameter SDK (20)                     V1.0
Providers de fuentes externas          V0.5 (Connectors) + V0.4 (interfaz)
```

---

*SQLviz DOC11 — Filter Engine Roadmap v0.1.0*
*"El usuario escribe SQL con `$parámetros`. Los 20 motores infieren el control,*
*los valores, la cascada, el estado y la explicación — sin declarar nada."*
