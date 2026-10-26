# Roadmap de releases: v0.2.11 → Beta (v0.12.0b)

**Creado:** 2026-10-17. **Revisado:** 2026-10-25 (política alpha → beta).
**Estado:** F0 cerrada (`v0.3.0`); F1 en curso.
**Seguimiento operativo:** [milestones de GitHub](https://github.com/eribertocz/sqlviz/milestones)
(uno por fase) e issues con labels `fase:F*`, `tamaño:S|M`, `tipo:*`.

Este documento fija fases, versiones objetivo e issues tentativos. El
[plan operativo del Studio](sqlviz-studio-delivery-plan.md) conserva el detalle
técnico de cada etapa S*/M*/R*; este roadmap lo agrupa en releases. Los issues
de cada fase se abren oficialmente al iniciarla; la lista aquí es tentativa y se
ajusta al cerrar cada fase.

## Política de versiones

SQLviz no es apto para producción hasta `v1.0.0`. Hasta entonces la madurez se
lee en el sufijo del tag, y **todos los releases se publican como pre-release**:
`pip install sqlviz` no los instala sin `--pre`, lo que refleja su estado real.

| Etapa | Fases | Tags (PEP 440, hatch-vcs) | Significado |
| --- | --- | --- | --- |
| **Alpha** | F1–F4 | `v0.N.0a1`, `v0.N.0a2`… | Aún no usable de punta a punta; contratos y datos pueden romperse |
| **Beta** | Desde el cierre de F4 hasta F9 | `v0.N.0b1`, `v0.N.0b2`… | Usable para crear y compartir dashboards; puede tener fallos y cambios con migración |
| RC | Roadmap posterior | `v1.0.0rc1`… | Solo correcciones y pulido; sin funcionalidad nueva |
| **Estable** | Roadmap posterior | `v1.0.0` | Pulido completo, sin bloqueantes |

Reglas:

- **Una fase = un minor** (`0.4`, `0.5`…). Cada fase publica solo pre-releases;
  la fase se cierra con su último alpha o beta, sin tag `v0.N.0` sin sufijo.
- **Alpha → Beta:** el primer beta (`v0.7.0b1`) sale cuando se cumple el cierre
  de F4: un usuario crea, guarda, filtra, reabre y comparte un dashboard sin
  tocar código.
- **Correcciones** sobre una fase ya cerrada: siguiente número del mismo sufijo
  (`v0.7.0b2`), nunca un patch final.
- **Fin de este roadmap:** `v0.12.0bN`, todavía **beta**. `v1.0.0` solo llega
  tras el roadmap de pulido (RC), cuando todo esté bien terminado.
- `v0.3.0` (F0) quedó publicado antes de esta política y se conserva.

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
| F0-04 (#4) | Verificar CHANGELOG `Unreleased` | S |
| F0-05 (#5) | CI obligatoria en PRs a `main` | S |
| F0-06 (#6) | Merge de `feat/sqlviz-foundations` → `main` y tag `v0.3.0` | M |

Cierre: `main` verde, sin ramas largas, primer release salido de un PR.

## F1 — Lienzo persistido (S1) → `v0.4.0a1`, `v0.4.0a2` · Alpha

| ID | Issue | Tam. |
| --- | --- | --- |
| F1-01 (#8) | S1.1c.2c.3b: API tipada/autorizada de borrador y revisión | M |
| F1-02 (#9) | 3c: autoguardado web con revisión confirmada y conflicto visible | M |
| F1-03 (#10) | 3d: recuperación de respuesta perdida, IDs durables de operación | M |
| — | **tag `v0.4.0a1`** (borrador fiable) | |
| F1-04 (#11) | Contrato del documento de layout versionado | S |
| F1-05 (#12) | Migración de overrides legacy de altura al layout | M |
| F1-06 (#13) | Repositorio transaccional de layout con revisión | M |
| F1-07 (#14) | Endpoints de layout (admin escribe, viewer lee) | S |
| F1-08 (#15) | UI de posición/columnas/alto sin re-ejecutar SQL | M |
| F1-09 (#16) | E2E editar → guardar → reabrir → compartir | S |
| F1-10 (#19) | Leer archivos locales de carpetas autorizadas (`--data-dir`) | S |
| — | **tag `v0.4.0a2`** (cierre de F1) | |

Cierre: el diseño sobrevive a recarga y viewer; guardados obsoletos se rechazan.

## F2 — Mover con confianza (S2) → `v0.5.0a1`, `v0.5.0a2` · Alpha

| ID | Issue | Tam. |
| --- | --- | --- |
| F2-01 | Drag con GridStack sobre contrato S0, preview y guías | M |
| F2-02 | Resize con mínimos y colisiones | M |
| — | **tag `v0.5.0a1`** | |
| F2-03 | Cancelación con Esc y bloqueo de paneles | S |
| F2-04 | Undo/redo de layout | M |
| F2-05 | Teclado y alternativa clic/tap | M |
| F2-06 | Gestos sin conflicto con ECharts; mover no ejecuta SQL | S |

## F3 — Dataset/Visual/Panel (S3 + M1 + R1) → `v0.6.0a1`, `v0.6.0a2` · Alpha

| ID | Issue | Tam. |
| --- | --- | --- |
| F3-01 | Dataset con revisiones y esquema + migración | M |
| F3-02 | Entidad Visual con bindings a campos | M |
| F3-03 | Panel → Visual; un dataset alimenta dos visuales | M |
| — | **tag `v0.6.0a1`** | |
| F3-04 | SQL reordenado no transfiere personalizaciones | S |
| F3-05 | Matriz M1: grano y medidas mínimas | M |
| F3-06 | Biblioteca R1: listar/buscar por ID/revisión | M |

## F4 — Primer recorrido completo (S4 + M2–M5) → `v0.7.0a1`, `a2` → **`v0.7.0b1` (primera Beta)**

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

Cierre: un dashboard de punta a punta sin tocar código → **paso a Beta** con `v0.7.0b1`.

## F5 — Inferencia y renderizado (S5 + M6–M7) → `v0.8.0b1`, `v0.8.0b2` · Beta

| ID | Issue | Tam. |
| --- | --- | --- |
| F5-01 | Corpus de evaluación independiente con métrica en CI | M |
| F5-02 | Fechas, granularidad y unidades | M |
| F5-03 | Nulos y datos vacíos | S |
| — | **tag `v0.8.0b1`** | |
| F5-04 | Familias ECharts lote 1 (heatmap, scatter, combinado) | M |
| F5-05 | Familias ECharts lote 2 (treemap, funnel, gauge) | M |
| F5-06 | Formato numérico/semántico | M |
| F5-07 | Escala de matriz: virtualización y carga progresiva | M |

## F6 — Pantalla y áreas (S6) → `v0.9.0b1` · Beta

| ID | Issue | Tam. |
| --- | --- | --- |
| F6-01 | Usar altura disponible sin recortar | M |
| F6-02 | Mínimos medidos por visual y fallback explicado | S |
| F6-03 | Secciones/áreas del dashboard | M |
| F6-04 | Lectura responsive preservando desktop | M |

## F7 — Interacciones del lector (S7) → `v0.10.0b1` · Beta

| ID | Issue | Tam. |
| --- | --- | --- |
| F7-01 | Filtros versionados con alcance | M |
| F7-02 | Crossfilter visible y reversible | M |
| F7-03 | Drill autorizado por rol | M |
| F7-04 | Cancelación efectiva de SQL en DuckDB | M |
| F7-05 | Contexto preservado al navegar entre dashboards | S |

## F8 — Publicación (S8 + R4) → `v0.11.0b1` · Beta

| ID | Issue | Tam. |
| --- | --- | --- |
| F8-01 | Revisión publicada estable separada del borrador | M |
| F8-02 | Preview fiel | S |
| F8-03 | Exportaciones autorizadas (PNG/CSV) | M |
| F8-04 | Bundles de definiciones export/import | M |
| F8-05 | Estados vacío/error/carga homogéneos | S |

## F9 — Endurecimiento → **`v0.12.0b1`** · Beta (fin de este roadmap)

| ID | Issue | Tam. |
| --- | --- | --- |
| F9-01 | Contratos candidatos a 1.0 congelados con golden tests | M |
| F9-02 | Matriz negativa de seguridad/autorización | M |
| F9-03 | Accesibilidad WCAG AA en flujos clave | M |
| F9-04 | Presupuesto de rendimiento y benchmarks en CI | M |
| F9-05 | Migraciones probadas v0.2.11 → beta | M |
| F9-06 | Documentación de usuario e instalación | M |
| F9-07 | Pruebas con usuarios y triage | M |

## Después de la Beta (roadmap de pulido, por planificar)

Al terminar F9 SQLviz sigue en **beta**. Un roadmap posterior repasa cada fase
de nuevo solo con correcciones, rendimiento, accesibilidad y documentación:
`v1.0.0rc1`, `rc2`… hasta `v1.0.0` estable sin bloqueantes. Conectores (R5),
alertas (R6) y APIs (R7) se planifican para 1.x.
