# Cierre verificado de Run

**Implementado — 2026-10-09: S1.1c.2c.1c.** La última ejecución se registra por
un endpoint de autor con prueba del servidor y precondición de definición vigente.
Run deja de enviar SQL/timestamp mediante PATCH. Este incremento cierra el registro
de éxito de S1.1c.2c.1; recarga entregada en
[2c.2](sqlviz-sql-snapshot-reload.md), recuperación pendiente en 2c.3.

## Qué se verifica

La [referencia de definición de 1b](sqlviz-sql-execution-definition.md) expresa
procedencia, pero un autor podría declararla sin ejecutar consultas. Por eso no
basta para registrar éxito. La API incorpora dos recibos opacos firmados mediante
HMAC-SHA256, con una clave aleatoria de 256 bits privada a cada instancia de app:

1. La ejecución ligada a definición devuelve `execution_receipt` y
   `query_executed`. Firma dashboard/revisión, ID del panel, hash del contrato de
   inferencia exacto y si realmente se ejecutó. Una consulta real lo emite después
   del commit de inferencia; un fallback lo emite tras verificar la definición,
   con resultado de ejecución falso. No contiene SQL ni filas analíticas.
2. `/sql-script/compose` comprueba definición, cobertura/orden de bindings y, si
   hay recibos, firma, vigencia, ID y hash de cada inferencia. No confía en un
   booleano suministrado por el cliente. Comprueba también que el motor produzca
   exactamente todos los IDs, una vez cada uno. Solo después de componer un lote
   no vacío de consultas realmente ejecutadas emite `completion_receipt`.

Una consulta que devuelve cero filas sí puede ejecutarse correctamente. Un HTTP
200 de fallback, incluso si permite mostrar filtros, no produce éxito analítico.
Un script vacío tampoco. Las composiciones de autor sin recibos mantienen el
contrato de 1b, pero reciben `completion_receipt: null`. Filtros/lectores legacy
conservan su API y no producen estos recibos.

Los IDs/definición se vinculan mediante hashes de tamaño fijo, incluidos IDs
legacy Unicode de 256 caracteres. El contrato de inferencia se normaliza por
semántica numérica JSON: `1.0`/`1` y `-0.0`/`0` conservan la firma tras pasar por
el navegador; cambios de campos/valores la invalidan.

Los tokens miden como máximo 2.048 caracteres y caducan a los 15 minutos de su
emisión. La firma se compara en tiempo constante antes de decodificar los claims.
Las claves y recibos no se guardan en el proyecto ni se exponen en logs. Un reinicio
de app invalida las operaciones pendientes; un proyecto/app diferente tampoco
puede verificar los recibos. Estos límites son explícitos para el despliegue
actual de una instancia, no una solución de coordinación entre múltiples workers.

## Registro condicionado

`POST /api/v1/dashboards/{id}/sql-script/complete` requiere autor y recibe solo:

```json
{
  "definition": {"version": 1, "dashboard_id": "...", "revision": "sql-definition-v1:..."},
  "completion_receipt": "..."
}
```

Exige un recibo de composición válido de ese dashboard/definición. Un recibo de
ejecución individual no lo reemplaza. No acepta SQL o timestamp del cliente.
El repositorio, independiente de HTTP y de la firma, abre una transacción breve:

- Escribe realmente la fila del dashboard para establecer conflicto con commits,
  borrado y otros cierres concurrentes, y verifica el snapshot completo esperado.
- Obtiene `last_run_sql` de la fuente exacta de la publicación persistida.
- Modifica los timestamps de todos los paneles del dashboard, hasta 256, para
  detectar también cambios/borrados legacy de vecinos posteriores a la lectura.
- Guarda conjuntamente SQL y timestamp de composición generado por el servidor.
  No cambia `sql_content`, nombres, ajustes, asociaciones ni inferencias.

Un cambio de definición, conflicto de escritura o COMMIT fallido revierte todas
las escrituras propias. Un recibo de una composición anterior no puede reemplazar
una última ejecución más reciente. Reintentar el mismo recibo válido devuelve el
mismo SQL/timestamp, aunque las fechas de modificación de metadata pueden cambiar.
No es un registro durable de IDs de operaciones ni recuperación tras reinicio.

La respuesta contiene `definition`, `last_run_at` y `last_run_sql`. El frontend
comprueba los tres antes de adoptar la última ejecución. Ya no genera su reloj
local para ese registro ni reescribe un borrador que cambió durante Run. Si falla
el cierre, conserva los IDs y resultados del lote completo con un error explícito;
no afirma que el registro haya tenido éxito. Un lote con fallbacks conserva sus
controles y resultados disponibles, pero no modifica la última ejecución exitosa.

## Contratos y seguridad

`last_run_at` y `last_run_sql` siguen en GET/listado, pero dejan de ser campos de
`DashboardUpdate`. Cualquier PATCH que los incluya, incluso null o junto a un
borrador válido, devuelve 422 sin guardar nada. La normalización/repo internos
pueden seguir usando esos campos para operaciones confiables y fixtures legacy.
Actualizar frontend/backend juntos; el frontend nuevo no usa el cierre legacy.

Una prueba inválida, expirada o de otra app devuelve 409 con código
`sql_run_receipt_invalid`, sin revelar claims, SQL ni valores privados. Una
definición cambiada/recibo anterior a un cierre más reciente devuelve 409 con
`sql_definition_conflict`; los contratos inválidos devuelven 422. Shares y
solicitudes anónimas no pueden registrar éxito.

## Límites y siguiente paso

Los recibos prueban hechos observados por esta instancia, no un snapshot analítico
común entre consultas ni permanencia de las filas después de ejecutarlas. El hash
protege el contrato de inferencia utilizado al componer, no certifica filas enviadas
al navegador. La firma tampoco representa una publicación estable del viewer.
Una edición posterior a un cierre válido sigue siendo posible.

No se incorpora una migración ni un ledger de ejecuciones. La recuperación durable
de respuesta perdida/reinicio, coherencia amplia entre editores y publicación
del viewer siguen en sus entregas respectivas. Recarga de bindings y compatibilidad
de caché con definiciones están entregadas en [2c.2](sqlviz-sql-snapshot-reload.md).
Un reintento válido de
complete no resuelve todavía la respuesta perdida de un commit de definiciones.

Se verifican contratos, firmas/IR/paneles incompatibles, expiración/reinicio,
fallback y cero filas, cobertura del motor, permisos, PATCH protegido, fuente
exacta/borrador, reintentos y orden de cierres. Cursores reales ejercitan cambios
de SQL/borrado después de la lectura y rollback ante COMMIT fallido. Chromium
ejercita Run completo y la carrera posterior a composición sobre una copia de
preview; artefactos en `build/sql-run-completion-review/`, ignorados por Git.

Validación: suite completa Python **2.540 aprobadas / 3 omitidas**, más una pasada
final de **67 casos de recibos, definición y cierre** que incluye los nuevos
casos de normalización JSON, IDs Unicode máximos y dashboard eliminado. Frontend:
**304 pruebas**, check sin errores/advertencias y build de producción correcto.
Ruff y mypy sin errores (152 archivos fuente). Chromium: cinco commits, dos
cierres verificados, cero escrituras legacy de última ejecución, acciones en
desktop/móvil y cero errores JavaScript. Una edición real entre composición y
cierre devuelve 409, conserva IDs y borrador nuevo y no registra éxito. Preview
actualizada mediante cierre ordenado y copias de respaldo, sin tocar el proyecto
o aprendizaje reales. Persisten los avisos conocidos de teardown Svelte y chunks.

Ver el [plan operativo](sqlviz-studio-delivery-plan.md). La recarga de snapshots
y asociaciones confirmadas está entregada en [2c.2](sqlviz-sql-snapshot-reload.md).
Sigue **S1.1c.2c.3**: borrador/autoguardado, conflicto y respuesta perdida.
