# Run: guardar definiciones y después ejecutar

**Implementado — 2026-10-09: S1.1c.2b.** Run del workspace usa un único
[commit HTTP](sqlviz-sql-commit-api.md) para SQL, paneles y asociaciones. Después
ejecuta por IDs confirmados y compone los resultados. Un fallo de ejecución no
significa que las definiciones no se hayan guardado. S1.1c.2c sigue pendiente para
recarga, recuperación y coherencia de revisiones durante la ejecución.

## Recorrido confirmado

1. Analizar el script con el parser nativo, conservando fuente y rangos UTF-16.
2. Esperar escrituras de borrador ya iniciadas y suspender nuevas durante Run.
3. Leer el snapshot del dashboard. Si difieren sus IDs o SQL respecto de los
   paneles cargados, exigir recarga; no adoptar esos cambios silenciosamente.
4. Preparar asociaciones con la procedencia del editor. Si hay ambigüedad o un
   panel sin destino, mostrar el diálogo. Conservar la revisión leída mientras
   el autor decide; confirmar no sustituye ese token por otro más reciente.
5. Validar el preflight, incluidos los borrados explícitos, y enviar un commit.
   El servidor repite parsing, política de lectura y reconciliación contra el
   estado esperado dentro de la transacción.
6. Comprobar el recibo: dashboard, fuente, revisión, rangos, IDs conservados,
   correlaciones de creaciones, orden y SQL. Adoptar las definiciones confirmadas.
7. Ejecutar cada panel por su ID. Publicar la nueva vista de resultados solo
   después de completar todas las respuestas y la composición.
8. Registrar `last_run_sql` y `last_run_at` de ese recorrido. Este PATCH no incluye
   `sql_content`: no puede reemplazar el texto editado mientras Run estaba activo.

Las antiguas escrituras por sentencia `PATCH /panels/{id}` y `POST /panels` ya no
forman parte de Run. El preflight es una propuesta; el commit sigue siendo la
única confirmación del conjunto. Endpoints legacy para edición individual,
overrides y borrado desde herramientas de panel conservan sus propios recorridos.

## Decisiones del diálogo

Cada consulta debe conservar un panel o crear uno nuevo; un panel no se comparte
entre dos consultas. Los paneles que quedan sin consulta requieren asignación o
una casilla explícita de eliminación. La casilla empieza desmarcada, muestra el
nombre y permite comparar el SQL anterior. La confirmación avisa que también se
eliminarán sus ajustes. Desmarcar conserva la decisión pendiente; asignar el panel
a una consulta sustituye su eliminación por la elección explícita de conservar.

Cancelar o Escape no escribe definiciones. Un script vacío o de comentarios puede
retirar todos los paneles existentes, solo si se confirma cada uno; no crea un
dashboard vacío automáticamente. Guardar esta eliminación no registra una nueva
consulta como ejecutada. El diálogo mantiene foco, scroll interno y acciones
accesibles en pantallas pequeñas; no añade una segunda confirmación modal.

## Estados y recuperación local

| Situación | Comportamiento |
| --- | --- |
| Fallo de parsing, snapshot o preflight | Sin commit; conserva la vista anterior |
| Commit rechazado | Sin ejecución; conserva vista/IDs anteriores y decisiones para revisión |
| Commit confirmado | Adopta IDs/SQL/bindings aunque luego falle la ejecución |
| Ejecución o composición fallida | «Definitions saved…»; no muestra resultados parciales ni recrea paneles al reintentar |
| Registro de última ejecución fallido | Informa que las definiciones se guardaron y las consultas respondieron; no inventa un timestamp persistido |
| Edición de texto durante commit/ejecución | Mantiene el texto nuevo como borrador y el SQL efectivamente solicitado por separado |

Después de confirmar definiciones se retira la vista anterior: puede contener
paneles eliminados o SQL sustituido. Hasta disponer de una nueva composición no
se publican resultados parciales ni se aplican filtros sobre referencias retiradas.
Antes de ese commit, un fallo conserva el resultado y los filtros anteriores.

El SQL de la caché de resultados corresponde a la ejecución mostrada, separado
del borrador y del registro durable de «última ejecución». Una respuesta tardía de
autoguardado de otro dashboard no cambia el indicador o baseline de la vista nueva.
La restauración de la última ejecución no recupera bindings de IDs ya eliminados.

## Límites entre capas

[sqlRunResolution.ts](../../packages/sqlviz-web/src/lib/sql/sqlRunResolution.ts)
mantiene decisiones puras de conservar/crear/eliminar y valida el preflight.
[sqlScriptCommit.ts](../../packages/sqlviz-web/src/lib/sql/sqlScriptCommit.ts)
define el transporte y comprueba snapshots/recibos antes de adoptar IDs.
[dashboardStore](../../packages/sqlviz-web/src/lib/stores/dashboardStore.svelte.ts)
coordina el borrador, commit, ejecución y vista. La UI no asigna UUID durable ni
autoriza escrituras; esas responsabilidades permanecen en API/core/storage.

No se implementa un rollback distribuido entre metadata, consultas analíticas,
composición y aprendizaje. El commit es atómico para las definiciones; resultados
y registros de inferencia se producen después, mediante sus endpoints existentes.
El autoguardado sigue usando el PATCH legacy del borrador y no confirma bindings.
El texto editado durante Run queda pendiente en memoria y se vuelve a programar
al terminar. Recuperarlo tras cerrar la página durante esa operación sigue en 2c.

## Qué falta en S1.1c.2c

**1b entregado:** [Run ligado a una definición](sqlviz-sql-execution-definition.md)
valida el script esperado antes/después de consulta y al componer, incluidos
fallbacks y cambios de paneles vecinos. La referencia acompaña los recibos y el
cliente rechaza resultados/layout incompatibles; no es una firma de ejecución.

**1a entregado:** la [publicación de inferencia](sqlviz-inference-publication.md)
rechaza cambios de SQL/elección de gráfico durante una consulta real del autor
y guarda inferencia/clasificación juntas. Protege los inputs capturados por esa
solicitud; no confirma todavía que coincidan con el commit previo de Run.

- Restaurar bindings persistidos solo para fuente exacta o procedencia válida.
  Por ahora, recargar un borrador arbitrario vuelve a pedir asociación explícita.
- Recuperar conflictos o respuestas perdidas con un snapshot nuevo y revisión del
  autor. No existe respuesta idempotente almacenada ni adopción automática tras
  pérdida de respuesta; reintentar con el mismo token no duplica creaciones.
- Completar autosave/recarga y coherencia del cache ante otros editores y cambios
  legacy, preservando borrador y estado confirmado.
- Completar el registro condicionado de éxito. Run ya valida la definición de
  consulta/composición, pero su PATCH legacy puede registrar la fuente anterior
  si hay un cambio posterior a composición. No hay snapshot analítico común del
  lote; lectores/refrescos legacy no se ligan todavía a una definición esperada.

Crear el primer dashboard sigue siendo una operación separada del commit de sus
paneles. Si el commit posterior falla, puede quedar el dashboard sin paneles;
no se borran recursos automáticamente. La congelación/publicación del viewer,
datasets reutilizables y layout persistido tampoco se incorporan aquí.

## Evidencia

Pruebas cubren creación/reordenación por ID, inserciones Monaco, eliminación
explícita y cancelación, autoguardado en vuelo, cambios de fuente, rechazo de
recibos contradictorios, commit fallido y reintento tras fallo de consulta/layout.
Se verifica que Run no use escrituras por panel ni sobrescriba el borrador con
su PATCH de última ejecución. El navegador se prueba sobre una copia aislada,
sin editar el proyecto del usuario ni su base de aprendizaje.

Validación: **277 pruebas de frontend**, check sin errores/advertencias y build
de producción correcto. Chromium confirma cinco commits atómicos, ninguna
escritura individual de paneles desde Run, cancelación, overrides conservados,
fallo de consulta con guardado confirmado, reintento con los mismos IDs y
eliminación explícita, incluida la totalidad del dashboard. Las acciones se
verifican a 1440 × 1000 y 390 × 650; sin errores JavaScript. Persisten los avisos
conocidos de teardown Svelte y tamaño de chunks. Artefactos en
`build/sql-run-commit-review/`, ignorados por Git.

Siguiente: **S1.1c.2c.1c**, registro de éxito condicionado, antes de cerrar recarga
y recuperación.

Ver el [plan operativo](sqlviz-studio-delivery-plan.md).
