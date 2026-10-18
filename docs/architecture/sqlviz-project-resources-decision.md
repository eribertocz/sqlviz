# Proyecto analítico: recursos, biblioteca y automatización

**Decisión aceptada por el usuario:** 2026-10-09.
**Estado:** dirección obligatoria de desarrollo; capacidades pendientes de
implementación. Este documento convierte la organización por recursos discutida
a partir de Rill en parte del alcance de SQLviz. No adopta automáticamente todas
las tecnologías ni las fases P0–P6 del informe externo.

SQLviz será un proyecto analítico integrado: conectar fuentes, preparar datasets,
definir medidas, explorar, diseñar dashboards y automatizar evaluaciones. La
biblioteca y el Mapa vivo deben permitir encontrar, reutilizar y editar los mismos
objetos, con permisos y revisiones coherentes.

El [plan operativo](sqlviz-studio-delivery-plan.md) sigue siendo la única secuencia
de implementación. El lienzo y los tres niveles de autoría conservan su prioridad;
el catálogo semántico crece junto a datasets y matriz, y la automatización se
integra después de disponer de definiciones y contextos fiables.

## Recursos que forman parte del producto

| Recurso | Responsabilidad | Invariante |
| --- | --- | --- |
| Conexión | Motor/dialecto, capacidades y referencia a credenciales | Los secretos no se exportan ni se exponen en el mapa |
| Fuente | Relación, archivo u origen permitido bajo una conexión | Acceso validado en servidor; una ruta local no se supone accesible remotamente |
| Dataset/modelo y revisión | Definición de preparación, parámetros, esquema y grano | Un modelo SQL es la definición del dataset, no otra copia independiente de su consulta |
| Dimensión/medida y revisión | Identidad, expresión, tipo, unidad, agregación, dependencias y contexto | Inferencia sugiere; confirmación y validación incorporan la definición al catálogo |
| Visual y revisión | Inputs, campos/roles, renderer y configuración | Reutilizable; ajustes explícitos sobreviven al refresco compatible |
| Panel | Instancia de un visual en el lienzo | Posición/tamaño no cambian SQL ni identidad del visual compartido |
| Dashboard y publicación | Composición, filtros, tema y referencias fijadas | Editar un recurso no altera publicaciones existentes silenciosamente |
| API analítica | Consulta de datasets o medidas autorizadas | Reutiliza planificación y ejecución; no abre un segundo camino de SQL privilegiado |
| Alerta | Regla sobre métricas, frescura o estado de recursos; evaluación y notificación | Registra contexto, revisión, estado y entregas; no confunde fallo de evaluación con condición cumplida |

La distinción conexión/fuente debe resolverse al concretar los contratos existentes
de `DataSource`. No crear dos catálogos equivalentes ni todas las tablas de una vez.
Las operaciones iniciales usan SQL; Polars, DuckLake y motores adicionales conservan
su evaluación e integración posteriores. No son requisitos para usar la biblioteca.

## Un solo catálogo y varias maneras de trabajar

La persistencia conserva IDs y revisiones; etiquetas, nombres de archivos y
fingerprints no sustituyen la identidad. Biblioteca, mapa, editor SQL, builder,
APIs y alertas utilizan esos recursos y sus referencias. El grafo mostrado es una
proyección autorizada de las dependencias confirmadas; Drawflow no guarda un
segundo modelo de negocio ni decide permisos.

Preparación SQL, esquema/resultados y presentación permanecen separados. Guardar
una definición no importa filas ni crea una tabla física. El resultado de preview
declara límites y frescura; no se convierte en fuente completa para una matriz.
Una consulta aislada puede producir un gráfico antes de promoverse a dataset
reutilizable. El editor multiconsulta mantiene identidad por sentencia: el script
entero no se convierte en una única fuente ni el orden decide las dependencias.

Cambiar una consulta usada por varios visuales crea una revisión y un plan de
impacto. Los consumidores conservan identidad y ajustes compatibles; adoptar la
revisión es una operación explícita y condicionada. Una incompatibilidad pide
reparación, sin descartar todos los paneles ni cambiar datos publicados por accidente.
Ver [autoría e impacto](sqlviz-visual-authoring-decision.md).

**Inferencia automática → Visual Builder → ECharts native options** siguen siendo
los tres niveles de una misma visualización. La matriz comparte la autoría
progresiva con un renderer y configuración experta de grilla propios. Editar la
configuración del proyecto SQL/JSON/YAML es otra superficie avanzada y no sustituye
estos niveles ni permite ejecutar callbacks arbitrarios.

## Biblioteca y navegación

El autor dispone de una biblioteca bajo demanda, integrada con el acceso actual
de navegación. Ordena por recurso y permite búsqueda, estado, usos y acciones
contextuales. El dashboard conserva el espacio disponible cuando la biblioteca
está oculta. No añadir otro sidebar permanente o una barra independiente para
cada módulo.

Al abrir un recurso aparecen su editor correspondiente, preview y referencias
autorizadas. Desde «Usado en» o el [Mapa vivo](sqlviz-dashboard-map-spec.md) se llega
al consumidor y se vuelve conservando selección, posición y borradores. Una
medida permite inspeccionar definición y contexto; una alerta muestra condición,
programación, historial y entrega. Sin pantallas vacías para módulos pendientes.

El viewer mantiene el selector compacto de dashboards y filtros bajo demanda.
No necesita abrir el árbol técnico del proyecto. Los recursos disponibles para un
autor tampoco aparecen automáticamente en una publicación o enlace de lector.
La [navegación vigente](sqlviz-navigation.md) sigue siendo la base de integración.

## Semántica compartida

Matriz, gráficos basados en medidas, Explore, APIs y alertas deben consultar el
mismo servicio semántico. El frontend no implementa otro compilador de métricas.
Inicialmente se soporta un dataset con operaciones explícitas; relaciones entre
hechos y gobernanza de equipos amplían ese núcleo sin reemplazarlo.

La petición conserva dimensiones/medidas por ID, filtros de filas y agregados,
roles temporales, contexto autorizado y revisiones. El compilador resuelve campos,
valida expresiones/dependencias y genera SQL del motor con valores parametrizados.
Los permisos se aplican también a preview, dominios de filtros, exportación y
aciertos de caché.

DISTINCT se evalúa en el contexto correcto; ratios recalculan componentes;
promedios requieren pesos válidos; saldos tienen política temporal. Si la fuente
solo devuelve estadísticos insuficientes, diagnosticarlo. Top-N, paginación o
expansión no redefinen silenciosamente el total. La [matriz analítica](sqlviz-analytical-matrix-spec.md)
ya establece ese contrato mínimo y su desglose M1–M9.

## Definiciones inspeccionables y Git

La UI y la edición avanzada actúan sobre el mismo modelo canónico mediante
validación, revisión esperada y preview de impacto. Exportación/importación
SQL/JSON/YAML es parte del alcance, con formato versionado y orden determinista.
No afirmar conversión visual completa de SQL arbitrario.

El archivo `.sqlviz` sigue usando DuckDB. El bundle de definiciones no duplica
la autoridad del proyecto activo, no contiene secretos, sesiones o datos de
preview, y puede revisarse en Git. Importar muestra diferencias, asignación de
identidades y referencias faltantes antes de aplicar de forma transaccional.
La elección precisa de formato se decide al implementar el primer bundle; no se
obliga al usuario visual a mantener archivos YAML.

## Alertas y operación

Las alertas forman parte del alcance comprometido. Dos recorridos distintos
comparten infraestructura: condición sobre medida autorizada y estado/frescura
de un recurso. La UI define condición, período, zona horaria, frecuencia,
destinatarios y política de recuperación/repetición. Un fallo de consulta produce
estado de error, no una notificación de cumplimiento inventada.

Antes de habilitar ejecución programada, definir identidad efectiva, permisos
vigentes, revisión consultada y versión/frescura de datos disponible. Evaluar
desde un servidor activo con registro durable, cuotas, cancelación y recuperación;
no usar temporizadores del navegador ni depender de que el dashboard esté abierto.

Separar definición, evaluación y entrega. Registrar el intento y evitar repetir
la misma evaluación ante reinicio o respuesta perdida; usar una cola de entrega
durable, reintentos acotados y política explícita de duplicados por canal. No
prometer entrega externa exactamente una vez sin garantía del proveedor.
Configurar canales y credenciales separadamente; autorizaciones y destinatarios
no se heredan por el mero hecho de poder leer un dashboard.

## Integración en entregas pequeñas

Este desglose complementa S0–S8; no crea una segunda cola que compita con el Studio.
Todas las capacidades siguientes están pendientes. Sus códigos identifican
partes de alcance y criterios de cierre, no versiones ni fechas.

| Parte | Encaje y cierre |
| --- | --- |
| R1a | S3.1–S3.2: identidad/revisión de dataset y campos, grano, parámetros y referencias autorizadas; pruebas de compatibilidad |
| R1b | S3.4–S3.5: persistencia y promoción de sentencia a dataset reutilizable; dos visuales comparten definición sin duplicar SQL |
| R2a | S3.5: biblioteca inicial de datasets/visuales/dashboards sobre los recursos realmente entregados; búsqueda y navegación por identidad |
| R2b | S3.6/S4.6, F1–F3: mapa y «Usado en», abrir/editar/regresar con estado conservado; biblioteca y mapa muestran la misma revisión |
| R3a | S3.M1: contrato compartido de dimensiones/medidas, grano, dependencia y unidades; inferencia no confirma significado de negocio |
| R3b | S4.M2–M3: planificación, cálculo por contexto y API interna autorizada; corpus de ratios, distintos, filtros y totales |
| R3c | S4.M4–M5 y S4.2: matriz/builder y exploración inicial usan ese núcleo; guardar/reabrir/viewer con resultados equivalentes |
| R3d | S5/S7: ampliar medidas, calendario y filtros cruzados/roles temporales por incrementos; relaciones solo con corrección demostrada |
| R4a | S8: primer bundle exportable sin secretos/resultados, formato versionado y validación determinista |
| R4b | S8: preview de importación y conflictos; aplicar por revisión, rollback y equivalencia al reabrir |
| R5a | Extensión posterior al primer recorrido publicado S8: contratos de conexión/fuente y adaptador autorizado prioritario; diagnóstico y ciclo de credenciales |
| R5b | Después de R5a: preview/ingesta acotados; opcionalmente refresh/publicación de datos con recuperación, sin mezclarlo con guardar definiciones |
| R6a | Extensión posterior a S8, dependiente de R3b y publicación/contexto: definición de alerta, autorización, evaluación manual e historial durable |
| R6b | Después de R6a: scheduler con zona horaria, cuotas, reinicio y deduplicación de evaluaciones; no ejecutar con revisión o permiso obsoleto |
| R6c | Después de R6b: primer canal de entrega y pruebas de fallo/reintento; recuperación/repetición y permisos de destinatarios antes de ampliar canales |
| R7a | Después de R3b/S8: API analítica pública por recurso con autenticación, versiones, límites y la misma semántica |
| R7b | Después de R7a: consumidores externos y auditoría, revocación y caché aislada; ampliar solo capacidades realmente entregadas |

Las APIs internas preceden a la UI de cada recurso. R7 designa su exposición a
consumidores externos, no pospone contratos o autorización. Conexiones/fuentes
externas tienen incremento propio: la biblioteca inicial reutiliza los datos
locales permitidos y no espera a disponer de múltiples motores.

**Trabajo inmediato:** cerrar 3b/3c/3d de S1.1c.2c, persistencia del lienzo S1.2,
texto S1.3 y gestos S2. Esos contratos son la base de la dirección aceptada.
La mayor inversión funcional continúa en S3–S5: dataset/semántica, matriz, autoría
visual e inferencia. Cada recurso nuevo debe cerrar guardar → reabrir → usar con
permisos y errores coherentes antes de ampliar el catálogo.
