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
- **Se retira el modo demo en memoria** (también decisión del usuario): no
  persiste almacén ni ETL y desactiva la autenticación. Lo sustituye un
  **proyecto de ejemplo** con datos sintéticos, persistente y con login normal.

## Dashboards sin SQL

**Decisión del usuario — 2026-10-25:** el usuario ya no escribe SQL en el
dashboard. El SQL vive en los modelos del ETL (`modelos/*.sql`) y las métricas y
dimensiones en el modelo semántico (YAML Apache Ossie). Un panel se construye
eligiendo métricas, dimensiones y filtros; el motor semántico lo traduce a SQL.

- **Se elimina el editor SQL del dashboard**, también en proyectos legados:
  Run, multiconsulta, reconciliación de identidad, borrador y autoguardado del
  script (S1.1). Los dashboards `.sqlviz` existentes quedan de solo lectura hasta
  su migración a modelos en F8. Es un cambio incompatible.
- **La inferencia cambia de papel:** el análisis de SQL arbitrario (S5.1a–c: AST,
  ámbitos, linaje) sale del roadmap. El nivel Automático propone el gráfico a
  partir de los roles que declara el modelo semántico (métrica, dimensión,
  tiempo, unidad) y de la forma del resultado.
- **El editor pasa al proyecto como código:** la web edita los archivos del
  proyecto con Monaco: `modelos/*.sql` (SQL con bloque `MODELO`), `semantica/*.yaml`
  (Ossie, validado con su JSON Schema) y `conexiones/*.yaml` (sin mostrar ni
  guardar valores de secretos). Se reutilizan Monaco y el patrón de guardado
  condicionado por revisión con conflicto visible de #8/#9: un archivo cambiado
  en disco o por Git no se sobrescribe en silencio. En Docker es la forma normal
  de editar, sin entrar al volumen.
- La consulta libre de solo lectura sigue disponible en la consola del explorador (F7).

## Motor semántico

**Decisión del usuario — 2026-10-25:** el motor semántico es un **traductor**,
no un motor de cálculo. Lee modelos semánticos en formato
[Apache Ossie](https://github.com/apache/ossie) (antes Open Semantic
Interchange) y genera SQL en dialecto **DuckDB**; el cálculo lo ejecuta siempre
el motor de la base sobre los datos del almacén, a través de `QueryService` y
sus presupuestos. No guarda datos, no cachea agregados y no tiene un segundo
camino de ejecución. Otros dialectos se consideran después.

Los modelos Ossie viven en el proyecto como código (`semantica/*.yaml`) y sus
datasets apuntan a relaciones del almacén producidas por el ETL. Ossie está en
incubación y su núcleo es un borrador (`0.2.0.dev0`, que pide no usarlo aún en
producción): se fija una versión, se valida con su JSON Schema y lo que la
especificación no cubre (grano, aditividad, unidades, formato) va en
`custom_extensions` de SQLviz.

## Cambio de nombre del producto

**Decisión del usuario — 2026-10-25:** «SQLviz» se reemplaza en **todo** el
código y el repositorio, primero por el nombre provisional genérico **`nexobi`**
y más adelante por el definitivo (candidato: *Kipu*), elegido antes de la
primera Beta. El segundo cambio es mecánico porque `nexobi` es un término único. Medido
el 2026-10-25: 3 232 menciones en 349 archivos y 610 rutas (paquetes
`sqlviz-*`, imports `sqlviz_*`, comando `sqlviz`, variables `SQLVIZ_*`, tablas
`_sqlviz_*`, formato `.sqlviz`, documentación y nombre del repositorio).

Se hace **al inicio de F2**, después de eliminar el editor SQL y antes de crear nombres nuevos (imagen Docker,
`sqlviz.yaml`, carpeta `.sqlviz/`, subcomandos); hacerlo después multiplica lo
que hay que renombrar y mantener compatible. Requisitos:

- `nexobi` está libre en PyPI (verificado el 2026-10-25). El definitivo se
  verifica en PyPI, registro de imágenes, GitHub, dominio y marca.
- Por partes revisables (F2-00a–d), con la suite verde en cada PR.
- Compatibilidad: los proyectos `.sqlviz` existentes siguen abriendo en modo
  legado (firma `_sqlviz_meta` incluida) hasta la migración de F8; las variables
  `SQLVIZ_*` se aceptan con aviso de deprecación durante un ciclo.
- El historial (CHANGELOG, tags y releases anteriores) no se reescribe.

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

| Fase | Paraguas | Contenido | Hitos de origen | Versión | Etapa |
| --- | --- | --- | --- | --- | --- |
| F0 | — | Consolidación | — | `v0.3.0` | Cerrada |
| F1 | — | Borrador y archivos locales | S1.1c.2c.3, #19 | `v0.4.0a1` | Alpha |
| F2 | #23 | Base de proyecto | H0, H1 | `v0.5.0a1`, `a2` | Alpha |
| F3 | #24 | Almacén analítico y conexiones | H2, H3 | `v0.6.0a1`, `a2` | Alpha |
| F4 | #25 | ETL núcleo | H4, H5 | `v0.7.0a1`, `a2` | Alpha |
| F5 | #26 | Semántica y builder | Ossie, R2a, Automático | `v0.8.0a1`, `a2` | Alpha |
| F6 | #27 | Lienzo y primer recorrido | S1.2, S1.3, S2, S4.4, M1–M5 | `v0.9.0a1`, `a2` → **`v0.9.0b1`** | **Primera Beta** |
| F7 | #28 | UI de datos | H6, H7 | `v0.10.0b1` | Beta |
| F8 | #29 | Programación y migración | H8, H9 | `v0.11.0b1` | Beta |
| F9 | #30 | Automático y renderizado | S5 (sin S5.1), M6–M7 | `v0.12.0b1`, `b2` | Beta |
| F10 | #31 | Pantalla y áreas | S6 | `v0.13.0b1` | Beta |
| F11 | #32 | Interacciones del lector | S7, M8 | `v0.14.0b1` | Beta |
| F12 | #33 | Publicación | S8, M9, R4 | `v0.15.0b1` | Beta |
| F13 | #34 | Endurecimiento | — | `v0.16.0b1` | Beta (fin) |

Dependencias principales: F2 → F3 → F4 → F5 → F6 (la semántica se apoya en
tablas del almacén producidas por el ETL; el lienzo necesita paneles creados
con el builder); F4 → F7 y F8. Ver el [orden unificado](sqlviz-almacen-etl-integracion-propuesta.md#orden-unificado-de-trabajo).

## F0 — Consolidación → `v0.3.0` · Cerrada

| ID | Issue | Tam. |
| --- | --- | --- |
| F0-01 (#1) | Registrar roadmap de releases y milestones | S |
| F0-02 (#2) | Limpiar artefactos de la raíz y `.gitignore` | S |
| F0-03 (#3) | Plantillas de issue/PR | S |
| F0-04 (#4) | Verificar CHANGELOG `Unreleased` | S |
| F0-05 (#5) | CI obligatoria en PRs a `main` | S |
| F0-06 (#6) | Merge de `feat/sqlviz-foundations` → `main` y tag `v0.3.0` | M |

## F1 — Borrador y archivos locales → `v0.4.0a1` · Alpha

Reducida el 2026-10-25: el layout (#11–#16) pasa a F6 y #10 se cancela porque
el editor SQL del dashboard se elimina. `v0.4.0a1` es el **último release con
editor SQL**.

| ID | Issue | Tam. |
| --- | --- | --- |
| F1-01 (#8) | S1.1c.2c.3b: API tipada/autorizada de borrador y revisión | M |
| F1-02 (#9) | 3c: autoguardado web con revisión confirmada y conflicto visible | M |
| ~~F1-03 (#10)~~ | ~~3d: recuperación de respuesta perdida~~ (cancelado) | — |
| F1-10 (#19) | Leer archivos locales de carpetas autorizadas (`--data-dir`) | S |

Cierre: PR #20 fusionado → `v0.4.0a1`.

## F2 — Base de proyecto (H0 + H1) → `v0.5.0a1`, `a2` · Alpha

Objetivo: decidir y preparar la base. DuckDB 2.0.0, proyecto como carpeta y
almacén de estado, con el modo `.sqlviz` legado funcionando.

| ID | Entregable tentativo | Tam. |
| --- | --- | --- |
| F2-00a | Eliminar el editor SQL del dashboard en la web: Run, multiconsulta, diálogo de identidad y autoguardado del script; se conservan Monaco y el patrón de guardado con revisión para el editor de archivos; los dashboards legados quedan de solo lectura | M |
| F2-00b | Eliminar sus APIs y almacenamiento: `/sql/parse`, `/sql/reconcile`, `/sql-script/*`, recibos de Run y escritores de script/borrador; las tablas se conservan para leer legados | M |
| F2-00c | Renombrar a `nexobi`: paquetes, imports y metadatos de build; suite verde | M |
| F2-00d | Renombrar CLI, variables de entorno (alias `SQLVIZ_*` deprecados), textos de UI y firma de proyectos nuevos; legado `.sqlviz` sigue abriendo | M |
| F2-00e | Renombrar documentación, README y repositorio de GitHub (las URLs antiguas redirigen) | S |
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
| F2-11 | Retirar el modo demo en memoria y su bypass de autenticación; sin proyecto, el contenedor crea uno vacío en el volumen | M |
| — | **tag `v0.5.0a2`** | |

Cierre: con `docker compose up`, un proyecto carpeta nuevo y uno `.sqlviz`
existente abren, inician sesión y comparten; los dashboards legados se ven en
solo lectura, también desde otro equipo de la red. Sesiones en memoria;
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
| F3-09 | API de archivos del proyecto: leer/escribir solo bajo `modelos/`, `semantica/`, `conexiones/` y `semillas/`; rutas validadas, revisión por hash y 409 ante cambio externo | M |
| F3-10 | Editor de conexiones en la web: validación del YAML, referencias `${VARIABLE}` y prueba de conexión; nunca muestra ni guarda secretos | M |
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
| F4-10 | Proyecto de ejemplo: semillas CSV y modelos sintéticos (clientes y lecturas) que se cargan con `aplicar`; sirve de onboarding y de datos para E2E | M |
| F4-11 | Editor de modelos en la web: árbol de `modelos/`, Monaco SQL, errores del bloque `MODELO` como marcadores con línea y columna, guardado con revisión y `plan` del cambio antes de aplicar | M |
| — | **tag `v0.7.0a2`** | |

Cierre: cambiar un modelo replanifica solo ese modelo y sus dependientes;
aplicar dos veces no cambia nada; una auditoría fallida deja el intervalo previo intacto.

## F5 — Semántica y builder → `v0.8.0a1`, `a2` · Alpha

Objetivo: crear paneles sin SQL, eligiendo métricas y dimensiones del modelo
semántico sobre el almacén. Es la primera forma de autoría tras eliminar el editor.

| ID | Entregable tentativo | Tam. |
| --- | --- | --- |
| F5-01 | Modelo semántico en formato **Apache Ossie** (versión fijada): `semantica/*.yaml` validado con su JSON Schema; extensiones propias en `custom_extensions` | M |
| F5-02 | Compilador semántico Ossie → SQL dialecto DuckDB con sqlglot: campos, métricas, relaciones many-to-one y filtros parametrizados. **No ejecuta**: entrega SQL a `QueryService` | M |
| F5-03 | Visual con revisión = métricas + dimensiones + filtros sobre el modelo; el panel referencia el visual | M |
| F5-04 | Builder mínimo: crear un panel eligiendo métricas, dimensiones y tipo de gráfico | M |
| F5-05 | Editor de semántica en la web: Monaco YAML con validación y autocompletado por el JSON Schema de Ossie, y vista previa del SQL que genera el compilador | M |
| — | **tag `v0.8.0a1`** | |
| F5-06 | Nivel Automático por roles semánticos (tiempo → línea, categoría → barras, métrica sola → KPI) y forma del resultado | M |
| F5-07 | Biblioteca inicial (R2a): modelos semánticos, visuales y tableros con búsqueda | M |
| F5-08 | E2E: modelo ETL → semántica → panel sin SQL → viewer | S |
| — | **tag `v0.8.0a2`** | |

Cierre: un usuario crea un dashboard sin escribir SQL sobre datos del almacén.

## F6 — Lienzo y primer recorrido → `v0.9.0a1`, `a2` → **`v0.9.0b1`** · Primera Beta

Objetivo: composición manual, ajuste experto y matriz sobre los paneles del builder.

| ID | Entregable tentativo | Tam. |
| --- | --- | --- |
| F6-01 (#11) | Contrato del documento de layout versionado | S |
| F6-02 (#12) | Migración de alturas legacy al documento de layout | M |
| F6-03 (#13) | Repositorio transaccional de layout con revisión | M |
| F6-04 (#14) | Endpoints de layout (admin escribe, viewer lee) | S |
| F6-05 (#15) | UI de posición, columnas y alto sin re-ejecutar consultas | M |
| F6-06 (#16) | E2E editar → guardar → reabrir → compartir | S |
| — | **tag `v0.9.0a1`** | |
| F6-07 | S1.3: bloques de texto tipados, edición y publicación | M |
| F6-08 | S2.1–S2.3: drag y resize con guías, preview y mínimos | M |
| F6-09 | S2.4–S2.6: teclado, clic/tap, undo/redo, bloqueo; mover no ejecuta consultas | M |
| F6-10 | S4.4: editor de opciones nativas ECharts con precedencia | M |
| — | **tag `v0.9.0a2`** | |
| F6-11 | M1–M3 + R3: contrato de matriz y medidas por contexto compiladas a SQL | M |
| F6-12 | M4–M5: grilla y builder de matriz con drag de campos | M |
| F6-13 | E2E builder → guardar → filtrar → reabrir → viewer → reset | M |
| — | **tag `v0.9.0b1`** (primera Beta) | |

Cierre: un usuario crea, compone, filtra, reabre y comparte un dashboard sin
tocar código → **primera Beta**.

## F7 — UI de datos (H6 + H7) → `v0.10.0b1` · Beta

| ID | Entregable tentativo | Tam. |
| --- | --- | --- |
| F7-01 | Grilla virtualizada compartida (también la usará la matriz M7) | M |
| F7-02 | ETL: lista de modelos y detalle (editor de F4-11, dependencias, auditorías) con línea de tiempo de intervalos | M |
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
| F8-03 | Migración `.sqlviz` → carpeta: cada panel SQL legado pasa a un modelo `vista` y un visual semántico; desde la web y `exportar`, ensayada sobre copias | M |
| F8-04 | Retirar el modo legado tras migración probada | M |

## F9 — Automático y renderizado (S5 sin S5.1 + M6–M7) → `v0.12.0b1`, `b2` · Beta

| ID | Entregable tentativo | Tam. |
| --- | --- | --- |
| F9-01 | Corpus de evaluación del nivel Automático semántico con métrica en CI | M |
| F9-02 | Fechas, granularidad y unidades desde el modelo semántico | M |
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
