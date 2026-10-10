# Run ligado a una definición de SQL

**Implementado — 2026-10-09: S1.1c.2c.1b.** El commit de Run devuelve una
referencia de definición que acompaña cada consulta y la composición. Si cambia
la definición esperada, Run falla de forma explícita; no adopta el SQL nuevo como
si hubiera ejecutado el que el autor confirmó.

La [publicación de inferencia de 1a](sqlviz-inference-publication.md) comprueba los
inputs leídos por una consulta. Este incremento conecta esa comprobación con el
[commit confirmado por Run](sqlviz-sql-run-atomic-commit.md) y el conjunto completo
de paneles del script. El [registro condicionado de 1c](sqlviz-sql-run-completion.md)
está entregado y añade recibos firmados; las referencias de 1b siguen sin ser firmas.

## Dos referencias con responsabilidades diferentes

| Campo del snapshot | Qué cubre | Uso |
| --- | --- | --- |
| `revision`, prefijo `sql-script-v1:` | Todo el estado persistido, incluidos borrador, timestamps, ajustes e inferencia | Precondición del commit de definiciones |
| `definition_revision`, prefijo `sql-definition-v1:` | Dashboard, contador/fuente/bindings confirmados, IDs/SQL/orden actuales | Precondición de ejecución y composición de Run |

`definition_revision` tiene 82 caracteres: prefijo y SHA-256 hexadecimal. Es
`null` cuando no existen asociaciones confirmadas compatibles; no fabrica
identidad para proyectos legacy. Cambia al guardar otro commit, incluso si repite
la misma fuente. Un cambio de SQL/IDs/orden legacy invalida o cambia la referencia.
No depende de nombres, título, tamaños, borrador, inferencia o timestamps.

Una transición legacy SQL A → B → A no crea por sí sola una generación durable
distinta. La referencia compara la definición compatible actual y el contador
de commits explícitos; no representa un historial completo de todas las mutaciones.
No es una credencial, publicación del viewer ni snapshot de las filas analíticas.

## Ejecución ligada a la definición

`POST /api/v1/panels/{id}/execute` admite `definition` opcional junto con sus
variables existentes. La referencia contiene `version: 1`, `dashboard_id` y
`revision`. Versiones booleanas, flotantes o de texto no se convierten a entero.

Cuando se proporciona una referencia:

1. Exige autor y comprueba el acceso al panel antes de leer la definición.
2. Lee un snapshot consistente de metadata, comprueba la referencia y pertenencia
   del panel y captura el SQL de esa definición. No ejecuta una definición
   distinta por haber releído después el panel desde otra solicitud.
3. Ejecuta en el catálogo analítico aislado e infiere sin transacción de proyecto.
4. En una consulta real, vuelve a comprobar el script dentro de la publicación
   transaccional de inferencia/clasificación. Además de la fila del padre, modifica
   realmente los timestamps de todos sus paneles para establecer conflicto con
   PATCH/borrado de un panel vecino, incluso cuando ese escritor legacy no toca
   al padre. El conjunto está limitado a 256 paneles.
5. Devuelve `execution_reference` con versión, ID de panel y definición. El cliente
   verifica esos campos antes de incorporar datos o enviar composición.

Los caminos de fallback por sintaxis o filtros también vuelven a verificar la
definición después de calcular y devuelven referencia; no publican inferencia.
Un HTTP 200 de fallback continúa significando ausencia de datos ejecutados, no
éxito analítico de todo el dashboard.

Los resultados de solicitudes sin `definition` conservan su formato anterior.
Lectores y filtros legacy siguen usando ese contrato. Un share no puede utilizar
la ejecución ligada a definiciones del autor; no se amplía su alcance.

## Composición ligada a la definición

`POST /api/v1/dashboards/{id}/sql-script/compose` exige autor y recibe:

- `definition`: referencia confirmada por Run.
- `panels`: resultados tipados con `panel_id`, `inference_result` y
  `execution_reference`, sin filas de datos.

Rechaza contratos inválidos o referencias declaradas mezcladas con **422**. En una
única transacción de lectura verifica la definición actual y exige exactamente
los IDs/orden de sus bindings, sin duplicados, omisiones o paneles añadidos. Lee
anchos fijados y compone sobre ese snapshot. Devuelve `rows` y la misma definición.
No ejecuta SQL ni modifica metadata.

El motor puede ordenar visualmente los paneles según su narrativa; el cliente
comprueba que la respuesta contenga exactamente el conjunto solicitado y une
filas analíticas solo por ID validado. La definición se comprueba también para
scripts vacíos. Run no recurre al endpoint legacy si esta composición falla.

El endpoint compartido `/api/v1/compose` mantiene su contrato de array y permisos.
Ambos caminos usan el mismo helper para llamar al motor y serializar el layout;
la autorización y propiedad de la transacción quedan en sus rutas respectivas.

## Conflictos y límites

Una definición ausente, cambiada, de otro dashboard o con cobertura de paneles
incompatible devuelve **409 / `sql_definition_conflict`**, sin SQL ni valores
privados. Un conflicto de escritura durante publicación conserva el **409 de 1a**
y revierte timestamps, inferencia y clasificación propios. Las asociaciones
corruptas siguen fallando de forma cerrada; no se convierten en una revisión nueva.

El frontend conserva los IDs del commit cuando falla una consulta, su referencia
o composición. No publica el lote parcial ni registra éxito en esos caminos. El
autor debe revisar/reintentar; no se cambia silenciosamente la revisión esperada.

La referencia de una respuesta describe su procedencia; no es una firma del
resultado ni prueba de que un cliente haya ejecutado consultas. Composición sigue
recibiendo inferencias del autor. **1c ya verifica recibos firmados del servidor
antes de registrar éxito; no confía en la referencia declarada.**

**1c reemplaza el PATCH de `last_run_at`/`last_run_sql`** por un cierre transaccional
con prueba de composición y definición vigente; se rechazan esos campos por PATCH.
No hay un snapshot analítico común del lote, protección de
todos los refrescos de filtros/lectores, publicación estable del viewer, adopción
idempotente tras respuesta perdida. La restauración de bindings al recargar se
incorpora en [2c.2](sqlviz-sql-snapshot-reload.md).

Las comprobaciones corresponden a instantes consistentes de metadata; otro autor
puede editar después de una respuesta válida. No se mantiene una transacción
abierta durante todo Run. Las barreras de escritura de publicación se acotan a
un dashboard; otros dashboards pueden seguir guardando. La contención/costo del
conjunto de hasta 256 filas se medirá antes de ampliar el modelo de datasets.

## Evidencia y siguiente incremento

Pruebas HTTP cubren consultas normales y los tres fallbacks, cambios antes/después
de consultar, cambio de otro panel, commit idéntico nuevo, composición incompleta,
orden/IDs/referencias inválidos, script vacío, estabilidad ante borrador/ajustes y
permisos. Pruebas con cursores reales ejercitan cambios posteriores a la lectura,
competencia de PATCH/borrado/commit y escritura independiente de otro dashboard.

El frontend prueba rechazo de recibos, el envío de una misma definición a todo
Run y la preservación de IDs sin adoptar datos ni registrar éxito ante conflictos.
Se verifica el recorrido en Chromium con el build de producción. Los artefactos
de revisión se guardan en `build/sql-definition-review/`, ignorados por Git.

Validación: **2.508 pruebas Python aprobadas y 3 omitidas; 296 pruebas frontend**.
Ruff, mypy (150 archivos fuente), check Svelte sin errores/advertencias y build
correctos. Chromium verifica el recorrido de cinco commits atómicos de Run y
un cambio real de SQL entre consultas: 409, mismos IDs, sin composición/registro
de éxito ni SQL privado en el error. Las fixtures se eliminan por su propio ID.
Se conserva la copia de preview mediante cierre ordenado y respaldo antes de
actualizar el backend; no se toca el proyecto o aprendizaje reales del usuario.
Persisten los avisos conocidos de teardown Svelte y tamaño de chunks.

Ver el [plan operativo](sqlviz-studio-delivery-plan.md). Recarga de snapshots y
asociaciones entregada en [2c.2](sqlviz-sql-snapshot-reload.md).
**Siguiente: 2c.3**, borrador/autoguardado y recuperación explícita.
