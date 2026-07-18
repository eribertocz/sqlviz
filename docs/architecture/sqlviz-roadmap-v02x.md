# SQLviz Roadmap — v0.2.x

Plan de versiones menores desde v0.2.1 hasta v0.2.11, seguido de v0.3.0.
Cada versión menor es independiente y shippeable. Las mejoras no planificadas
que surjan durante el desarrollo se agregan como versiones adicionales
(v0.2.12, v0.2.13, etc.).

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

- Sidebar con grupos colapsables (carpetas / dominios inferidos)
- Editar nombre y descripción de dashboard inline
- Eliminar dashboard con confirmación
- Organizar dashboards por grupos con drag o click
- Click en panel resalta el panel visualmente y en el editor Monaco hace scroll
  hasta el statement correspondiente, lo resalta completo y posiciona el cursor
  al inicio de ese query
- Reubicar botón "Nuevo Dashboard" en lugar estratégico dentro del explorador
  (hoy está en la app bar, poco visible y fuera de contexto)
- Al crear nuevo dashboard no arrastrar la query del dashboard anterior
  (el editor SQL debe iniciar vacío)

---

## v0.2.8 — Sidebar Colapsable

Objetivo: sidebar que no ocupe espacio cuando no se necesita.

- Modo expandido: icono + label + separadores entre grupos
- Modo colapsado: solo iconos + tooltip al hover + separadores visuales entre grupos
- Header del sidebar: logo cargable por el usuario + botón colapsar/expandir
- Estado persistido en localStorage

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

## v0.3.0 — Semantic Dashboard Intelligence

> Comienza después de completar v0.2.1 a v0.2.11.

Objetivo: que SQLviz entienda semánticamente lo que el usuario está construyendo
y proponga estructura, no solo visualización.

Alcance a definir una vez que v0.2.x esté completo y estable.
