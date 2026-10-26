# Roadmap de releases: v0.2.11 → Alpha completa (v0.16.0a)

**Creado:** 2026-10-17. **Revisado:** 2026-10-25: corte de versiones (todo este
roadmap es alpha), módulos con interfaz propia y reordenamiento por la
[integración de almacén, estado y ELT](sqlviz-almacen-etl-integracion-propuesta.md).
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
  su migración a modelos en F13. Es un cambio incompatible.
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
- La consulta libre de solo lectura sigue disponible en la consola del explorador (F4).

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
primera beta. El segundo cambio es mecánico porque `nexobi` es un término único. Medido
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

## Corte del 2026-10-25

El nuevo rumbo (proyecto como código, almacén, ELT, semántica, tableros sin SQL
y despliegue en Docker) cambia el producto. Se hace un **corte**:

- `v0.3.0` y `v0.4.0a1` cierran la etapa SQLviz. `v0.4.0a1` es el último
  release con editor SQL en el dashboard.
- Desde F2 se renumeran las versiones y **todo este roadmap es Alpha**. Al
  terminarlo, la alpha queda **completa** (`v0.16.0aN`).
- Las betas llegan en el roadmap siguiente, ya con el producto usable, y la
  última beta es casi final antes de la versión estable.

## Política de versiones

SQLviz no es apto para producción hasta `v1.0.0`. La madurez se lee en el
sufijo del tag, y **todos los releases anteriores a `v1.0.0` se publican como
pre-release**: `pip install` no los instala sin `--pre`.

| Etapa | Cuándo | Tags (PEP 440, hatch-vcs) | Significado |
| --- | --- | --- | --- |
| **Alpha** | Este roadmap, F1–F13 | `v0.N.0a1`, `v0.N.0a2`… | En construcción: cada fase añade capacidades; contratos y datos pueden romperse con migración |
| **Beta** | Roadmap siguiente | `v1.0.0b1`, `b2`… | Usable de punta a punta; mejoras, pulido y correcciones. La última beta es casi final |
| RC | Después de las betas | `v1.0.0rc1`… | Solo correcciones; sin funcionalidad nueva |
| **Estable** | Al final | `v1.0.0` | Lista para producción |

Reglas:

- **Una fase = un minor** (`0.5`, `0.6`…), con tags solo alpha (`a1`, `a2`…).
  La fase se cierra con su último alpha; no se publica `v0.N.0` sin sufijo.
- **Correcciones** sobre una fase ya cerrada: siguiente número alpha del mismo
  minor (`v0.7.0a3`).
- **Fin de este roadmap:** `v0.16.0aN`, **alpha completa**.

**Tamaños:** S = 1–2 días, un PR, una capa. M = 3–5 días, un PR, puede cruzar
capas. Un issue mayor que M se divide antes de empezar.

**Flujo:** issue → rama `<tipo>/F<n>-<nn>-<slug>` desde `main` → PR con
`Closes #N` → CI verde → merge → al alcanzar un hito: CHANGELOG + tag + release.

## Módulos y experiencia de uso

**Decisión del usuario — 2026-10-25:** la herramienta debe sentirse moderna y de
nivel mundial, pero **minimalista y fácil de usar**. Cada área de trabajo tiene
su propia interfaz dentro de una sola aplicación:

| Módulo | Para qué | Fase |
| --- | --- | --- |
| **Conexiones** | Declarar fuentes y bases adjuntas, probar la conexión; nunca muestra secretos | F4 |
| **Explorador de datos** | Catálogo de bases → esquemas → tablas, vista de datos, perfil y consola de solo lectura | F4 |
| **Modelos (ELT)** | Editar modelos, ver el grafo, planificar, aplicar, intervalos, auditorías, ejecuciones y programación | F5–F6 |
| **Semántica** | Editar modelos Apache Ossie, explorar métricas y dimensiones, probar consultas y ver el SQL generado | F7–F8 |
| **Tableros** | Construir dashboards sin SQL, componer el lienzo y publicarlos; vista del lector | F9–F12 |
| **Administración** | Estado del proyecto, enlaces compartidos, sesiones, almacenes y ajustes | F3 (base), F13 |

Principios comunes:

- **Un solo shell**: navegación por módulos siempre en el mismo lugar, ocultable;
  paleta de comandos (`Ctrl+K`) y búsqueda global sobre todos los recursos.
- **Minimalismo funcional**: un color de acento, mucha jerarquía tipográfica y
  poco ornamento; densidad de herramienta profesional donde hay datos.
- **Revelación progresiva**: lo frecuente a la vista, lo avanzado bajo demanda.
- **Estados completos** en cada vista: carga, vacío con la siguiente acción,
  error útil con reintento y sin permisos.
- **Teclado y accesibilidad** (WCAG AA), temas claro y oscuro, responsive.
- **Rapidez percibida**: grillas virtualizadas, paginación en servidor y nada
  de cargar tablas completas en el navegador.
- **Un mismo sistema de diseño** (tokens de `app.css`, Tailwind, bits-ui, Geist,
  Lucide) en todos los módulos; ningún módulo inventa su propio estilo.

**Inversión:** el ELT y el motor semántico son lo nuevo, y por eso reciben más
fases (F5–F8) que cualquier otra área.

## Vista general

| Fase | Paraguas | Contenido | Versión |
| --- | --- | --- | --- |
| F0 | — | Consolidación | `v0.3.0` (cerrada) |
| F1 | — | Borrador y archivos locales (último SQLviz) | `v0.4.0a1` |
| F2 | #23 | Base de proyecto | `v0.5.0a1`, `a2` |
| F3 | #24 | Aplicación modular y sistema de diseño | `v0.6.0a1`, `a2` |
| F4 | #25 | Almacén, conexiones y explorador de datos | `v0.7.0a1`, `a2` |
| F5 | #26 | ELT núcleo y su interfaz | `v0.8.0a1`, `a2` |
| F6 | #27 | ELT incremental, auditorías y programación | `v0.9.0a1`, `a2` |
| F7 | #28 | Motor semántico y su interfaz | `v0.10.0a1`, `a2` |
| F8 | #29 | Semántica avanzada | `v0.11.0a1`, `a2` |
| F9 | #30 | Tableros sin SQL | `v0.12.0a1`, `a2` |
| F10 | #31 | Lienzo | `v0.13.0a1`, `a2` |
| F11 | #32 | Matriz y visualizaciones | `v0.14.0a1`, `a2` |
| F12 | #33 | Experiencia del lector y publicación | `v0.15.0a1`, `a2` |
| F13 | #34 | Migración y cierre de la alpha | **`v0.16.0a1`: alpha completa** |

Dependencias: F2 → F3 → F4 → F5 → F6; F4 → F7 → F8 → F9 → F10 → F11 → F12 → F13.
F6 y F7 pueden intercalarse si conviene.

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

Último release de la etapa SQLviz y con editor SQL en el dashboard.

| ID | Issue | Tam. |
| --- | --- | --- |
| F1-01 (#8) | S1.1c.2c.3b: API tipada/autorizada de borrador y revisión | M |
| F1-02 (#9) | 3c: autoguardado web con revisión confirmada y conflicto visible | M |
| ~~F1-03 (#10)~~ | ~~3d: recuperación de respuesta perdida~~ (cancelado) | — |
| F1-10 (#19) | Leer archivos locales de carpetas autorizadas (`--data-dir`) | S |

Cierre: PR #20 fusionado → `v0.4.0a1`.

## F2 — Base de proyecto → `v0.5.0a1`, `a2` · Alpha

Objetivo: retirar lo que ya no encaja, renombrar y preparar la base: DuckDB 2.0.0,
Docker, proyecto como carpeta y almacén de estado, con el legado `.sqlviz` abriendo.

| ID | Entregable tentativo | Tam. |
| --- | --- | --- |
| F2-01 | Eliminar el editor SQL del dashboard en la web (Run, multiconsulta, diálogo de identidad, autoguardado del script); se conservan Monaco y el patrón de guardado con revisión; legados en solo lectura | M |
| F2-02 | Eliminar sus APIs y almacenamiento (`/sql/parse`, `/sql/reconcile`, `/sql-script/*`, recibos de Run, escritores de script); las tablas se conservan para leer legados | M |
| F2-03 | Renombrar a `nexobi`: paquetes, imports y metadatos de build | M |
| F2-04 | Renombrar CLI, variables de entorno (alias `SQLVIZ_*` deprecados), textos de UI y firma de proyectos nuevos | M |
| F2-05 | Renombrar documentación, README y repositorio de GitHub | S |
| F2-06 | DuckDB 2.0.0: lockfile, suite verde, copia previa obligatoria al abrir proyectos de 1.5.x | M |
| — | **tag `v0.5.0a1`** | |
| F2-07 | Imagen Docker y `docker compose`: usuario no root, volumen, `.env`, extensiones preinstaladas, healthcheck | M |
| F2-08 | CLI mínima: `servir` como entrypoint y alias compatible con la ruta del proyecto | S |
| F2-09 | Admin inicial sin terminal (variable de entorno o primer acceso web) | S |
| F2-10 | Acceso por red: HTTPS opcional y frontend sin dependencia de contexto seguro | S |
| F2-11 | Repositorios y servicios reciben una conexión de estado (sin cambio de formato) | M |
| F2-12 | `nexobi.yaml` del proyecto: carga y validación con errores precisos | M |
| F2-13 | Proyecto carpeta: `estado.duckdb` con migraciones; credencial, enlaces, tableros, carpetas y paneles en el estado | M |
| F2-14 | Modo legado `.sqlviz` con la misma suite; retirar el modo demo en memoria | M |
| F2-15 | Documento de decisión y actualización de los documentos listados en la propuesta | M |
| — | **tag `v0.5.0a2`** | |

Cierre: con `docker compose up`, un proyecto nuevo y uno `.sqlviz` existente
abren, inician sesión y comparten, también desde otro equipo de la red.

## F3 — Aplicación modular y sistema de diseño → `v0.6.0a1`, `a2` · Alpha

Objetivo: el esqueleto común de una herramienta moderna y minimalista sobre el
que crecen todos los módulos.

| ID | Entregable tentativo | Tam. |
| --- | --- | --- |
| F3-01 | Especificación de UX: módulos, navegación, principios, estados y atajos, con prototipo navegable | M |
| F3-02 | Shell de la aplicación: navegación por módulos con rutas, ocultable y responsive | M |
| F3-03 | Componentes base: tabla compacta, estados (carga, vacío, error, sin permisos), toasts, confirmaciones, formatos de número y fecha | M |
| F3-04 | Paleta de comandos y búsqueda global para todos los módulos | S |
| — | **tag `v0.6.0a1`** | |
| F3-05 | Grilla virtualizada compartida con paginación desde el servidor | M |
| F3-06 | API de archivos del proyecto: solo `modelos/`, `semantica/`, `conexiones/`, `semillas/`; revisión por hash y 409 ante cambio externo | M |
| F3-07 | Editor de archivos común: Monaco con guardado condicionado, conflicto visible y marcadores de error | M |
| F3-08 | Administración básica: estado del proyecto, enlaces compartidos y sesiones (solo lectura y revocar) | S |
| — | **tag `v0.6.0a2`** | |

Cierre: el shell navega entre módulos con estados correctos en claro, oscuro y
pantalla estrecha; el editor de archivos guarda con revisión.

## F4 — Almacén, conexiones y explorador de datos → `v0.7.0a1`, `a2` · Alpha

| ID | Entregable tentativo | Tam. |
| --- | --- | --- |
| F4-01 | Almacén con instancia única dueña (opción A) y presupuestos de instancia | M |
| F4-02 | Política de sentencias ampliada (`DETACH`, `ATTACH`, `SET`, `COPY`, `EXPORT`, `PRAGMA`) y pruebas negativas | M |
| F4-03 | `QueryService` con consulta directa y referencias `base.esquema.tabla`; el legado conserva la copia | M |
| F4-04 | Conexiones: YAML, `.env` y `${VARIABLE}`; literal sensible = error | M |
| F4-05 | `ATTACH` generado (DuckDB, SQLite; PostgreSQL y DuckLake opcionales en CI); secretos temporales | M |
| — | **tag `v0.7.0a1`** | |
| F4-06 | UI de Conexiones: lista, editor, prueba de conexión; nunca muestra secretos | M |
| F4-07 | UI del Explorador: catálogo y detalle de tabla (datos, columnas, perfil acotado) | M |
| F4-08 | UI del Explorador: consola SQL de solo lectura con presupuestos e historial de sesión | M |
| F4-09 | `--data-dir` como conexión de tipo archivo; aceptación con una tabla de 1 M de filas | S |
| — | **tag `v0.7.0a2`** | |

Cierre: conectar una fuente, explorarla y consultarla desde la web; la consulta
no ve el estado, los secretos ni archivos no autorizados.

## F5 — ELT núcleo y su interfaz → `v0.8.0a1`, `a2` · Alpha

| ID | Entregable tentativo | Tam. |
| --- | --- | --- |
| F5-01 | Paquete de transformación y parser del bloque `MODELO` (errores con línea y columna) | M |
| F5-02 | Tipos `vista`, `tabla` y `semilla` con ejecución transaccional | M |
| F5-03 | DAG con sqlglot y huella de modelo | M |
| F5-04 | Tablas `etl_*` en el estado, registro de ejecuciones y bloqueo | M |
| F5-05 | `plan` / `aplicar` con huella del plan (409 si cambió); API y CLI como cliente fino | M |
| — | **tag `v0.8.0a1`** | |
| F5-06 | UI de Modelos: lista con filtros y editor con validación en vivo | M |
| F5-07 | UI: grafo de dependencias con estado y resaltado de ascendentes/descendentes | M |
| F5-08 | UI: plan con impacto, aplicar con confirmación y ejecuciones en vivo | M |
| F5-09 | Proyecto de ejemplo: semillas y modelos sintéticos (clientes y lecturas) | M |
| — | **tag `v0.8.0a2`** | |

Cierre: editar un modelo en la web → plan → aplicar → ver la tabla en el
explorador; aplicar dos veces seguidas no cambia nada.

## F6 — ELT incremental, auditorías y programación → `v0.9.0a1`, `a2` · Alpha

| ID | Entregable tentativo | Tam. |
| --- | --- | --- |
| F6-01 | Incremental por intervalos: grano, zona horaria, `inicio` | M |
| F6-02 | Recarga por rango y `reprocesar_ultimos` | M |
| F6-03 | Auditorías bloqueantes dentro de la transacción | M |
| F6-04 | Recuperación entre `COMMIT` de datos y registro; aceptación con 60 meses sintéticos | M |
| — | **tag `v0.9.0a1`** | |
| F6-05 | UI: línea de tiempo de intervalos con huecos y recarga por rango | M |
| F6-06 | UI: auditorías y su resultado, con la consulta que falló | S |
| F6-07 | Programación diaria/mensual en el servidor, con puesta al día al arrancar | M |
| F6-08 | UI de programación y cancelación de ejecuciones | S |
| — | **tag `v0.9.0a2`** | |

## F7 — Motor semántico y su interfaz → `v0.10.0a1`, `a2` · Alpha

| ID | Entregable tentativo | Tam. |
| --- | --- | --- |
| F7-01 | Modelos Apache Ossie (versión fijada) en `semantica/*.yaml`, validados con su JSON Schema; extensiones propias en `custom_extensions` | M |
| F7-02 | Compilador Ossie → SQL DuckDB con sqlglot: campos, métricas y filtros parametrizados; **no ejecuta** | M |
| F7-03 | Relaciones many-to-one con joins seguros, sin doble conteo | M |
| F7-04 | API semántica: métricas + dimensiones + filtros → SQL → `QueryService` | M |
| — | **tag `v0.10.0a1`** | |
| F7-05 | UI de Semántica: navegador de modelos, métricas y dimensiones; editor YAML con autocompletado por schema | M |
| F7-06 | UI: probar una consulta semántica con el SQL generado y el resultado | M |
| F7-07 | Linaje: fuente → modelo ELT → dataset Ossie → métrica | M |
| — | **tag `v0.10.0a2`** | |

## F8 — Semántica avanzada → `v0.11.0a1`, `a2` · Alpha

| ID | Entregable tentativo | Tam. |
| --- | --- | --- |
| F8-01 | Extensiones de grano, aditividad y unidades | M |
| F8-02 | Medidas no aditivas: ratios por componentes, distintos y promedios ponderados | M |
| F8-03 | Tiempo: granularidad, calendario y comparación de periodos | M |
| — | **tag `v0.11.0a1`** | |
| F8-04 | Totales y subtotales por contexto (base de la matriz) | M |
| F8-05 | Corpus de corrección semántica en CI: doble conteo, NULL, denominador cero | M |
| F8-06 | Importar/exportar Ossie con otras herramientas mediante sus convertidores | M |
| — | **tag `v0.11.0a2`** | |

## F9 — Tableros sin SQL → `v0.12.0a1`, `a2` · Alpha

| ID | Entregable tentativo | Tam. |
| --- | --- | --- |
| F9-01 | Visual con revisión = métricas + dimensiones + filtros; el panel referencia el visual | M |
| F9-02 | Builder de tableros sobre la semántica | M |
| F9-03 | Nivel Automático por roles semánticos y forma del resultado | M |
| — | **tag `v0.12.0a1`** | |
| F9-04 | Filtros del tablero sobre dimensiones semánticas | M |
| F9-05 | Biblioteca: modelos, métricas, visuales y tableros | M |
| F9-06 | E2E: modelo ELT → semántica → tablero → lector | S |
| — | **tag `v0.12.0a2`** | |

## F10 — Lienzo → `v0.13.0a1`, `a2` · Alpha

| ID | Entregable tentativo | Tam. |
| --- | --- | --- |
| F10-01 (#11) | Contrato del documento de layout versionado | S |
| F10-02 (#12) | Migración de alturas legacy al documento de layout | M |
| F10-03 (#13) | Repositorio transaccional de layout con revisión | M |
| F10-04 (#14) | Endpoints de layout (admin escribe, viewer lee) | S |
| F10-05 (#15) | UI de posición, columnas y alto sin re-ejecutar consultas | M |
| F10-06 (#16) | E2E editar → guardar → reabrir → compartir | S |
| — | **tag `v0.13.0a1`** | |
| F10-07 | Bloques de texto tipados | M |
| F10-08 | Drag y resize con guías, preview y mínimos | M |
| F10-09 | Teclado, clic/tap, undo/redo y bloqueo; mover no ejecuta consultas | M |
| F10-10 | Editor de opciones nativas ECharts con precedencia | M |
| — | **tag `v0.13.0a2`** | |

## F11 — Matriz y visualizaciones → `v0.14.0a1`, `a2` · Alpha

| ID | Entregable tentativo | Tam. |
| --- | --- | --- |
| F11-01 | Matriz: contrato, grilla y medidas por contexto del motor semántico | M |
| F11-02 | Matriz: builder con drag de campos, filas y columnas | M |
| F11-03 | Matriz: formato y escala con la grilla virtualizada | M |
| — | **tag `v0.14.0a1`** | |
| F11-04 | Familias ECharts, lote 1 (heatmap, scatter, combinado) | M |
| F11-05 | Familias ECharts, lote 2 (treemap, funnel, gauge) | M |
| F11-06 | Formato numérico y semántico desde el modelo (moneda, %, unidades) | M |
| F11-07 | Corpus de evaluación del nivel Automático en CI | M |
| — | **tag `v0.14.0a2`** | |

## F12 — Experiencia del lector y publicación → `v0.15.0a1`, `a2` · Alpha

| ID | Entregable tentativo | Tam. |
| --- | --- | --- |
| F12-01 | Modo pantalla/scroll y mínimos medidos por visual | M |
| F12-02 | Secciones y áreas del dashboard; lectura responsive | M |
| F12-03 | Filtros con alcance, crossfilter y drill autorizado | M |
| F12-04 | Cancelación efectiva de consultas en DuckDB | M |
| — | **tag `v0.15.0a1`** | |
| F12-05 | Revisión publicada separada del borrador y preview fiel | M |
| F12-06 | Exportaciones autorizadas (PNG/CSV) | M |
| F12-07 | Tableros y visuales exportables junto al proyecto como código | M |
| — | **tag `v0.15.0a2`** | |

## F13 — Migración y cierre de la alpha → **`v0.16.0a1`: alpha completa**

| ID | Entregable tentativo | Tam. |
| --- | --- | --- |
| F13-01 | Migración `.sqlviz` → carpeta: cada panel SQL legado pasa a un modelo `vista` y un visual semántico; ensayada sobre copias | M |
| F13-02 | Retirar el modo legado tras la migración probada | M |
| F13-03 | Matriz negativa de seguridad y autorización, incluida la política de sentencias | M |
| F13-04 | Accesibilidad WCAG AA en los flujos clave de cada módulo | M |
| F13-05 | Presupuesto de rendimiento y benchmarks en CI (almacén, ELT y semántica) | M |
| F13-06 | Documentación de usuario e instalación con Docker (respaldo, restauración y actualización) | M |
| F13-07 | Imagen de despliegue endurecida | M |
| F13-08 | Pruebas con usuarios por módulo y triage para el roadmap beta | M |

Cierre: **alpha completa**. Todo el recorrido fuente → ELT → semántica → tablero
→ lector funciona en Docker; lo que falte se planifica en el roadmap beta.

## Después de la alpha (roadmap beta, por planificar)

Betas `v1.0.0b1`, `b2`…: mejoras de cada módulo, pulido y correcciones con el
producto ya usable; la última beta es casi final. Después `v1.0.0rc*` y la
versión estable `v1.0.0`. El nombre definitivo del producto se elige antes de
la primera beta.

Quedan para después de la estable o según necesidad: despliegue en la nube,
aprendizaje de patrones (`brain.duckdb`), tableros como archivos, DuckLake como
destino de escritura, Quack para clientes externos, alertas, API analítica
pública y las capacidades ELT marcadas como posteriores en la propuesta.
