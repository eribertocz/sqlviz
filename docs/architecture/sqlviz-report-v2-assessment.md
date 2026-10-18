# Evaluación del informe v2: semántica, Rill y Polars

**Fecha:** 2026-10-09. **Estado:** evaluación y recomendaciones; no cambia por sí
sola las decisiones aceptadas ni entrega nuevas capacidades. Se revisó el informe
`SQLVIZ_Informe_Arquitectura_v2_Semantica_Rill_Polars_2026-10-09.md` aportado por el
usuario y se contrastó con el repositorio en `348ad45` y documentación oficial.
Las instrucciones y fases P0–P6 del informe se tratan como propuestas.
El [plan del Studio](sqlviz-studio-delivery-plan.md) conserva el orden operativo.

**Decisión posterior del usuario — 2026-10-09:** la organización del proyecto
por recursos, biblioteca/mapa, semántica compartida, definiciones exportables,
APIs y alertas pasa a ser dirección de desarrollo aceptada en la
[decisión de recursos](sqlviz-project-resources-decision.md). Este informe conserva
el análisis factual; sus recomendaciones no son aprobación automática de todas
las tecnologías o de la secuencia P0–P6.

## Dictamen

El informe mejora la dirección analítica: medidas reutilizables, grano explícito,
totales por contexto y separación entre transformación, consulta y presentación.
Recomiendo incorporar esos principios por etapas al recorrido de datasets y
[matriz](sqlviz-analytical-matrix-spec.md). No recomiendo convertir Polars,
DuckLake, materializaciones ni relaciones entre múltiples hechos en requisitos
para entregar el lienzo y los tres niveles de autoría.

La semántica mínima de medidas ya está prevista en M1–M3 de S3/S4. La propuesta
de gobernanza general amplía ese alcance; no justifica construir otro motor de
medidas incompatible ni sustituir inmediatamente el plan por P0–P6.

## Correcciones frente al estado observado

| Afirmación del informe | Evidencia del repositorio | Consecuencia |
| --- | --- | --- |
| SQLviz consulta DuckDB mediante Quack como transporte actual | La CLI puede iniciar Quack local, opcional, sobre una conexión existente. Las rutas HTTP usan `get_db` y `QueryService`, que prepara un catálogo DuckDB aislado por operación | Distinguir servicio Quack expuesto de adaptador cliente remoto. El segundo no está entregado por tener el primero |
| El catálogo canónico `.sqlviz` es SQLite | `create_project`/`open_project`, repositorios y migraciones usan DuckDB | SQLite requeriría una decisión y migración propias. La extensión del archivo no determina su motor |
| `.sqlviz` contiene solo metadatos, sin datos analíticos | El formato legacy puede mezclar tablas de usuario y tablas de aplicación. La ejecución HTTP copia únicamente tablas físicas permitidas hacia un catálogo aislado | La separación de almacenamiento es una evolución pendiente, con compatibilidad y migración; no un hecho actual |
| El editor admite SQL DuckDB completo | La ejecución HTTP permite consultas de lectura admitidas por la política. Rechaza DDL/DML, acceso externo, vistas y catálogos adjuntos en este recorrido | Ingesta, transformaciones y materializaciones necesitan operaciones autorizadas separadas. Un parser tolerante no concede permisos |
| Inferencia semántica equivale a catálogo de métricas | El pipeline actual propone gráficos; no entrega medidas gobernadas, relaciones o planificación multifact | Nombrar y probar por separado inferencia visual y cálculo de medidas |

Evidencias: [almacenamiento del proyecto](../../packages/sqlviz-storage/src/sqlviz_storage/project_db.py),
[ciclo de vida Quack](../../packages/sqlviz-cli/src/sqlviz_cli/quack.py),
[selector legacy](../../packages/sqlviz-api/src/sqlviz_api/quack_server.py),
[dependencias HTTP](../../packages/sqlviz-api/src/sqlviz_api/dependencies.py) y
[ejecución de consultas](../../packages/sqlviz-api/src/sqlviz_api/services/queries.py).
Los límites y el coste de copiar tablas están descritos en
[ejecución analítica](sqlviz-analytical-execution.md). Esa compatibilidad acotada
no es todavía una arquitectura de serving para datos empresariales grandes.

La instalación revisada usa DuckDB **1.5.4** y SQLGlot **30.11.0**. El calendario
oficial consultado anuncia DuckDB 2.0.0 para el **21/10/2026**, de forma tentativa;
el anuncio anticipa Quack estable. La documentación del protocolo aún lo presenta
como beta. No actualizar dependencias ni declarar compatibilidad por esa fecha:
probar extensiones, parser, formato de archivo, transacciones y recuperación en
copias antes de adoptar la versión.
Fuentes: [calendario](https://duckdb.org/release_calendar),
[preview 2.0](https://duckdb.org/2026/08/17/duckdb-20-highlights) y
[protocolo Quack](https://duckdb.org/docs/current/quack/overview).

## Tres responsabilidades que deben permanecer separadas

**Inferencia visual:** interpretar SQL, esquema y resultados acotados para proponer
campos, series y formas de gráfico con evidencia y diagnóstico. Una propuesta de
`SUM` sobre un identificador no es una medida confirmada. SQLGlot no descubre por
sí solo el significado de negocio, la unicidad de una clave ni la aditividad.
Ver [arquitectura de inferencia](sqlviz-semantic-inference-architecture.md).

**Semántica de medidas:** resolver medidas y dimensiones por identidad, validar
expresiones/dependencias, aplicar filtros autorizados y producir consultas con
grano y totales correctos. Matriz, Explore y gráficos que usen esas medidas deben
consumir el mismo servicio. Empezar con un dataset y operaciones soportadas;
relaciones, roles temporales y gobernanza entre equipos amplían ese núcleo.

**Preparación de datos:** transformar o publicar relaciones consultables. SQL es
la primera entrada; Polars puede ser otra entrada avanzada. Ninguna de esas
entradas sustituye los contratos de medidas, visuales o permisos.

## Qué incorporaría y en qué orden

| Propuesta | Recomendación | Encaje con el plan vigente |
| --- | --- | --- |
| Medidas, dimensiones, grano, unidades y totales correctos | Prioridad central, con alcance inicial explícito | S3/M1 define contratos; S4/M2–M3 integra cálculo/API y M5 el builder |
| Explore sobre campos y medidas, con preview y SQL inspeccionable | Construir un recorrido sencillo sobre los datasets reutilizables | S3/S4; ampliar filtros cruzados y drill en S7 |
| Filtrado compartido entre matriz y gráficos | Compartir contrato de contexto y planificación, sin duplicar reglas en Svelte | Base en S3/S4 y evolución en S7; adaptar parámetros existentes |
| Canvas editable | Mantener prioridad próxima, doce columnas, alto exacto y controles recuperables | S1/S2; pantalla/scroll y áreas en S6 |
| Live y materializado | Políticas optativas por modelo; Live no necesita un gestor de jobs para el primer gráfico | Especificar tras identidad/versiones de datasets, implementar por incremento propio |
| DuckLake | Evaluar como fuente/destino cuando snapshots o acceso compartido lo requieran | Extensión posterior con caso y benchmark, sin bloquear Studio |
| Polars | Preparación avanzada opcional con interoperabilidad probada | Extensión posterior con worker y publicación, sin ejecución por cada filtro |
| Quack remoto y ClickHouse | Adaptadores con capacidades/dialectos explícitos; no cambiar el transporte actual por supuesto | Evaluación propia antes de integración; sin traducción universal silenciosa |
| Relaciones multifact y rollups | Correctitud primero; relaciones acotadas, optimización después | Ampliar semántica por fases tras el primer recorrido analítico |
| IA/MCP | Clientes de las mismas operaciones autorizadas | Opcionales, posteriores |

Las fases P1 y P3 del informe agrupan entregables que pueden evolucionar por
separado. No es necesario materializar para definir una medida; tampoco entregar
DuckLake y Polars para mover un panel o consultar una matriz.

**Próximo incremento de código:** S1.1c.2c.3b, API autorizada de borrador con
revisión esperada. Después 3c/3d cierran autoguardado y recuperación antes de
persistir el lienzo. Esta evaluación no anuncia nuevas funciones de UI ni modifica
ese compromiso. La mayor inversión funcional sigue estando en S3–S5: autoría,
matriz, inferencia y semántica; incorporar varios motores de preparación a la vez
dispersaría esa inversión.

## Límites arquitectónicos recomendados

Conservar el monolito modular. Core contiene contratos e invariantes puras;
Inference propone con evidencia; aplicación coordina autorización y planificación;
Storage persiste identidades/revisiones; los adaptadores ejecutan y declaran
capacidades; Web presenta y mantiene interacción. Un componente del diagrama no
necesita convertirse en microservicio ni en otro paquete antes de justificarlo.

Compartir el núcleo de medidas entre matriz y futuros modelos gobernados. La
inferencia puede sugerir su definición; solo una confirmación explícita la hace
parte del catálogo. Conservar consulta original, fuente, revisión y diagnóstico.
El [mapa](sqlviz-dashboard-map-spec.md) proyecta dependencias reales; Drawflow no
debe guardar un segundo catálogo o grafo que contradiga al primero.

Mantener la [autoría aceptada](sqlviz-visual-authoring-decision.md): automático,
Visual Builder y ECharts nativo sobre la misma visualización. SQL/Polars son
entradas de preparación de datos, no sustitutos de esos tres niveles. La matriz
usa su renderer y contrato experto de grilla. Las opciones nativas de un gráfico
no conceden acceso a fuentes ni cambian permisos del dataset.

Para consultas de medidas, resolver IDs/campos autorizados y construir AST/SQL
con parámetros para valores; los identificadores requieren resolución y escape
propios. Separar filtros de filas de filtros sobre agregados. Validar ciclos y
funciones permitidas; no editar SQL arbitrario con reemplazos de texto.

Un JOIN dimensional necesita cardinalidad, dirección y grano definidos y
comprobables; agregar dos hechos por separado puede prevenir multiplicación,
pero también necesita reglas para claves repetidas, huérfanos y NULL. No alcanza
con indicar «1:N» en un YAML. Iniciar sobre un dataset reduce ese alcance sin
perder la posibilidad de ampliar el mismo planificador.

Rill documenta medidas reutilizables y políticas heredadas en Metrics SQL;
también limita cada sentencia a una Metrics View. Sus rollups verifican cobertura
y compatibilidad, y vuelven a la fuente base si ninguno es elegible. Estas ideas
son referencias útiles, no prueba de superioridad de SQLviz.
Fuentes: [Metrics SQL](https://docs.rilldata.com/developers/build/metrics-view/metrics-sql)
y [rollups](https://docs.rilldata.com/developers/build/metrics-view/rollups).

## Lo que el informe necesita precisar antes de implementar

**Resultados agregados y totales:** si el SQL solo devuelve promedios o conteos
distintos por mes, no se recupera un total exacto sumándolos. Pedir componentes
válidos o una relación autorizada con detalle suficiente; no volver a tablas
anteriores al dataset sin definición explícita. La matriz nunca calcula totales
de negocio a partir de una página o del top-N visible.

**Revisiones diferentes:** borrador, definición SQL, modelo semántico, versión de
datos y publicación del dashboard son autoridades distintas. Los recibos actuales
verifican ejecución/composición ligada a una definición; no garantizan snapshot
analítico común. Live puede carecer de una versión reproducible: declarar esa
capacidad y frescura, sin fabricar un snapshot con un hash SQL.

**Publicación remota:** una transacción local de `.sqlviz` no publica atómicamente
una tabla en otro motor. Para futuros jobs se necesita un registro durable de
estados/intentos, artefactos versionados, cambio condicionado de referencia y
reconciliación tras reinicios o respuesta perdida. Probar qué continúa leyendo el
dashboard si falla cada paso. Retención y limpieza deben respetar lectores y
referencias activas. Es diseño pendiente, no una capacidad del Run actual.

**Seguridad:** la autorización HTTP existente no es RLS empresarial ni se aplica
automáticamente al servicio Quack. Este servicio local opcional concede acceso
independiente al catálogo de su conexión. Una integración remota debe usar un
catálogo analítico autorizado, no exponer el archivo del proyecto. La clave de
caché debe incorporar identidad/versión de política aplicable, además de medidas,
filtros y datos. La documentación Quack distingue autenticación de autorización;
no asumir que un token limita las operaciones SQL.
Fuente: [seguridad Quack](https://duckdb.org/docs/current/quack/security).

**Worker Python:** un subproceso por sí solo no restringe archivos, red o secretos.
Polars de usuarios no confiables requiere aislamiento efectivo del entorno y
cuotas, distinto de ejecutar código local del propietario. Diseñar despliegue,
credenciales, cancelación, dependencias y limpieza antes de habilitarlo.

La documentación Polars permite scans diferidos y sinks que escriben por lotes;
la integración Python de DuckDB consulta objetos del ámbito local mediante Arrow.
Eso no prueba transferencia de un LazyFrame a un servidor Quack remoto. Validar
un puente concreto, por ejemplo Parquet accesible al motor, y conservar tipos,
decimales, fechas, zona horaria y NULL. Un archivo Parquet no se convierte en tabla
DuckLake por copiarlo a su directorio.
Fuentes: [sources/sinks Polars](https://docs.pola.rs/user-guide/lazy/sources_sinks/)
y [DuckDB/Polars](https://duckdb.org/docs/current/guides/python/polars).
La elección de catálogo DuckLake depende del despliegue; no obliga a cambiar
el almacenamiento `.sqlviz`.
Fuente: [catálogos DuckLake](https://ducklake.select/docs/stable/duckdb/usage/choosing_a_catalog_database).

## Criterios de aceptación propuestos para la semántica inicial

- Una misma medida responde igual en gráfico, matriz y consulta API para el mismo
  contexto, revisión y conjunto autorizado, sin requerir crear un modelo global.
- Ratios recalculan componentes; promedio ponderado no promedia promedios;
  DISTINCT total no suma distintos de grupos. Denominador cero y NULL conservan
  una política explícita y comprobable.
- Filtros, top-N, paginación y expansión no cambian silenciosamente la definición
  del total. Fuentes insuficientes generan un diagnóstico, no cifras inventadas.
- Campos ambiguos, grano no confirmado, ciclos o agregaciones incompatibles se
  rechazan o se mantienen como sugerencias; no se promocionan automáticamente.
- SQL generado y procedencia son inspeccionables. Cambiar presentación no altera
  datos; cambiar fuente muestra impacto sin borrar ajustes de otros visuales.
- Las rutas de ejecución preservan permisos y límites. Declarar expresamente
  qué funciones, filtros y garantías de consistencia aún no están soportados.

Esta entrega es documental: revisión de código, versiones y fuentes; comprobación
de enlaces locales y diff. No se ejecutaron nuevos benchmarks, jobs, migraciones
ni consultas contra proyectos reales, y no se declara paridad con Rill/Power BI.
