# Roadmap de releases: v0.2.9 → v1.0.0 Beta

**Creado:** 2026-10-17. **Estado:** F0 en curso.
**Seguimiento operativo:** [milestones de GitHub](https://github.com/eribertocz/sqlviz/milestones)
(uno por fase) e issues con labels `fase:F*`, `tamaño:S|M`, `tipo:*`.

Este documento fija fases, versiones objetivo e issues tentativos. El
[plan operativo del Studio](sqlviz-studio-delivery-plan.md) conserva el detalle
técnico de cada etapa S*/M*/R*; este roadmap lo agrupa en releases. Los issues
de cada fase se abren oficialmente al iniciarla; la lista aquí es tentativa y se
ajusta al cerrar cada fase.

## Política de versiones

| Tag | Formato (PEP 440, hatch-vcs) | Cuándo |
| --- | --- | --- |
| Alpha intermedio | `v0.N.0a1`, `v0.N.0a2` | A mitad de fase, al completar un recorrido usable |
| Cierre de fase | `v0.N.0` | Criterio de cierre cumplido; 0.x admite rupturas |
| Patch | `v0.N.1` | Solo correcciones sobre una fase cerrada |
| Alpha de 1.0 | `v1.0.0aN` | Recorrido central completo, se completa alcance 1.0 |
| **Beta de 1.0** | `v1.0.0b1` | **Meta de este roadmap:** feature freeze y contratos estables |
| RC / estable | `v1.0.0rcN`, `v1.0.0` | Fuera de alcance: roadmap posterior de mejora por fases |

**Tamaños:** S = 1–2 días, un PR, una capa. M = 3–5 días, un PR, puede cruzar
capas. Un issue mayor que M se divide antes de empezar.

**Flujo:** issue → rama `<tipo>/F<n>-<nn>-<slug>` desde `main` → PR con
`Closes #N` → CI verde → merge → al alcanzar un hito: CHANGELOG + tag + release.

## F0 — Consolidación → `v0.3.0`

| ID | Issue | Tam. |
| --- | --- | --- |
| F0-01 (#1) | Registrar roadmap de releases y milestones | S |
| F0-02 (#2) | Limpiar artefactos de la raíz y `.gitignore` | S |
| F0-03 (#3) | Plantillas de issue/PR | S |
| F0-04 (#4) | CHANGELOG desde v0.2.9 | S |
| F0-05 (#5) | CI obligatoria en PRs a `main` | S |
| F0-06 (#6) | Merge de `feat/sqlviz-foundations` → `main` y tag `v0.3.0` | M |

Cierre: `main` verde, sin ramas largas, primer release salido de un PR.

## F1 — Lienzo persistido (S1) → `v0.4.0a1` → `v0.4.0`

| ID | Issue | Tam. |
| --- | --- | --- |
| F1-01 | S1.1c.2c.3b: API tipada/autorizada de borrador y revisión | M |
| F1-02 | 3c: autoguardado web con revisión confirmada y conflicto visible | M |
| F1-03 | 3d: recuperación de respuesta perdida, IDs durables de operación | M |
| — | **tag `v0.4.0a1`** | |
| F1-04 | Contrato del documento de layout versionado | S |
| F1-05 | Migración de overrides legacy de altura al layout | M |
| F1-06 | Repositorio transaccional de layout con revisión | M |
| F1-07 | Endpoints de layout (admin escribe, viewer lee) | S |
| F1-08 | UI de posición/columnas/alto sin re-ejecutar SQL | M |
| F1-09 | E2E editar → guardar → reabrir → compartir | S |

Cierre: el diseño sobrevive a recarga y viewer; guardados obsoletos se rechazan.

## F2 — Mover con confianza (S2) → `v0.5.0a1` → `v0.5.0`

| ID | Issue | Tam. |
| --- | --- | --- |
| F2-01 | Drag con GridStack sobre contrato S0, preview y guías | M |
| F2-02 | Resize con mínimos y colisiones | M |
| — | **tag `v0.5.0a1`** | |
| F2-03 | Cancelación con Esc y bloqueo de paneles | S |
| F2-04 | Undo/redo de layout | M |
| F2-05 | Teclado y alternativa clic/tap | M |
| F2-06 | Gestos sin conflicto con ECharts; mover no ejecuta SQL | S |

## F3 — Dataset/Visual/Panel (S3 + M1 + R1) → `v0.6.0a1` → `v0.6.0`

| ID | Issue | Tam. |
| --- | --- | --- |
| F3-01 | Dataset con revisiones y esquema + migración | M |
| F3-02 | Entidad Visual con bindings a campos | M |
| F3-03 | Panel → Visual; un dataset alimenta dos visuales | M |
| — | **tag `v0.6.0a1`** | |
| F3-04 | SQL reordenado no transfiere personalizaciones | S |
| F3-05 | Matriz M1: grano y medidas mínimas | M |
| F3-06 | Biblioteca R1: listar/buscar por ID/revisión | M |

## F4 — Primer recorrido completo (S4 + M2–M5) → `v0.7.0a1`, `a2` → `v0.7.0`

| ID | Issue | Tam. |
| --- | --- | --- |
| F4-01 | Nivel Automático sobre la entidad Visual | M |
| F4-02 | Visual Builder: tipo y campos → canales | M |
| — | **tag `v0.7.0a1`** | |
| F4-03 | Nivel experto: opciones nativas ECharts con precedencia | M |
| F4-04 | Reset/undo entre niveles | S |
| F4-05 | Matriz M2–M3: filas/columnas con drag de campos | M |
| F4-06 | Matriz M4–M5: totales/subtotales por contexto | M |
| — | **tag `v0.7.0a2`** | |
| F4-07 | E2E builder → guardar → filtrar → reabrir → viewer → reset | M |

Cierre ("MVP alpha"): un dashboard de punta a punta sin tocar código.

## F5 — Inferencia y renderizado (S5 + M6–M7) → `v0.8.0a1` → `v0.8.0`

| ID | Issue | Tam. |
| --- | --- | --- |
| F5-01 | Corpus de evaluación independiente con métrica en CI | M |
| F5-02 | Fechas, granularidad y unidades | M |
| F5-03 | Nulos y datos vacíos | S |
| — | **tag `v0.8.0a1`** | |
| F5-04 | Familias ECharts lote 1 (heatmap, scatter, combinado) | M |
| F5-05 | Familias ECharts lote 2 (treemap, funnel, gauge) | M |
| F5-06 | Formato numérico/semántico | M |
| F5-07 | Escala de matriz: virtualización y carga progresiva | M |

## F6 — Pantalla y áreas (S6) → `v0.9.0`

| ID | Issue | Tam. |
| --- | --- | --- |
| F6-01 | Usar altura disponible sin recortar | M |
| F6-02 | Mínimos medidos por visual y fallback explicado | S |
| F6-03 | Secciones/áreas del dashboard | M |
| F6-04 | Lectura responsive preservando desktop | M |

## F7 — Interacciones del lector (S7) → `v1.0.0a1`

| ID | Issue | Tam. |
| --- | --- | --- |
| F7-01 | Filtros versionados con alcance | M |
| F7-02 | Crossfilter visible y reversible | M |
| F7-03 | Drill autorizado por rol | M |
| F7-04 | Cancelación efectiva de SQL en DuckDB | M |
| F7-05 | Contexto preservado al navegar entre dashboards | S |

## F8 — Publicación (S8 + R4) → `v1.0.0a2`

| ID | Issue | Tam. |
| --- | --- | --- |
| F8-01 | Revisión publicada estable separada del borrador | M |
| F8-02 | Preview fiel | S |
| F8-03 | Exportaciones autorizadas (PNG/CSV) | M |
| F8-04 | Bundles de definiciones export/import | M |
| F8-05 | Estados vacío/error/carga homogéneos | S |

## F9 — Endurecimiento → `v1.0.0a3` → **`v1.0.0b1`**

| ID | Issue | Tam. |
| --- | --- | --- |
| F9-01 | Contratos 1.0 congelados con golden tests | M |
| F9-02 | Matriz negativa de seguridad/autorización | M |
| F9-03 | Accesibilidad WCAG AA en flujos clave | M |
| F9-04 | Presupuesto de rendimiento y benchmarks en CI | M |
| F9-05 | Migraciones probadas v0.2.9 → beta | M |
| F9-06 | Documentación de usuario e instalación | M |
| F9-07 | Pruebas con usuarios y triage | M |

## Después de la Beta

Roadmap separado: ciclo RC repasando cada fase solo con correcciones y pulido,
`v1.0.0` estable sin bloqueantes, y 1.x con conectores (R5), alertas (R6) y
APIs (R7).
