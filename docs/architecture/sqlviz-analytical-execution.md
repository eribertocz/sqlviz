# Ejecución analítica aislada — tercera unidad de E0

**Implementado en el árbol de trabajo: 2026-10-06.** Cubre ejecución HTTP de
paneles, dominios de filtros, sondeos de esquema y ejemplos. No cierra E0 ni
constituye un sandbox de proceso para SQL de autores hostiles.

## Frontera implementada

`QueryService` es el camino común de esas operaciones. Autor y lector ejecutan
una sola consulta de lectura. DDL/DML, múltiples sentencias, `SELECT INTO`,
instalación/carga de extensiones y cambios de configuración quedan rechazados.
La autorización del panel ocurre antes; el lector solo ejecuta SQL guardado,
con valores enlazados, y no persiste inferencia ni aprendizaje.

Cada operación crea un DuckDB independiente en memoria. **Nunca adjunta el
archivo del proyecto.** No hereda tablas de aplicación, macros, variables,
conexiones adjuntas ni secretos. El directorio de secretos es temporal y vacío.
Antes de ejecutar SQL del usuario se desactiva acceso externo y se bloquea la
configuración. También están desactivadas las extensiones comunitarias,
autoinstalación, autocarga y búsquedas de objetos Python.

Son controles documentados por DuckDB: [restricción de archivos y configuración](https://duckdb.org/docs/current/operations_manual/securing_duckdb/overview)
y [control de extensiones](https://duckdb.org/docs/current/operations_manual/securing_duckdb/securing_extensions).
Un AST de lectura sigue siendo una política de sentencias; la separación física
del catálogo y la configuración del motor impiden que SELECT alcance el proyecto.

## Compatibilidad con archivos existentes

El formato `.sqlviz` anterior mezcla metadatos y posibles tablas analíticas. No
se migra ni vacía el archivo. El adaptador identifica tablas físicas locales
referenciadas por la consulta, respetando CTEs y subconsultas. Exporta únicamente
esas tablas a Parquet temporal y las carga en el catálogo analítico.

La conexión de metadatos ejecuta solo SQL construido por el adaptador con
identificadores escapados y rutas propias; jamás la consulta, predicados o
funciones del usuario. Los nombres reservados de aplicación están registrados
en `sqlviz_storage.schema.APPLICATION_TABLES`, con una prueba que compara el
registro contra todo el esquema. Prefijos internos y tablas del aprendizaje
también se excluyen.

Soportado: SELECT/WITH/UNION, VALUES, funciones locales como `range`, tablas
físicas locales y esquemas explícitos, filtros enlazados, decimales y tipos
representables en Parquet. Un sondeo de esquema agrega `LIMIT 0`; no depende de
que enlazar NULL deje el resultado vacío.

**Cambio de comportamiento:** SQL de gráficos ya no crea/modifica tablas ni
consulta archivos, red, vistas locales, macros del proyecto o catálogos adjuntos.
Las vistas se rechazan explícitamente: evaluarlas en la conexión original podría
leer metadatos o recursos externos. Referencias con catálogo explícito también se
rechazan. Ingesta, conexiones externas y vistas requieren adaptadores de datasets
posteriores; no existe todavía una UI para importarlas en este contexto.

## Presupuestos iniciales

Se configuran por aplicación con `create_app(..., query_limits=QueryLimits(...))`.
El cliente no puede aumentarlos desde la solicitud.

| Recurso | Valor predeterminado | Comportamiento al excederlo |
| --- | --- | --- |
| Tiempo de snapshot, SQL y lectura de resultados | 10 segundos | 408 / `query_timeout`; interrupción del motor |
| Ejecuciones simultáneas | 2 por aplicación | 429 / `query_busy`; sin cola ilimitada |
| Filas de resultado | 10 000 | 413 / `row_limit` |
| JSON de filas de resultado | 8 MiB | 413 / `result_limit` |
| Filas del conjunto de tablas fuente | 100 000 | 413 / `source_limit` |
| Parquet del conjunto de fuentes | 64 MiB | 413 / `snapshot_limit` |
| Tablas fuente | 16 | 413 / `source_limit` |
| SQL ejecutado | 100 000 bytes UTF-8 | 413 / `sql_limit` |
| Memoria del catálogo analítico | 256 MB | 413 / `memory_limit` |
| Hilos / spill del catálogo analítico | 2 / desactivado | Sin crecimiento de archivos de spill |

No se devuelve un agregado calculado sobre una fuente truncada ni un gráfico con
filas omitidas silenciosamente. El autor debe agregar, filtrar el dataset fuente
o reducir su tamaño; `LIMIT` en el resultado no evita el límite del snapshot.

Errores de política y acceso externo retornan 403 con `detail` y `code`.
Los límites y denegaciones tampoco se convierten en un dominio vacío o un
fallback exitoso. Los errores ordinarios conservan por ahora el contrato previo:
fallback de sintaxis del autor, 422 de ejecución y dominio best-effort.

## Ownership y decisiones de arquitectura

| Componente | Responsabilidad |
| --- | --- |
| `services/query_policy.py` | Elegibilidad de una sentencia de lectura |
| `services/queries.py` | Admisión, catálogo aislado, adaptación de tablas locales, presupuestos y resultado tipado |
| `schema.py` | Nombres de almacenamiento reservados |
| `dependencies.py` | Inyectar servicio por aplicación y cursor prestado por solicitud |
| Routers | Autorizar recurso, preparar filtros/inferencia y construir respuesta |
| `main.py` | Configuración y traducción de `QueryFailure` a HTTP |

El servicio no importa FastAPI. No incorpora repositorios genéricos ni un motor
distribuido. La extracción de un protocolo de adaptadores se hará al añadir el
segundo proveedor real. El resultado mantiene el contrato de gráficos existente.

El temporizador interrumpe solo el cursor de origen prestado y el catálogo de
esa operación; se cancela y se espera su cierre antes de cerrar la conexión.
El catálogo y sus archivos temporales se liberan ante éxito, límite o rechazo.
La plaza de concurrencia se devuelve también ante excepciones.

## Límites pendientes

- El snapshot por consulta tiene coste de copia y disco. No es la solución
  definitiva para datasets grandes; falta almacenamiento analítico propio,
  adaptadores, revisiones, frescura y caché con contexto de autorización.
- Copias de varias tablas no comparten todavía una transacción de snapshot.
  No prometer consistencia de una misma revisión bajo escrituras concurrentes.
- Parquet no preserva todas las identidades de tipos exclusivos de DuckDB.
  Ampliar pruebas de contrato cuando se soporten esos tipos como datasets.
- El límite de bytes Parquet se verifica después de cada exportación, y el de
  resultado después de materializar cada lote/celda. No son cuotas duras de SO.
  La memoria del cursor de origen y los objetos Python no quedan cubiertos por
  el `memory_limit` del catálogo nuevo.
- El presupuesto de tiempo comienza tras parsear y abrir el catálogo; no cubre
  inferencia ni toda la duración HTTP. `interrupt()` es cancelación cooperativa,
  no terminación forzada de un proceso. No hay aún cancelación desde la UI.
- La [cuarta unidad](sqlviz-parameters-and-quality.md) incorpora contrato tipado
  de transporte y límites de cuerpos/valores. Faltan declaraciones persistidas de
  parámetros y políticas RLS/columnas. Un filtro de negocio no es autorización.
- Quack opt-in conserva acceso privilegiado a la base original. Su credencial
  pertenece al operador; no es un transporte permitido para lectores.

## Validación

Pruebas reales con DuckDB y TestClient: tablas reservadas y mayúsculas, acceso
indirecto con `query_table`, enumeración de catálogo, secretos/macros/vistas,
archivos existentes, catálogos adjuntos, DDL y múltiples sentencias. Casos HTTP
para autor y lector incluyen ejecución, sondeo/reveal y dominios de filtros.

Presupuestos probados con fuentes y resultados que exceden sus límites;
interrupción real de una agregación costosa y ejecución posterior válida;
concurrencia por aplicación, devolución de plazas y cursores independientes.
Un archivo de proyecto sintético se reabre conservando datos y credenciales;
se verifica limpieza de temporales también ante errores. Ninguna prueba usa
archivos de proyectos reales del usuario.

- Suite Python completa: **1559 pasan, 3 omitidas**, en **114,52 s**; incluye
  **62 casos nuevos** de aislamiento/presupuestos y flujos HTTP. Comando:
  `.venv/Scripts/python.exe -m pytest -q --tb=short --basetemp build/query-review/pytest-final-02`.
- Ruff correcto para API y registro del esquema. Mypy correcto para API/CLI
  (**26 archivos**). El chequeo global (**120 archivos**) conserva un error previo
  en `sqlviz-inference/filters/neutralize.py:46`; no se presenta como chequeo global limpio.
- Chromium con frontend de producción y backend real actualizado: login de
  autor, dashboard/workspace públicos y con contraseña, gráficos visibles,
  credenciales por solicitud y retirada de datos tras revocación. **Sin errores
  de página**. Reporte local ignorado por git: `build/query-review/browser-report.json`.
  El servidor de ensayo usó bases en memoria y se cerró al terminar. No se reinició
  la demo abierta del usuario ni se modificaron sus proyectos.
- No se modificó frontend en esta unidad; la revisión de navegador utilizó el
  build validado en la segunda unidad. Validación local Windows/Python 3.13;
  CI Python 3.12 y pruebas de otros sistemas siguen siendo verificación aparte.

La carpeta de `--basetemp` es exclusiva del ensayo: pytest puede eliminarla al
reutilizarla. No usar una carpeta con datos personales.

**Continuación entregada:** [parámetros y controles de calidad de E0](sqlviz-parameters-and-quality.md).
E1 abordará persistencia transaccional, identidad de
paneles y contrato visual antes de concentrar el trabajo en Dashboard Studio.
