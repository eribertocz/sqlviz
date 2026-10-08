# Auditoría técnica y de producto

**Fecha:** 2026-10-05. **Base revisada:** commit `7f59429`.
**Alcance:** lectura del monorepo, contratos, documentación, CI, ejecución de las
pruebas disponibles y reproducción aislada de autorización. No se hizo una
auditoría visual en navegador, una prueba de carga ni un pentest exhaustivo.
No se abrió ni modificó `test2.sqlviz`.

**Ampliación de esta revisión:** la [evaluación de buenas prácticas](sqlviz-engineering-practices-review.md)
añade cinco ensayos reproducidos de integridad/contratos (BP-01–05) y revisa
dependencias, transacciones y concurrencia. BP-01 está corregido en el quinto
incremento; BP-02 y PATCH de ubicación de BP-05 se corrigen en el sexto.
BP-03 se corrige en el séptimo incremento. BP-04 y PATCH de otros campos siguen
pendientes. La evidencia original se conserva.

La [revisión del Dashboard Studio](sqlviz-dashboard-studio-spec.md) añade evidencia
de ejes sensibles al orden de columnas y métricas omitidas en especificaciones
de línea. El benchmark existente pasa 52 casos, pero no cubre esas garantías de
calidad. La nueva especificación incorpora los requisitos visuales del usuario.

## Dictamen

SQLviz tiene una base útil para un producto enfocado en crear dashboards de alta
calidad rápidamente. Su ventaja potencial es combinar SQL, recomendaciones
explicables y control visual. Obligar a todos los usuarios a escribir SQL reduce
innecesariamente su alcance; prometer inferir siempre la intención de negocio
también excede lo que se puede deducir de una consulta.

La arquitectura actual es adecuada como punto de partida local y de un solo
proceso. No está preparada para exponerse como producto colaborativo confiable:
hay un fallo de autorización reproducido y acoplamiento entre consultas,
metadatos, aprendizaje y presentación. La siguiente etapa debe fortalecer estos
límites y completar la experiencia de autoría. No se justifica una reescritura
del stack ni convertir ahora el producto en una plataforma ETL.

## Fortalezas verificadas

| Elemento | Evidencia | Valor que se conserva |
| --- | --- | --- |
| Monorepo con seis paquetes | `packages/`, workspace de uv | Separación inicial de responsabilidades y despliegue sencillo |
| Inferencia por etapas | `sqlviz_inference/pipeline.py`, reglas YAML | Decisiones trazables, sustitución gradual de componentes |
| Resultados y visualización estructurados | `result.py`, `spec/visual_spec.py`, contratos | Evolucionar el renderer sin acoplarlo al SQL |
| Overrides explícitos | `sqlviz_storage/override_system.py` | Respetar decisiones del autor sobre sugerencias automáticas |
| Editor y viewer diferenciados | rutas Svelte, `PanelPropertiesPanel.svelte` | Base para autoría visual y consumo sin SQL |
| Filtros y parámetros enlazados | `routers/panels.py`, `filters/` | Controles funcionales y binding de valores |
| Pruebas y CI | suites Python/Vitest, `.github/workflows/ci.yml` | Base de regresión considerable, aunque faltan garantías importantes |

## Hallazgos priorizados

**Seguimiento — 2026-10-06:** el arranque de SEC-03 está corregido en el árbol
de trabajo: loopback por defecto, Quack opt-in, sin instalación automática ni
token literal, con limpieza de recursos probada. Ver
[alcance y evidencia](sqlviz-local-startup.md). No hay commit nuevo de referencia.

**Segundo incremento — 2026-10-06:** los controles HTTP de SEC-01/04 están
implementados con sesiones por aplicación y credenciales de viewer por solicitud;
ver [política y validación](sqlviz-authorization.md). DATA-04 mejora en sesiones/cursores;
el estado global del aprendizaje permanece pendiente. La tabla conserva lo
observado en la base auditada; Quack opt-in sigue otorgando acceso a la base a
su titular y no representa aislamiento analítico.

**Tercer incremento — 2026-10-06:** SEC-02 se corrige para la ejecución HTTP
de gráficos, sondeos y dominios: catálogo separado que nunca adjunta el proyecto,
consultas de lectura también para autor y capacidades externas desactivadas.
DATA-01 incorpora presupuestos y cancelación cooperativa; siguen pendientes
cuotas duras de proceso y cancelación desde UI. Ver
[compatibilidad, evidencia y límites](sqlviz-analytical-execution.md). Las
observaciones históricas siguientes describen la base auditada, no el código actual.

**Cuarto incremento — 2026-10-06:** valores y cuerpos de filtros acotados,
placeholders desde AST y preparación de listas sin regex sobre SQL. Se corrigen
los errores previos de tipos: mypy global y svelte-check pasan sin errores; desaparecen las seis
advertencias de compilación Svelte. REL-01 mejora con versión instalada común
para API/meta/creación y runtimes de CI alineados. Ver
[alcance y evidencia](sqlviz-parameters-and-quality.md); no constituye aprobación
de CI remoto ni sincroniza retrospectivamente las versiones de archivos existentes.

**Quinto incremento — 2026-10-06:** BP-01 corregido: borrado de dashboard y sus
paneles/enlaces/filtros en una transacción, revocación posterior al commit y
creación dependiente protegida frente a borrado simultáneo. 25 casos nuevos
cubren rollback, reapertura, conflictos y alcance de sesiones. Ver
[decisiones, pruebas y límites](sqlviz-dashboard-integrity.md). E1 sigue en curso.

**Sexto incremento — 2026-10-06:** BP-02 corregido con política de ancestros en
core y repositorio transaccional. Una revisión del árbol protege movimientos
simultáneos y creación/ubicación de dashboards frente a borrado de carpetas.
BP-05 corregido para `parent_id`/`folder_id`: omisión conserva y null quita.
La política de borrar solo la carpeta y promover contenidos se mantiene, con
rollback probado. Ver [alcance y evidencia](sqlviz-folder-integrity.md). El
explorador sigue siendo plano; no se declara implementada una nueva UI anidada.

**Séptimo incremento — 2026-10-06:** BP-03 corregido con rangos manuales en core
y PATCH estricto. La UI conserva el gráfico ante rechazo y aplica tamaños
confirmados; brain registra patrón/evento por separado sin invalidar el guardado
del proyecto. Se preservan ambas dimensiones aprendidas y se ignoran overrides
históricos inválidos al renderizar. 49 casos nuevos Python y 9 frontend.
Ver [contratos, evidencia y límites](sqlviz-panel-dimensions.md). No resuelve
BP-04 ni revisiones de panel/concurrencia entre todas las operaciones del editor.

P0 bloquea compartir en redes no confiables. P1 bloquea una beta de calidad
profesional. P2 mejora mantenimiento y preparación para escalar. Las referencias
de código son relativas a `packages/`.

| ID | Prioridad | Observación y evidencia | Consecuencia / acción |
| --- | --- | --- | --- |
| SEC-01 | P0 | `sqlviz-api/src/sqlviz_api/routers/{dashboards,panels,folders,compose}.py` no aplican una política de acceso al router; `main.py` protege el frontend, no estos routers | Acceso directo sin sesión a datos y operaciones. Centralizar autorización y comprobar cada recurso |
| SEC-02 | P0 | `routers/panels.py:execute_panel` ejecuta SQL sobre el mismo DuckDB que almacena `_sqlviz_auth`, shares y dashboards | Lectura/escritura de datos internos a través de consultas; separar ejecución analítica y almacenamiento de aplicación |
| SEC-03 | P0 | `sqlviz-cli/src/sqlviz_cli/cli.py` usa `0.0.0.0` por defecto; `server.py:_try_start_quack` intenta instalar una extensión nightly y arrancarla con un token literal | Exposición innecesaria y servicio adicional sin configuración de credenciales. Default loopback; Quack solo opt-in, versionado y con autenticación propia |
| SEC-04 | P0 | Los viewers validan un enlace en `/view/...` pero luego llaman a las rutas generales de paneles/ejecución, sin credencial de share en cada operación | El alcance/revocación del enlace no protege las rutas de datos posteriores. Emitir sesión limitada o validar capacidad en cada solicitud |
| DATA-01 | P1 | `panels.py` usa `fetchall()` sin límite central de filas, bytes o tiempo; no existe cancelación de ejecución | Una consulta costosa puede agotar el proceso. Presupuestos, concurrencia limitada, cancelación efectiva y resultados acotados |
| DATA-02 | P1 | `dashboardStore.svelte.ts:splitStatements` usa `text.split(';')`; `run()` asocia paneles por posición y los persiste antes de completar el run | SQL con `';'` en literales/comentarios se fragmenta; reordenar consultas puede reasignar overrides. Parser backend, IDs estables y revisiones |
| DATA-03 | P1 | `sqlviz-storage/src/sqlviz_storage/migrations.py:run_migrations` registra y continúa ante fallos, sin transacción conjunta de DDL y registro | Apertura sobre esquema parcialmente migrado. Migraciones transaccionales y bloqueo de escrituras si la migración requerida falla |
| DATA-04 | P1 | `sqlviz-storage/src/sqlviz_storage/brain_db.py` mantiene una conexión global compartida entre proyectos; `routers/auth.py` usa sesiones globales al módulo | Concurrencia y aislamiento insuficientes para múltiples proyectos/usuarios. Estado por aplicación/workspace y contextos de conexión por operación |
| UX-01 | P1 | `dashboardStore.svelte.ts:handleAxisOverride` es explícitamente de sesión; paleta de dashboard y vistas de filtro usan localStorage | La configuración visual no tiene aún una persistencia uniforme y compartible. Separar configuración del autor y preferencia personal |
| UX-02 | P1 | `executeFilteredPanels` conserva resultados anteriores silenciosamente ante errores | Se puede mostrar información vieja bajo filtros nuevos sin indicarlo. Estados por panel, identidad de ejecución y aviso de datos anteriores |
| ARCH-01 | P1 | `routers/panels.py` combina acceso SQL, parámetros, ejecución, inferencia, aprendizaje, persistencia y presentación | Extraer servicios de aplicación; rutas HTTP pequeñas; una ruta de ejecución reutilizable para editor y viewer |
| ARCH-02 | P2 | `DataSourceContract` y registro existen en core, pero la API ejecuta DuckDB directamente | Abstracción aún no integrada. Conectar el contrato a un servicio real antes de multiplicar conectores |
| ARCH-03 | P2 | `FeedbackEngine` consulta/persiste por `brain_conn` y el pipeline comparte un `RuntimeContext` mutable | La inferencia no es completamente pura. Inyectar preferencias como valores y persistir eventos fuera del compilador |
| WEB-01 | P1 | `dashboardStore.svelte.ts` ronda 47 KB; viewers de dashboard/workspace duplican ejecución y filtros | Separar comandos de edición, estado de ejecución y presentación; compartir un runtime de dashboard |
| DOC-01 | P1 | README decía Python 3.11, API `main:app`, puerto 8000 y v0.2.4; código requiere 3.12+, fábrica de app y proxy a 4000 | Onboarding no reproducible. README corregido en esta revisión |
| REL-01 | P2 | `main.py` anuncia 0.2.1, `project_db.py` 0.2.5, frontend 0.2.11 y entorno Python instalado 0.2.4 | Separar versión de producto, contrato y esquema; sincronizar artefactos desde la build |

SEC-01 y la escritura descrita en SEC-02 fueron **reproducidas**. El resto combina
lectura directa del código y evaluación de sus consecuencias; no se afirma que
se hayan reproducido carreras de concurrencia, agotamiento de memoria o accesos
a archivos del sistema. En la auditoría original los P0 permanecían abiertos;
el seguimiento anterior registra la corrección posterior de arranque. La
autorización HTTP tiene seguimiento en el segundo incremento; el aislamiento
analítico HTTP tiene seguimiento en el tercer incremento. Las reproducciones
siguientes conservan la evidencia original.

### Reproducción aislada de SEC-01/SEC-02

Se crearon dos bases en memoria: proyecto y aprendizaje. Se configuró una
contraseña administrativa y `create_app(..., demo_mode=False)`. Con TestClient,
sin cookie ni login, se obtuvieron estos resultados:

| Operación | Resultado observado | Resultado requerido |
| --- | --- | --- |
| `GET /api/v1/auth/me` | 401 | 401 |
| `GET /api/v1/dashboards` | 200 | 401 |
| `POST /api/v1/dashboards` | 201 | 401 |
| Crear panel con `SELECT 42 AS audit_value` | 201 | 401 |
| Ejecutar ese panel | 200, dato 42 | 401 |
| Cambiar su SQL a un `CREATE TABLE` inocuo y ejecutar | 200, tabla temporal del ensayo creada | 401; además, un viewer nunca puede ejecutar DDL |

Se sustituyó `get_brain_connection` por la conexión en memoria. No se arrancó
un servidor accesible por red, no se usaron enlaces reales y no se leyeron
contraseñas ni archivos personales.

Proteger solo las escrituras no corrige la fuga de lectura. Añadir `require_admin`
a todo sin adaptar los viewers rompe el compartir legítimo. La solución debe
abarcar permisos de recursos, sesiones de viewer, ejecución y regresiones de los
flujos de compartir. Ver la entrega E0 del nuevo roadmap.

### El aislamiento descrito no está aplicado

`quack_server.py` describe conexiones de viewer de solo lectura. Sin embargo,
`server.py` crea un cursor de la conexión de escritura y `dependencies.py:get_db`
entrega cursores de `app.state.db_conn`; no consulta `connection_for_request`.
Un cursor independiente ayuda con resultados concurrentes, pero no constituye
una frontera de autorización. Tampoco se cierra explícitamente en la dependencia.

La documentación de DuckDB advierte que SQL puede acceder a archivos, red y
recursos del proceso. Una comprobación de que la consulta empieza con SELECT
no basta como aislamiento. Se requieren permisos de la fuente y restricciones
del entorno de ejecución. [Fuente: seguridad de DuckDB](https://duckdb.org/docs/current/operations_manual/securing_duckdb/overview).

## Validación ejecutada

Entorno existente, sin reinstalar dependencias: Windows, Python **3.13.14**,
Node **24.21.0**, DuckDB **1.5.4**, SQLGlot **30.11.0**, FastAPI **0.139.0**.
CI declara Python 3.12 y Node 20: esta ejecución local no sustituye esa matriz.

| Comando | Resultado |
| --- | --- |
| `.venv/Scripts/python.exe -m pytest --tb=short -q` | **1391 passed, 3 skipped**; aviso de permisos al escribir caché de pytest |
| `.venv/Scripts/python.exe -m ruff check packages/` | Correcto |
| `.venv/Scripts/python.exe -m mypy` sobre los cinco directorios `src` | **2 errores** en 114 archivos |
| `npm run check` en `sqlviz-web` | 0 errores, **6 advertencias** |
| `npm test` en `sqlviz-web` | **51 tests pasan**, 8 archivos; avisos `derived_inert` |
| `npm run build` en `sqlviz-web` | Correcto; SPA generada, advertencias de Svelte, sourcemaps/anotación PURE y chunks grandes |

Errores de mypy: asignación de `Expr` a `Expression` en
`filters/neutralize.py:46`, y borrado con clave `str | None` en
`routers/auth.py:74`. Advertencias Svelte: valores iniciales de props capturados
en `ChartSelectorPanel.svelte` (4) y `autofocus` en login/viewer (2).

Las suites prueban funcionalidad, pero su éxito no acredita control de acceso,
resistencia a carga, accesibilidad completa ni calidad visual premium. Los
fixtures generales de API usan clientes sin autenticar; hace falta una matriz
negativa de permisos, no solo pruebas del formulario de login.

## Documentación y ambición

El roadmap anterior describe v0.2.10 como endurecimiento de inferencia y v0.2.11
como selector de gráficos. El changelog y el código describen entregas distintas.
No debe utilizarse como fuente del estado de releases.

DOC9 mezcla un programa de investigación con ambición de producto. Sus hipótesis
sobre cognición y originalidad no son capacidades verificadas. DOC11 organiza
filtros en veinte motores antes de demostrar que esa separación aporta valor.
Se conservan como material de investigación, pero se reemplaza su orden de
ejecución por entregas medibles de valor y fiabilidad.

El motor semántico actual clasifica nombres y señales para recomendar gráficos.
No es todavía una capa de métricas gobernadas: faltan definiciones versionadas,
granularidad, agregación, relaciones verificadas, permisos y linaje. La
[arquitectura objetivo](sqlviz-product-architecture.md) diferencia ambas cosas.
