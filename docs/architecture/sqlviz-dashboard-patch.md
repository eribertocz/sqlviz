# Contrato PATCH de dashboards

**Estado:** implementado localmente el 2026-10-07, como segundo incremento de
la unidad 8 de E1, después de [composición tipada](sqlviz-composition-contract.md).
El [PATCH básico del panel](sqlviz-panel-patch.md) se implementa en el tercer
incremento; [presentación](sqlviz-panel-presentation.md) se entrega en el cuarto.
La revisión de overrides sigue pendiente. No cambia el esquema `.sqlviz`, el
algoritmo de inferencia ni el contrato visual aceptado para el Studio.

## Semántica de actualización

`PATCH /api/v1/dashboards/{dashboard_id}` requiere autorización de autor y recibe
un objeto con los campos que se quieren modificar. Un campo omitido conserva su
valor. `null` borra únicamente un campo nullable; no significa omisión. `{}`
devuelve el dashboard existente sin escribir ni cambiar `updated_at` o la revisión
del árbol de carpetas. Un dashboard inexistente devuelve 404, también para `{}`.

| Campo | Valor admitido | `null` explícito |
| --- | --- | --- |
| `name` | String con texto, hasta 256 caracteres; conserva espacios originales | Rechazado |
| `folder_id` | ID de hasta 256 caracteres; destino y ascendencia válidos | Mueve a raíz |
| `connection_id` | Referencia opaca de hasta 256 caracteres | Quita la referencia |
| `sort_order` | Entero estricto entre −2³¹ y 2³¹−1, incluido cero | Rechazado |
| `description` | String de hasta 16 384 caracteres | Borra la descripción |
| `sql_content` | Texto exacto del borrador, hasta 1 MiB en UTF-8; `""` válido | Rechazado |

**Actualización S1.1c.2c.1c — 2026-10-09:** `last_run_at` y `last_run_sql` son
campos de respuesta administrados por el servidor. Incluirlos en PATCH, incluso
con null, devuelve 422 sin guardar ningún campo. El [cierre verificado de Run](sqlviz-sql-run-completion.md)
los guarda con prueba del servidor y definición vigente. Core/repositorio siguen
validando esos campos para escrituras internas confiables, sin admitirlos por HTTP.

Los IDs compuestos solo por espacios se rechazan. `""` se normaliza a `null` en
`folder_id`, `connection_id` y `description`; conserva el borrado heredado de
ubicación/descripción y evita una referencia de conexión vacía. Esta normalización
no se aplica a SQL. Los strings deben poder codificarse como UTF-8.

No se convierten números a strings, booleanos a enteros, strings numéricos a
enteros ni floats a enteros. Campos desconocidos, incluidos `id`, `updated_at`,
`dashboard_hint` y `dashboard_domain`, se rechazan. Estos dos últimos siguen
presentes en la respuesta, pero no son editables mediante este PATCH.

Ejemplo: `{"description": null, "sql_content": ""}` borra la descripción y deja
vacío el borrador; conserva carpeta, conexión y última ejecución. Si cualquiera
de los campos de una solicitud es inválido, ninguno se guarda.

El cuerpo HTTP completo mantiene el límite existente de **1 MiB antes de JSON**,
también con envío por chunks. La envoltura JSON, los escapes y los campos combinados
cuentan para ese presupuesto, por lo que un texto de exactamente 1 MiB admitido
por core no cabe necesariamente en una solicitud HTTP. El límite de guardar un
borrador es independiente del presupuesto por sentencia al ejecutar SQL.

## Responsabilidades de arquitectura

- [Core](../../packages/sqlviz-core/src/sqlviz_core/models/dashboards.py) define
  `Dashboard`, `DashboardChanges`, límites y normalización sin HTTP, Pydantic
  ni DuckDB. La normalización devuelve una copia y conserva omisión y SQL exacto.
- [Contrato HTTP](../../packages/sqlviz-api/src/sqlviz_api/models.py) rechaza
  extras y coerción con Pydantic; entrega solo campos presentes y reutiliza
  las reglas de core. La validación posterior rechaza `null` en los tres campos
  no borrables, aunque sus anotaciones opcionales permiten representar omisión.
- [Repositorio](../../packages/sqlviz-storage/src/sqlviz_storage/dashboard_repository.py)
  valida también llamadas directas, concentra adaptación de filas y lecturas,
  y aplica el cambio dentro de una transacción. No depende de FastAPI.
- [Router](../../packages/sqlviz-api/src/sqlviz_api/routers/dashboards.py) adapta
  solicitud/respuesta y delega el guardado. No necesita un servicio adicional
  que repita una única operación del repositorio.

Los valores SQL se enlazan como parámetros. Los nombres de columnas solo se
interpolan después de comprobar la lista de campos permitidos en core.

## Atomicidad y concurrencia

Una actualización no vacía lee el dashboard, modifica todos los campos y su
timestamp, y lee el resultado dentro de la misma transacción. Solo devuelve
ese resultado después de un commit confirmado. Fallos de escritura, lectura
posterior o commit deshacen todos los cambios; el timestamp también se revierte.
Se usa precisión de microsegundos y se evita escribir un timestamp idéntico
al anterior, para establecer un conflicto real sobre la fila del dashboard.

Si se proporciona `folder_id`, la operación reutiliza la transacción y revisión
del [árbol de carpetas](sqlviz-folder-integrity.md). Validación del destino,
ubicación, otros campos y timestamp se confirman juntos, sin transacciones
anidadas. Los cambios sin ubicación no escriben esa revisión.

Los cursores independientes de las solicitudes comparten las garantías de
conflicto de DuckDB. La actualización compite sobre el mismo dashboard con
ediciones, borrado y creación dependiente protegida por `dashboard_write`.
Una actualización de otro dashboard sin cambio de carpeta puede confirmarse
durante esa operación. Un lector con una transacción abierta mantiene su
snapshot anterior hasta terminarla.

| Respuesta | Condición |
| --- | --- |
| 200 | Guardado confirmado, o lectura sin escritura para `{}` |
| 422 | Tipo, campo, rango, texto o timestamp inválido; destino inexistente (`folder_parent_not_found`) o ascendencia no válida según la política de carpetas |
| 404 | Dashboard inexistente; `dashboard_not_found` |
| 409 | Conflicto de escritura: `dashboard_write_conflict`, o `folder_write_conflict` si participa ubicación; jerarquía histórica corrupta según la política existente |
| 413 | Cuerpo HTTP excede el presupuesto; `body_limit` |

Los errores de validación conservan `detail: [{type, loc, msg}]`, sin devolver
valores enviados ni contexto de excepciones. Los conflictos no exponen mensajes
internos de DuckDB. No se promete precedencia entre errores distintos en una
solicitud inválida. La autorización existente conserva sus propias respuestas.

## Compatibilidad y límites

El autoguardado existente conserva borradores vacíos, comentarios, saltos de
línea, Unicode y puntos y coma. El timestamp ISO emitido por JavaScript sigue
siendo válido. Guardar solo el borrador no cambia los campos de última ejecución.
Una columna histórica `sql_content` con NULL sigue leyéndose como `""`; no se
reparan filas ni se abre el archivo real del usuario para probar este cambio.

Este incremento no endurece `DashboardCreate` ni los PATCH de paneles. No verifica
la existencia de `connection_id`: el catálogo y su política de referencias aún
están pendientes. `last_run_at` y `last_run_sql` siguen siendo campos enviados por
el autor; validarlos no demuestra que ese SQL haya sido ejecutado por el servidor.

El conflicto transaccional no equivale a edición condicional por revisión:
dos solicitudes sucesivas válidas pueden sobrescribir el mismo campo. El cliente
debe refrescar antes de reintentar un 409; no hay reintento automático del servidor.
La interfaz actual no incorpora en este incremento avisos ni recuperación de
conflictos del autoguardado. ETag/revisión, coordinación entre pestañas y recuperación
visible se diseñarán conjuntamente con identidad y revisiones persistidas.

## Evidencia de verificación

Las pruebas nuevas cubren tres fronteras:

- [Política pura](../../packages/sqlviz-core/tests/test_dashboard_policy.py):
  presencia/null, tipos estrictos, límites exactos, bytes UTF-8, timestamp y
  conservación del texto y del objeto de entrada.
- [Repositorio real](../../packages/sqlviz-storage/tests/test_dashboard_update.py):
  rollback de campos/revisión, fallo de lectura después de escribir, fallo de
  commit, reapertura de archivos sintéticos, snapshots y conflictos entre
  cursores, incluido borrado entre lectura y actualización.
- [API](../../packages/sqlviz-api/tests/test_dashboard_patch.py): rechazo completo
  antes de guardar, limpieza de campos, borrador exacto, PATCH vacío, conflictos
  y rollback con y sin cambio de carpeta.

La suite existente también ejercita listados, creación, borrado, carpetas,
ejecución, autorización y viewers. Logs de revisión bajo
`build/dashboard-patch-review/`, ignorados por Git. Los temporales de pytest
usan subdirectorios nuevos de esa ruta debido a permisos del directorio temporal
predeterminado de Windows.

Validación local del 2026-10-07:

- **86 casos nuevos** de política, repositorio y API pasan dentro de la suite
  completa: **1968 pruebas pasan y 3 se omiten**, en 170,14 s.
- Las 83 pruebas existentes enfocadas de dashboards, borradores, explorer,
  carpetas y repositorio también pasaron antes de ampliar la suite.
- `ruff check packages/` y mypy estricto de los cinco paquetes Python pasan
  (132 archivos de código revisados por mypy).
- 90 enlaces locales de los Markdown cambiados verificados y `git diff --check`
  sin errores. Sin cambios de frontend: no se vuelve a ejecutar su build local;
  las pruebas HTTP usan el artefacto existente y CI construye el suyo.

CI remoto se verifica sobre el commit enviado; estos checks locales no certifican
E1 completo ni calidad del futuro Studio.
