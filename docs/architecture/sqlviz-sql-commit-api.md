# API de snapshots y guardado del script

**Implementado — 2026-10-09: S1.1c.2a.** HTTP tipado y autorizado sobre el
[escritor transaccional](sqlviz-sql-atomic-writer.md). Guarda las definiciones de
un dashboard existente en una sola transacción. **Run integrado después en
[S1.1c.2b](sqlviz-sql-run-atomic-commit.md)**. Esta API no activa arrastre,
Visual Builder, datasets compartidos ni publicación de revisiones del viewer.

## Recorrido y responsabilidad de cada capa

1. El autor obtiene `GET /api/v1/dashboards/{id}/sql-script`.
2. Confirma decisiones explícitas para cada sentencia y panel anterior.
3. Envía `POST /api/v1/dashboards/{id}/sql-script/commit` con el token leído.
4. La aplicación analiza toda la fuente con DuckDB y aplica a cada sentencia la
   misma política de consulta de lectura y presupuesto SQL que la ejecución.
5. El repositorio comprueba de nuevo la revisión y la reconciliación contra el
   estado real dentro de la transacción. Devuelve el resultado después de COMMIT.

[SqlAuthoringService](../../packages/sqlviz-api/src/sqlviz_api/services/sql_authoring.py)
coordina admisión y persistencia sin depender de DTO HTTP.
El [router](../../packages/sqlviz-api/src/sqlviz_api/routers/sql_script_commits.py)
adapta solicitudes/respuestas, y su registro exige `require_admin`.
La [política pura](sqlviz-sql-identity-reconciliation.md) decide si las asociaciones
están completas; almacenamiento asigna UUID y confirma el conjunto.
El preflight `/api/v1/sql/reconcile` sigue siendo una propuesta sin escrituras,
no una reserva ni una autorización para saltarse la comprobación del commit.

## Snapshot

La respuesta tiene `version: 1`, `dashboard_id`, `revision`, `draft_source`,
`panels` y `publication`. Cada panel expone ID, nombre, SQL y orden. La lista se
ordena por `sort_order`, fecha de creación e ID para resolver empates.
La revisión cubre también los ajustes y campos persistidos que no se incluyen
en esta respuesta mínima. **Es un token de estado, no una credencial.**

`publication` es `null` si nunca se publicaron asociaciones explícitas, o si una
operación legacy cambió SQL o el conjunto de paneles. No se reconstruye por orden
o igualdad de consultas. Cuando existe, contiene `version: 1`, contador positivo
`revision`, `source` exacta y `bindings`: índice de sentencia, ID de panel y
`start_offset`/`end_offset` UTF-16, con fin exclusivo, compatibles con Monaco.

`draft_source` puede diferir de `publication.source`: un autoguardado legacy del
borrador no cambia por sí solo las asociaciones de la última fuente confirmada.
La futura restauración deberá verificar fuente exacta o procedencia de edición.
GET no analiza SQL, ejecuta consultas ni escribe asociaciones. Ambas rutas usan
`Cache-Control: no-store`.

## Commit estricto

Los [contratos](../../packages/sqlviz-api/src/sqlviz_api/sql_commit_contract.py)
están publicados en OpenAPI. Los tres campos son obligatorios:

```json
{
  "sql": "SELECT region, revenue FROM sales; SELECT count(*) FROM sales",
  "expected_revision": "sql-script-v1:0000000000000000000000000000000000000000000000000000000000000000",
  "decisions": [
    {"kind": "keep", "statement_index": 0, "panel_id": "panel-existente"},
    {"kind": "create", "statement_index": 1, "creation_key": "nuevo-resumen"},
    {"kind": "remove", "panel_id": "panel-retirado"}
  ]
}
```

El token del ejemplo es ilustrativo: usar el del GET del dashboard destino.
Conservar requiere un panel de ese dashboard; crear usa una clave de correlación
del borrador; eliminar exige una decisión expresa. Todas las sentencias y todos
los paneles anteriores deben resolverse una sola vez. Dos sentencias idénticas
no comparten identidad automáticamente. Un script vacío puede retirar todos los
paneles, pero solo si cada eliminación está confirmada explícitamente.

Se rechazan campos extra, coerción de tipos, índices fuera de rango, decisiones
desconocidas, IDs duplicados o ajenos y propuestas incompletas. El navegador no
envía slices SQL, rangos, planes calculados ni IDs para nuevas creaciones.

La respuesta `200` contiene `version: 1`, el `snapshot` confirmado y
`created_panels: [{creation_key, panel_id}]`. Solo este resultado confirma el
guardado de definiciones; no equivale a consulta ejecutada o gráfico actualizado.
Los errores de ejecución posteriores no deben deshacer el commit ni señalarlo
como no guardado. No se modifican `last_run_sql` ni `last_run_at` aquí.

## Autorización, admisión y presupuestos

En modo normal ambas rutas exigen la sesión admin del proyecto. Sin ella se
devuelve `401`. Un encabezado de share recibe `403`, incluso si el cliente tiene
también cookie admin. Shares públicos/privados y sesiones viewer no habilitan
lectura de este snapshot de autor ni escritura, para dashboards propios,
ajenos o inexistentes. El modo demo conserva el bypass explícito de autor existente.
No se añaden roles de equipo en este incremento.

El parsing nativo debe aceptar el script completo; después cada sentencia pasa
por `QueryService.validate`. DDL/DML se rechazan; una forma que DuckDB ya rechaza
por sintaxis termina antes en `sql_script_invalid`. Sintaxis nativa aceptada que
la validación analítica no pueda interpretar produce un error seguro, sin eco de SQL.

**Esta admisión no ejecuta ni vincula tablas, comprueba esquema o infiere gráficos.**
Puede guardar una consulta de lectura que luego falle por tabla inexistente,
parámetro sin valor o restricción de acceso a una fuente. Los controles de catálogo,
funciones externas y recursos de ejecución siguen en el camino de ejecución.
No usar estas definiciones como evidencia de que un resultado se puede obtener.

Límites: cuerpo HTTP total de 1 MiB antes de parsear JSON; fuente de hasta 1 MiB
UTF-8 en el servicio; hasta 256 sentencias y 256 paneles anteriores, y 512 decisiones.
El JSON y sus escapes consumen también el presupuesto HTTP, por lo que una fuente
en el límite no tiene garantizada su admisión por HTTP. Cada consulta tiene el
presupuesto SQL de la aplicación, 100.000 bytes UTF-8 por defecto. Las asociaciones
persistidas tienen su propio límite de 256 KiB. No se amplían presupuestos de
ejecución para poder guardar scripts grandes.

## Errores y recuperación

| Estado | Caso y código cuando corresponde |
| --- | --- |
| 401 / 403 | Sesión ausente / acceso de viewer o share; `query_policy` si la sentencia incumple lectura |
| 404 | Dashboard inexistente para un autor autorizado |
| 409 | Estado obsoleto o conflicto transaccional: `sql_script_write_conflict` |
| 413 | `body_limit`, `sql_script_limit`, `sql_limit`, `sql_reconciliation_limit` o `sql_script_state_limit` |
| 422 | Validación de transporte, `sql_script_invalid`, `sql_commit_query_invalid`, o error `sql_reconciliation_*` |
| 429 | Análisis nativo ocupado: `sql_parse_busy`; reintentar después, sin escrituras |
| 500 | Asociaciones almacenadas corruptas: `sql_script_metadata_invalid`; requiere reparación |

Los errores de dominio exponen `detail` y `code`; la validación de transporte usa
el detalle estructurado existente, sin incluir los valores de entrada. Los
conflictos y errores de metadata no revelan SQL ni mensajes internos de DuckDB.
Otros fallos inesperados conservan el tratamiento general de error del servidor;
no existe reparación automática de schema o proyecto.

Ante `409`, obtener un snapshot nuevo y revisar las decisiones antes de intentar
guardar otra vez. No reemplazar el token y reenviar silenciosamente. Si se pierde
una respuesta después del COMMIT, reenviar el token anterior devuelve conflicto
y no crea duplicados; no hay caché de respuestas idempotentes. La recuperación
en UI y la distinción draft/guardado/ejecutado se cierran en S1.1c.2c.

## Evidencia y siguiente parte

Pruebas HTTP sobre proyectos aislados verifican permisos antes de acceder a DB
o parser, contratos estrictos, SQL nativo/UTF-16, IDs asignados, conservación de
presentación, eliminación expresa, rollback tras mutaciones, tokens obsoletos,
respuesta repetida, límites, metadata corrupta y guardar/reabrir un archivo.
No se prueban escribiendo sobre el proyecto del usuario.

Validación local: **2.441 pruebas correctas y tres omitidas** en la suite Python
completa; **118 casos focalizados** después de los ajustes finales de admisión y
OpenAPI. Ruff y mypy pasan. No hay cambios de frontend en esta entrega.

**S1.1c.2b entregado:** Run usa un único commit y separa ejecución/composición.
Siguiente: S1.1c.2c, recarga, autoguardado, recuperación y revisión ejecutada.
Ver el [plan operativo](sqlviz-studio-delivery-plan.md).
