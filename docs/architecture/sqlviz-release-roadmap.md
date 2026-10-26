# Roadmap de releases: v0.2.11 → Beta (v0.16.0b)

**Creado:** 2026-10-17. **Revisado:** 2026-10-25: política alpha → beta y
reordenamiento por la [integración de almacén, estado y ETL](sqlviz-almacen-etl-integracion-propuesta.md).
**Estado:** F0 cerrada (`v0.3.0`); F1 en curso.
**Seguimiento operativo:** [milestones de GitHub](https://github.com/eribertocz/sqlviz/milestones)
(uno por fase), un **issue paraguas** por fase e issues S/M con labels `fase:F*`,
`tamaño:S|M`, `tipo:*`.

Este documento fija fases, versiones objetivo y entregables tentativos. El
[plan operativo del Studio](sqlviz-studio-delivery-plan.md) conserva el detalle
técnico de las etapas S*/M*/R*; la [propuesta aprobada](sqlviz-almacen-etl-integracion-propuesta.md)
el de los hitos H0–H9 del almacén y el ETL. Este roadmap agrupa ambos en releases.

## Destino de despliegue

**Decisión del usuario — 2026-10-25:** SQLviz se despliega en la infraestructura
propia del cliente, **en Docker**, como un solo contenedor que es dueño del
proyecto (estado y almacén en un volumen). El almacén analítico es DuckDB; otras
bases se integran por `ATTACH`. La nube se diseña después de la versión estable.

Consecuencias en este roadmap:

- La **interfaz principal es la web**; la API la usan la web y las automatizaciones.
- La **CLI es mínima**: punto de entrada del contenedor (`sqlviz servir`) y
  `plan`/`aplicar` como cliente fino de la API para tareas programadas o CI.
  No es necesaria para usar el producto.
- Todo lo que hoy es interactivo en la terminal (contraseña del admin) debe poder
  configurarse con variables de entorno o desde la web.
- Las extensiones de DuckDB van **preinstaladas en la imagen**; las rutas de
  `ATTACH` y de archivos son volúmenes montados.
- El acceso por IP de red con `http://` deja la página en contexto inseguro
  (portapapeles y `crypto.randomUUID` fallan): la composición incluye HTTPS
  opcional y el frontend no debe depender de APIs de contexto seguro.

## Cómo se planifica cada fase

1. Cada fase tiene un **issue paraguas** con objetivo, versión, dependencias,
   criterio de cierre y lista tentativa de entregables.
2. **Al empezar la fase**, cada entregable de la lista se convierte en un issue
   S o M concreto; el paraguas los enlaza como lista de tareas.
3. Cada issue concreto se entrega con su rama y su PR. El paraguas se cierra
   cuando se cumple el criterio de cierre y se publica el tag de la fase.
4. Los entregables de fases futuras son tentativos: se ajustan al cerrar la
   fase anterior, sin abrir sus issues antes de tiempo.

## Política de versiones

SQLviz no es apto para producción hasta `v1.0.0`. Hasta entonces la madurez se
lee en el sufijo del tag, y **todos los releases se publican como pre-release**:
`pip install sqlviz` no los instala sin `--pre`, lo que refleja su estado real.

| Etapa | Fases | Tags (PEP 440, hatch-vcs) | Significado |
| --- | --- | --- | --- |
| **Alpha** | F1–F6 | `v0.N.0a1`, `v0.N.0a2`… | Aún no usable de punta a punta; contratos y datos pueden romperse |
| **Beta** | Desde el cierre de F6 hasta F13 | `v0.N.0b1`, `v0.N.0b2`… | Usable para crear y compartir dashboards; puede tener fallos y cambios con migración |
| RC | Roadmap posterior | `v1.0.0rc1`… | Solo correcciones y pulido; sin funcionalidad nueva |
| **Estable** | Roadmap posterior | `v1.0.0` | Pulido completo, sin bloqueantes |

Reglas:

- **Una fase = un minor** (`0.4`, `0.5`…). Cada fase publica solo pre-releases;
  la fase se cierra con su último alpha o beta, sin tag `v0.N.0` sin sufijo.
- **Alpha → Beta:** el primer beta (`v0.9.0b1`) sale al cerrar F6: un usuario
  crea, guarda, filtra, reabre y comparte un dashboard sin tocar código, sobre
  datos del almacén.
- **Correcciones** sobre una fase ya cerrada: siguiente número del mismo sufijo
  (`v0.9.0b2`), nunca un patch final.
- **Fin de este roadmap:** `v0.16.0bN`, todavía **beta**. `v1.0.0` solo llega
  tras el roadmap de pulido (RC), cuando todo esté bien terminado.
- `v0.3.0` (F0) quedó publicado antes de esta política y se conserva.

**Tamaños:** S = 1–2 días, un PR, una capa. M = 3–5 días, un PR, puede cruzar
capas. Un issue mayor que M se divide antes de empezar.

**Flujo:** issue → rama `<tipo>/F<n>-<nn>-<slug>` desde `main` → PR con
`Closes #N` → CI verde → merge → al alcanzar un hito: CHANGELOG + tag + release.

## Vista general

| Fase | Contenido | Hitos de origen | Versión | Etapa |
| --- | --- | --- | --- | --- |
| F0 | Consolidación | — | `v0.3.0` | Cerrada |
| F1 | Borrador fiable y archivos locales | S1.1c.2c.3, #19 | `v0.4.0a1` | Alpha |
| F2 | Base de proyecto | H0, H1 | `v0.5.0a1`, `a2` | Alpha |
| F3 | Almacén analítico y conexiones | H2, H3 | `v0.6.0a1`, `a2` | Alpha |
| F4 | ETL núcleo | H4, H5 | `v0.7.0a1`, `a2` | Alpha |
| F5 | Lienzo | S1.2, S1.3, S2 | `v0.8.0a1`, `a2` | Alpha |
| F6 | Dataset y primer recorrido | S3, S4, M1–M5, R1–R3 | `v0.9.0a1` → **`v0.9.0b1`** | **Primera Beta** |
| F7 | UI de datos | H6, H7 | `v0.10.0b1` | Beta |
| F8 | Programación y migración | H8, H9 | `v0.11.0b1` | Beta |
| F9 | Inferencia y renderizado | S5, M6–M7 | `v0.12.0b1`, `b2` | Beta |
| F10 | Pantalla y áreas | S6 | `v0.13.0b1` | Beta |
| F11 | Interacciones del lector | S7, M8 | `v0.14.0b1` | Beta |
| F12 | Publicación | S8, M9, R4 | `v0.15.0b1` | Beta |
| F13 | Endurecimiento | — | `v0.16.0b1` | Beta (fin) |

Dependencias principales: F2 → F3 → F4; F2 → F5; F3 → F6 (el dataset se diseña
sobre el almacén); F4 → F7 y F8. F5 no depende del almacén, pero se ubica tras
F4 por decisión del usuario. Ver el [orden unificado](sqlviz-almacen-etl-integracion-propuesta.md#orden-unificado-de-trabajo).

## F0 — Consolidación → `v0.3.0` · Cerrada

| ID | Issue | Tam. |
| --- | --- | --- |
| F0-01 (#1) | Registrar roadmap de releases y milestones | S |
| F0-02 (#2) | Limpiar artefactos de la raíz y `.gitignore` | S |
| F0-03 (#3) | Plantillas de issue/PR | S |
| F0-04 (#4) | Verificar CHANGELOG `Unreleased` | S |
| F0-05 (#5) | CI obligatoria en PRs a `main` | S |
| F0-06 (#6) | Merge de `feat/sqlviz-foundations` → `main` y tag `v0.3.0` | M |

## F1 — Borrador fiable y archivos locales → `v0.4.0a1` · Alpha

Reducida el 2026-10-25: el layout persistido (#11–#16) pasa a F5.

| ID | Issue | Tam. |
| --- | --- | --- |
| F1-01 (#8) | S1.1c.2c.3b: API tipada/autorizada de borrador y revisión | M |
| F1-02 (#9) | 3c: autoguardado web con revisión confirmada y conflicto visible | M |
| F1-03 (#10) | 3d: recuperación de respuesta perdida, IDs durables de operación | M |
| F1-10 (#19) | Leer archivos locales de carpetas autorizadas (`--data-dir`) | S |

Cierre: el borrador sobrevive a conflictos y respuestas perdidas → `v0.4.0a1`.

## F2 — Base de proyecto (H0 + H1) → `v0.5.0a1`, `a2` · Alpha

Objetivo: decidir y preparar la base. DuckDB 2.0.0, proyecto como carpeta y
almacén de estado, con el modo `.sqlviz` legado funcionando.

| ID | Entregable tentativo | Tam. |
| --- | --- | --- |
| F2-01 | Documento de decisión `sqlviz-proyecto-almacen-etl-decision.md` y actualización de los documentos listados en la propuesta | M |
| F2-02 | DuckDB 2.0.0: lockfile, suite verde, copia previa obligatoria al abrir proyectos de 1.5.x, nota de incompatibilidad | M |
| F2-03 | Imagen Docker y `docker compose`: usuario no root, volumen del proyecto, `.env`, extensiones `sqlite`/`postgres` preinstaladas, healthcheck | M |
| F2-04 | CLI mínima: `sqlviz servir` como entrypoint (host y puerto por variables) y alias compatible `sqlviz RUTA` | S |
| F2-05 | Admin inicial sin terminal: variable de entorno o primer acceso web | S |
| F2-06 | Acceso por red: HTTPS opcional en compose y frontend sin dependencia de contexto seguro | S |
| — | **tag `v0.5.0a1`** | |
| F2-07 | Repositorios y servicios reciben una conexión de estado (H1a, sin cambio de formato) | M |
| F2-08 | Carga y validación de `sqlviz.yaml` con errores precisos | M |
| F2-09 | Proyecto carpeta: `.sqlviz/estado.duckdb` con migraciones; credencial, enlaces, borradores, tableros, carpetas y paneles en el estado | M |
| F2-10 | Modo legado `.sqlviz`: misma suite en ambos modos | S |
| — | **tag `v0.5.0a2`** | |

Cierre: con `docker compose up`, un proyecto carpeta nuevo y uno `.sqlviz`
existente abren, inician sesión, comparten y guardan borradores igual que antes,
también desde otro equipo de la red. Sesiones en memoria;
`brain.duckdb` sin cambios.

## F3 — Almacén analítico y conexiones (H2 + H3) → `v0.6.0a1`, `a2` · Alpha

Objetivo: los tableros consultan el almacén directamente, sin copia previa.

| ID | Entregable tentativo | Tam. |
| --- | --- | --- |
| F3-01 | `almacen.duckdb` con instancia única dueña (opción A) y presupuestos de instancia | M |
| F3-02 | Política de sentencias ampliada (`DETACH`, `ATTACH`, `SET`, `COPY`, `EXPORT`, `PRAGMA`, funciones de escritura) y pruebas negativas | M |
| F3-03 | `QueryService` con consulta directa en modo carpeta y referencias `base.esquema.tabla`; el legado conserva la copia | M |
| F3-04 | Aceptación: tablero sobre 1 M de filas sin copia; no ve el estado ni escribe | S |
| — | **tag `v0.6.0a1`** | |
| F3-05 | `conexiones/*.yaml`, `.env` y `${VARIABLE}`; literal sensible = error de carga | M |
| F3-06 | `ATTACH` generado para DuckDB y SQLite; secretos temporales; reapertura controlada al cambiar conexiones | M |
| F3-07 | PostgreSQL y DuckLake de solo lectura como integración opcional en CI | M |
| F3-08 | `--data-dir` expresado como conexión de tipo archivo y deprecado | S |
| — | **tag `v0.6.0a2`** | |

Cierre: una fuente SQLite (y PostgreSQL opcional) consultable en solo lectura;
la consulta analítica no ve estado, secretos ni archivos no autorizados.

## F4 — ETL núcleo (H4 + H5) → `v0.7.0a1`, `a2` · Alpha

Objetivo: paquete `sqlviz-transform` con plan/aplicar, incremental y auditorías.

| ID | Entregable tentativo | Tam. |
| --- | --- | --- |
| F4-01 | Paquete `sqlviz-transform` y parser del bloque `MODELO` (errores con línea y columna) | M |
| F4-02 | Tipos `vista`, `tabla`, `semilla` con ejecución transaccional | M |
| F4-03 | DAG con sqlglot y huella de modelo (independiente de `fingerprint.py`) | M |
| F4-04 | Tablas `etl_*` en el estado, registro de ejecuciones y bloqueo de `aplicar` | M |
| F4-05 | `plan` / `aplicar` con huella del plan (409 si cambió) | M |
| F4-06 | API `/etl` y CLI `plan`/`aplicar` como cliente fino de la API (token de operador; uso con `docker compose exec` o tareas programadas) | M |
| — | **tag `v0.7.0a1`** | |
| F4-07 | Incremental por intervalos: grano, zona horaria, `inicio`, `reprocesar_ultimos`, `--desde/--hasta` | M |
| F4-08 | Auditorías bloqueantes dentro de la transacción | M |
| F4-09 | Recuperación entre `COMMIT` de datos y registro; aceptación con 60 meses sintéticos | M |
| — | **tag `v0.7.0a2`** | |

Cierre: cambiar un modelo replanifica solo ese modelo y sus dependientes;
aplicar dos veces no cambia nada; una auditoría fallida deja el intervalo previo intacto.

## F5 — Lienzo (S1.2 + S1.3 + S2) → `v0.8.0a1`, `a2` · Alpha

Objetivo: composición manual persistida y gestos, guardada en el almacén de estado.

| ID | Entregable tentativo | Tam. |
| --- | --- | --- |
| F5-01 (#11) | Contrato del documento de layout versionado | S |
| F5-02 (#12) | Migración de alturas legacy al documento de layout | M |
| F5-03 (#13) | Repositorio transaccional de layout con revisión | M |
| F5-04 (#14) | Endpoints de layout (admin escribe, viewer lee) | S |
| F5-05 (#15) | UI de posición, columnas y alto sin re-ejecutar SQL | M |
| F5-06 (#16) | E2E editar → guardar → reabrir → compartir | S |
| — | **tag `v0.8.0a1`** | |
| F5-07 | S1.3: bloques de texto tipados, edición y publicación | M |
| F5-08 | S2.1–S2.3: drag y resize con guías, preview y mínimos | M |
| F5-09 | S2.4–S2.5: teclado, clic/tap, undo/redo y bloqueo | M |
| F5-10 | S2.6: guardar → recargar → viewer sin ejecutar SQL al mover | S |
| — | **tag `v0.8.0a2`** | |

## F6 — Dataset y primer recorrido (S3 + S4 + M1–M5 + R1–R3) → `v0.9.0a1` → **`v0.9.0b1`** · Primera Beta

Objetivo: datasets reutilizables sobre el almacén y los tres niveles de autoría.

| ID | Entregable tentativo | Tam. |
| --- | --- | --- |
| F6-01 | S3.1–S3.2: dataset con revisión sobre relaciones del almacén; campos y bindings con identidad | M |
| F6-02 | S3.3–S3.4: visual separado del panel; un dataset alimenta dos visuales | M |
| F6-03 | S3.5 + R2a: promoción desde el editor y biblioteca inicial | M |
| F6-04 | M1 + R3a: contrato de matriz, grano y medidas | M |
| — | **tag `v0.9.0a1`** | |
| F6-05 | S4.1: nivel Automático completo para el corpus inicial | M |
| F6-06 | S4.2–S4.3: Visual Builder y compilación a ECharts | M |
| F6-07 | S4.4: editor de opciones nativas ECharts con precedencia | M |
| F6-08 | M2–M5 + R3b–c: motor de medidas, grilla y builder de matriz | M |
| F6-09 | S4.5: E2E builder → guardar → filtrar → reabrir → viewer → reset | M |
| — | **tag `v0.9.0b1`** (primera Beta) | |

## F7 — UI de datos (H6 + H7) → `v0.10.0b1` · Beta

| ID | Entregable tentativo | Tam. |
| --- | --- | --- |
| F7-01 | Grilla virtualizada compartida (también la usará la matriz M7) | M |
| F7-02 | ETL: lista de modelos y detalle con línea de tiempo de intervalos | M |
| F7-03 | ETL: grafo de dependencias (evaluar Drawflow con disposición por capas) | M |
| F7-04 | ETL: plan, aplicar con confirmación y ejecuciones en vivo | M |
| F7-05 | Explorador: catálogo de bases adjuntas y detalle de tabla con perfil | M |
| F7-06 | Explorador: consola SQL de solo lectura y «abrir como tablero» | M |
| F7-07 | Vista de estado para el admin | S |

## F8 — Programación y migración (H8 + H9) → `v0.11.0b1` · Beta

| ID | Entregable tentativo | Tam. |
| --- | --- | --- |
| F8-01 | Programación `diaria`/`mensual` en el servidor, con puesta al día al arrancar | M |
| F8-02 | Programación visible en la UI del ETL | S |
| F8-03 | Migración `.sqlviz` → carpeta (desde la web y `sqlviz exportar`), ensayada sobre copias | M |
| F8-04 | Retirar el modo legado tras migración probada | M |

## F9 — Inferencia y renderizado (S5 + M6–M7) → `v0.12.0b1`, `b2` · Beta

| ID | Entregable tentativo | Tam. |
| --- | --- | --- |
| F9-01 | Corpus de evaluación independiente con métrica en CI | M |
| F9-02 | Fechas, granularidad y unidades | M |
| F9-03 | Nulos y datos vacíos | S |
| — | **tag `v0.12.0b1`** | |
| F9-04 | Familias ECharts, lote 1 (heatmap, scatter, combinado) | M |
| F9-05 | Familias ECharts, lote 2 (treemap, funnel, gauge) | M |
| F9-06 | Formato numérico/semántico | M |
| F9-07 | Escala de la matriz con la grilla virtualizada | M |

## F10 — Pantalla y áreas (S6) → `v0.13.0b1` · Beta

| ID | Entregable tentativo | Tam. |
| --- | --- | --- |
| F10-01 | Usar la altura disponible sin recortar | M |
| F10-02 | Mínimos medidos por visual y fallback explicado | S |
| F10-03 | Secciones/áreas del dashboard | M |
| F10-04 | Lectura responsive preservando el escritorio | M |

## F11 — Interacciones del lector (S7 + M8) → `v0.14.0b1` · Beta

| ID | Entregable tentativo | Tam. |
| --- | --- | --- |
| F11-01 | Filtros versionados con alcance | M |
| F11-02 | Crossfilter visible y reversible | M |
| F11-03 | Drill autorizado por rol | M |
| F11-04 | Cancelación efectiva de SQL en DuckDB | M |
| F11-05 | Contexto preservado al navegar entre dashboards | S |

## F12 — Publicación (S8 + M9 + R4) → `v0.15.0b1` · Beta

| ID | Entregable tentativo | Tam. |
| --- | --- | --- |
| F12-01 | Revisión publicada estable separada del borrador | M |
| F12-02 | Preview fiel | S |
| F12-03 | Exportaciones autorizadas (PNG/CSV) | M |
| F12-04 | R4: tableros y visuales exportables junto al proyecto como código | M |
| F12-05 | Estados vacío/error/carga homogéneos | S |

## F13 — Endurecimiento → **`v0.16.0b1`** · Beta (fin de este roadmap)

| ID | Entregable tentativo | Tam. |
| --- | --- | --- |
| F13-01 | Contratos candidatos a 1.0 congelados con golden tests | M |
| F13-02 | Matriz negativa de seguridad/autorización, incluida la política de sentencias | M |
| F13-03 | Accesibilidad WCAG AA en flujos clave | M |
| F13-04 | Presupuesto de rendimiento y benchmarks en CI (almacén y ETL incluidos) | M |
| F13-05 | Migraciones probadas desde v0.2.11 hasta la beta | M |
| F13-06 | Documentación de usuario e instalación con Docker (respaldo y restauración del volumen, actualización de versión) | M |
| F13-07 | Pruebas con usuarios y triage | M |
| F13-08 | Imagen de despliegue endurecida: tamaño, escaneo de vulnerabilidades, límites de recursos | M |

## Después de la Beta (roadmap de pulido, por planificar)

Al terminar F13 SQLviz sigue en **beta**. Un roadmap posterior repasa cada fase
de nuevo solo con correcciones, rendimiento, accesibilidad y documentación:
`v1.0.0rc1`, `rc2`… hasta `v1.0.0` estable sin bloqueantes.

Quedan para después de la estable o según necesidad: despliegue en la nube,
aprendizaje de patrones
(`brain.duckdb`), tableros como archivos, capa de métricas, DuckLake como
destino de escritura, Quack para clientes externos, alertas (R6), API analítica
pública (R7) y las capacidades ETL marcadas como posteriores en la propuesta.
